import asyncio
import json
import os
import tempfile
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import httpx
from loguru import logger
from slugify import slugify
from storage3._async.bucket import AsyncBucket as StorageAsyncBucket  # type: ignore
from supabase import AsyncClient, acreate_client
from tenacity import RetryError, retry, stop_after_attempt, wait_exponential

from cp_agent.config import settings
from cp_agent.utils.dependency_management import add_dependency
from cp_agent.utils.runner_client import RunnerClient


class SupabaseUtil:
    """Utility class for Supabase API operations"""

    def __init__(self, project_root: str) -> None:
        # General properties
        self.project_root = project_root
        self._project_id = Path(project_root).name
        self.base_url = "https://api.supabase.com/v1"

        # For linked Supabase projects
        self._supabase_project_id: Optional[str] = None
        self._anon_key: Optional[str] = None
        self._supabase_client: Optional[AsyncClient] = None
        self._service_role_key: Optional[str] = None
        self._admin_client: Optional[AsyncClient] = None
        # These are used for caching the management API token for linked projects
        self._cached_access_token: Optional[str] = None
        self._cached_refresh_token: Optional[str] = None
        self._cached_token_expiry: Optional[datetime] = None

    async def _get_management_api_token(self) -> str:
        """Get the management API token"""
        return settings.USER_SUPABASE_PAT

    async def _fetch_supabase_project_id(self) -> str:
        """Fetch the Supabase project ID"""
        return settings.LINKED_SUPABASE_PROJECT_ID

    async def _get_request_headers(self) -> dict[str, str]:
        """Get the request headers"""
        token = await self._get_management_api_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def _read_project_id_from_config(self) -> Optional[str]:
        """Read project ID from Supabase config.toml file"""
        config_path = Path(self.project_root) / "supabase" / "config.toml"
        if not config_path.exists():
            return None

        try:
            # Simple parsing for the project_id from the TOML file
            with open(config_path, "r") as f:
                for line in f:
                    if line.strip().startswith("project_id"):
                        # Extract the value between quotes
                        parts = line.split("=", 1)
                        if len(parts) == 2:
                            return parts[1].strip().strip("\"'")
        except Exception as e:
            logger.error(f"Error reading Supabase config: {str(e)}")
        return None

    @property
    def supabase_project_id(self) -> str:
        """Get the Supabase project ID from config or default to a fallback value"""
        # Read the project ID from config each time to handle reconnections
        project_id = self._read_project_id_from_config()
        if not project_id:
            raise ValueError("Supabase project ID not found in config")
        return project_id

    async def _get_anon_key(self) -> str:
        """Fetch anon key from management API"""
        if not self._anon_key:
            async with httpx.AsyncClient(verify=False) as client:
                headers = await self._get_request_headers()
                response = await client.get(
                    f"{self.base_url}/projects/{self.supabase_project_id}/api-keys",
                    headers=headers,
                )
                response.raise_for_status()
                keys = response.json()
                for key in keys:
                    if key.get("name") == "anon":
                        self._anon_key = key.get("api_key")
                        break
        return self._anon_key or ""

    async def _get_service_role_key(self) -> str:
        """Fetch service role key from management API"""
        if not self._service_role_key:
            async with httpx.AsyncClient(verify=False) as client:
                headers = await self._get_request_headers()
                response = await client.get(
                    f"{self.base_url}/projects/{self.supabase_project_id}/api-keys",
                    headers=headers,
                )
                response.raise_for_status()
                keys = response.json()
                for key in keys:
                    if key.get("name") == "service_role":
                        self._service_role_key = key.get("api_key")
                        break
        return self._service_role_key or ""

    async def _get_supabase_client(self) -> AsyncClient:
        """Get or create Supabase client with anon key"""
        if not self._supabase_client:
            anon_key = await self._get_anon_key()
            project_url = f"https://{self.supabase_project_id}.supabase.co"
            self._supabase_client = await acreate_client(project_url, anon_key)
        return self._supabase_client

    async def _get_admin_client(self) -> AsyncClient:
        """Get or create Supabase client with service role key for admin operations"""
        if not self._admin_client:
            service_key = await self._get_service_role_key()
            project_url = f"https://{self.supabase_project_id}.supabase.co"
            self._admin_client = await acreate_client(project_url, service_key)
        return self._admin_client

    async def deploy_edge_function(
        self,
        function_name: str,
        source_code: str,
        verify_deploy: bool = True,
    ) -> dict[str, Any]:
        """
        Deploy an edge function to Supabase with provided source code.
        This will create the function if it doesn't exist or update it if it does.

        Args:
            function_name: The name of the function (slug)
            source_code: The TypeScript source code of the function
            verify_deploy: Whether to verify the deployment was successful

        Returns:
            dict: The deployment response from the API
        """
        try:
            # Deploy the function using the Management API
            async with httpx.AsyncClient(verify=False, timeout=60.0) as client:
                headers = await self._get_request_headers()

                slug = slugify(function_name)

                # First check if function exists
                function_exists = False
                try:
                    check_response = await client.get(
                        f"{self.base_url}/projects/{self.supabase_project_id}/functions/{slug}",
                        headers=headers,
                    )
                    function_exists = check_response.status_code == 200
                except Exception:
                    # If we can't check, assume it doesn't exist
                    function_exists = False

                if function_exists:
                    # Update existing function using PATCH endpoint
                    update_payload = {
                        "name": function_name,
                        "verify_jwt": True,
                        "body": source_code,
                    }

                    response = await client.patch(
                        f"{self.base_url}/projects/{self.supabase_project_id}/functions/{slug}",
                        headers=headers,
                        json=update_payload,
                    )
                else:
                    # Create a new function using multipart/form-data approach
                    # Remove content-type header as it will be set by the multipart request
                    if "Content-Type" in headers:
                        del headers["Content-Type"]

                    # Create a temporary file
                    with tempfile.NamedTemporaryFile(
                        suffix=".ts", delete=False
                    ) as temp_file:
                        temp_path = temp_file.name
                        temp_file.write(source_code.encode("utf-8"))

                    # Prepare multipart form data
                    files = {
                        "file": (
                            f"{function_name}.ts",
                            open(temp_path, "rb"),
                            "application/typescript",
                        )
                    }

                    # Metadata required by the API
                    metadata = {
                        "name": function_name,
                        "verify_jwt": True,
                        "entrypoint_path": f"{function_name}.ts",
                    }

                    # Prepare form data without the slug (it goes in query params)
                    data = {
                        "metadata": json.dumps(metadata),
                    }

                    # Make the deployment request with slug as query parameter
                    response = await client.post(
                        f"{self.base_url}/projects/{self.supabase_project_id}/functions/deploy?slug={slug}",
                        headers=headers,
                        files=files,
                        data=data,
                    )

                    # Clean up the temporary file
                    os.unlink(temp_path)

                response.raise_for_status()
                result = response.json()

                logger.info(
                    f"Edge function '{function_name}' successfully {'updated' if function_exists else 'created'}"
                )

                # Verify deployment if requested
                if verify_deploy:

                    @retry(
                        stop=stop_after_attempt(5),
                        wait=wait_exponential(multiplier=1, min=1, max=5),
                    )
                    async def verify_deployment() -> None:
                        """Verify function deployment with retries"""
                        verify_headers = await self._get_request_headers()
                        verify_response = await client.get(
                            f"{self.base_url}/projects/{self.supabase_project_id}/functions/{slug}",
                            headers=verify_headers,
                        )

                        if verify_response.status_code != 200:
                            raise ValueError(
                                f"Function verification failed: HTTP {verify_response.status_code}"
                            )

                        logger.info(
                            f"Verified edge function '{function_name}' is active"
                        )

                    try:
                        await verify_deployment()
                    except RetryError as e:
                        logger.warning(
                            f"Failed to verify deployment after multiple attempts: {str(e)}"
                        )

                return result

        except Exception as e:
            logger.error(f"Error deploying edge function '{function_name}': {str(e)}")
            raise ValueError(f"Failed to deploy edge function: {str(e)}") from e

    async def delete_edge_function(
        self,
        function_name: str,
        verify_delete: bool = True,
    ) -> bool:
        """
        Delete an edge function from Supabase.

        Args:
            function_name: The name/slug of the function to delete
            verify_delete: Whether to verify the deletion was successful

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            slug = slugify(function_name)

            # Delete the function using the Management API
            async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
                headers = await self._get_request_headers()

                # Make the deletion request
                response = await client.delete(
                    f"{self.base_url}/projects/{self.supabase_project_id}/functions/{slug}",
                    headers=headers,
                )

                response.raise_for_status()

                logger.info(
                    f"Edge function '{function_name}' deletion request successful"
                )

                # Verify deletion if requested
                if verify_delete:

                    @retry(
                        stop=stop_after_attempt(5),
                        wait=wait_exponential(multiplier=1, min=1, max=5),
                    )
                    async def verify_deletion() -> None:
                        """Verify function deletion with retries"""
                        try:
                            verify_headers = await self._get_request_headers()
                            verify_response = await client.get(
                                f"{self.base_url}/projects/{self.supabase_project_id}/functions/{slug}",
                                headers=verify_headers,
                            )

                            # If we can still get the function, it's not deleted yet
                            if verify_response.status_code != 404:
                                raise ValueError(
                                    f"Function still exists: HTTP {verify_response.status_code}"
                                )

                            logger.info(
                                f"Verified edge function '{function_name}' was deleted"
                            )
                        except httpx.HTTPStatusError as e:
                            if e.response.status_code == 404:
                                # 404 is what we want - function is gone
                                logger.info(
                                    f"Verified edge function '{function_name}' was deleted"
                                )
                            else:
                                raise ValueError(
                                    f"Unexpected error during deletion verification: {str(e)}"
                                )

                    try:
                        await verify_deletion()
                    except RetryError:
                        logger.warning(
                            f"Could not verify deletion of function '{function_name}' after multiple attempts"
                        )
                        return False

                return True

        except Exception as e:
            logger.error(f"Error deleting edge function '{function_name}': {str(e)}")
            return False

    async def execute_query(self, query: str) -> list[dict[str, Any]]:
        """Execute SQL query using Management API"""
        async with httpx.AsyncClient(verify=False) as client:
            headers = await self._get_request_headers()
            response = await client.post(
                f"{self.base_url}/projects/{self.supabase_project_id}/database/query",
                headers=headers,
                json={"query": query},
            )
            if not response.is_success:
                error_content = response.text
                logger.error(
                    f"Supabase query failed: {response.status_code} - {error_content}"
                )
                # Raise a ValueError with the actual error message from Supabase
                raise ValueError(f"Supabase query failed: {error_content}")
            return response.json()

    async def get_storage_buckets(self) -> list[StorageAsyncBucket]:
        """Fetch storage buckets information using admin client"""
        try:
            client = await self._get_admin_client()
            storage = client.storage
            buckets = await storage.list_buckets()
            return buckets
        except Exception as e:
            logger.error(f"Error fetching storage buckets: {str(e)}")
            return []

    async def get_project_secrets(self) -> list[dict[str, Any]]:
        """Fetch project secrets"""
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            try:
                headers = await self._get_request_headers()
                response = await client.get(
                    f"{self.base_url}/projects/{self.supabase_project_id}/secrets",
                    headers=headers,
                )
                response.raise_for_status()
                return response.json()
            except (httpx.ReadTimeout, httpx.HTTPStatusError, Exception) as e:
                logger.error(f"Error fetching project secrets: {str(e)}")
                return []

    async def get_edge_functions(
        self, fetch_details: bool = False
    ) -> list[dict[str, Any]]:
        """Fetch edge functions and their details"""
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            try:
                headers = await self._get_request_headers()
                response = await client.get(
                    f"{self.base_url}/projects/{self.supabase_project_id}/functions",
                    headers=headers,
                )
                response.raise_for_status()
                edge_functions = response.json()

                if fetch_details:
                    # Fetch function definitions
                    for func in edge_functions:
                        func_slug = func.get("slug") or func.get("name")
                        if func_slug:
                            try:
                                await asyncio.sleep(0.2)  # Rate limiting
                                headers = (
                                    await self._get_request_headers()
                                )  # Refresh headers for each request
                                func_def_response = await client.get(
                                    f"{self.base_url}/projects/{self.supabase_project_id}/functions/{func_slug}",
                                    headers=headers,
                                )
                                if func_def_response.status_code == 200:
                                    definition = func_def_response.json()
                                    func["code"] = definition.get("code", "")
                                else:
                                    func["code"] = (
                                        f"Unable to fetch function code: HTTP {func_def_response.status_code}"
                                    )
                            except Exception as e:
                                func["code"] = f"Error fetching function code: {str(e)}"

                return edge_functions
            except Exception as e:
                logger.error(f"Error fetching edge functions: {str(e)}")
                return []

    async def set_secret(self, name: str, value: str) -> dict[str, Any]:
        """
        Create or update a Supabase secret using the Management API.
        For updates, this deletes the existing secret and creates a new one.

        Args:
            name: The name of the secret
            value: The value of the secret

        Returns:
            dict: The API response
        """
        try:
            async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
                headers = await self._get_request_headers()

                # First, check if the secret already exists
                existing_secrets = await self.get_project_secrets()
                logger.info(f"Existing secrets: {existing_secrets}")
                secret_exists = any(
                    secret.get("name") == name for secret in existing_secrets
                )

                # If the secret exists, delete it first
                if secret_exists:
                    logger.info(f"Deleting existing secret '{name}'")
                    delete_response = await client.request(
                        "DELETE",
                        f"{self.base_url}/projects/{self.supabase_project_id}/secrets",
                        headers=headers,
                        content=json.dumps([name]),
                    )
                    delete_response.raise_for_status()
                    logger.info(f"Secret '{name}' successfully deleted")

                # Prepare the request payload as an array with a single object
                payload = [
                    {
                        "name": name,
                        "value": value,
                    }
                ]

                logger.info(f"Setting secret '{name}'")

                # Create the secret
                response = await client.post(
                    f"{self.base_url}/projects/{self.supabase_project_id}/secrets",
                    headers=headers,
                    json=payload,
                )

                response.raise_for_status()

                # Handle empty response properly
                result = {}
                if response.content and response.content.strip():
                    try:
                        result = response.json()
                    except json.JSONDecodeError:
                        logger.warning(
                            f"Received non-JSON response when setting secret: {response.text}"
                        )

                action = "updated" if secret_exists else "created"
                logger.info(f"Secret '{name}' successfully {action}")
                return result

        except httpx.RequestError as e:
            logger.error(f"HTTP request error setting secret '{name}': {str(e)}")
            raise ValueError(f"Failed to set secret: {str(e)}") from e
        except Exception as e:
            logger.error(f"Error setting secret '{name}': {str(e)}")
            raise ValueError(f"Failed to set secret: {str(e)}") from e

    async def get_database_info(self) -> dict[str, list[dict[str, Any]]]:
        """Get comprehensive database information including tables, policies, functions, and triggers"""
        query = """
        WITH table_info AS (
            SELECT
                tables.table_name,
                pd.description as table_description
            FROM information_schema.tables tables
            LEFT JOIN pg_stat_user_tables psut ON tables.table_name = psut.relname
            LEFT JOIN pg_description pd ON psut.relid = pd.objoid AND pd.objsubid = 0
            WHERE tables.table_schema = 'public'
        ),
        column_info AS (
            SELECT
                c.table_name,
                jsonb_agg(
                    jsonb_build_object(
                        'column_name', c.column_name,
                        'data_type', c.data_type,
                        'is_nullable', c.is_nullable,
                        'column_default', c.column_default
                    ) ORDER BY c.ordinal_position
                ) as columns
            FROM information_schema.columns c
            WHERE c.table_schema = 'public'
            GROUP BY c.table_name
        ),
        tables_result AS (
            SELECT
                'tables' as result_type,
                jsonb_build_object(
                    'name', ti.table_name::text,
                    'description', ti.table_description::text,
                    'columns', COALESCE(ci.columns, '[]'::jsonb)
                )::text as data
            FROM table_info ti
            LEFT JOIN column_info ci ON ti.table_name = ci.table_name
        ),
        policies_result AS (
            SELECT
                'policies' as result_type,
                jsonb_build_object(
                    'name', pol.polname::text,
                    'table', cls.relname::text,
                    'command', CASE
                        WHEN pol.polcmd = 'r' THEN 'SELECT'
                        WHEN pol.polcmd = 'w' THEN 'UPDATE'
                        WHEN pol.polcmd = 'a' THEN 'INSERT'
                        WHEN pol.polcmd = 'd' THEN 'DELETE'
                        ELSE pol.polcmd::text
                    END,
                    'permissive', pol.polpermissive,
                    'definition', pg_get_expr(pol.polqual, pol.polrelid)::text
                )::text as data
            FROM pg_policy pol
            JOIN pg_class cls ON pol.polrelid = cls.oid
            WHERE cls.relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
        ),
        functions_result AS (
            SELECT
                'functions' as result_type,
                jsonb_build_object(
                    'name', p.proname::text,
                    'description', d.description::text,
                    'arguments', pg_get_function_arguments(p.oid)::text,
                    'return_type', pg_get_function_result(p.oid)::text,
                    'language', l.lanname::text,
                    'volatility', CASE p.provolatile
                        WHEN 'i' THEN 'IMMUTABLE'
                        WHEN 's' THEN 'STABLE'
                        WHEN 'v' THEN 'VOLATILE'
                    END,
                    'source_code', pg_get_functiondef(p.oid)::text
                )::text as data
            FROM pg_proc p
            LEFT JOIN pg_description d ON p.oid = d.objoid
            LEFT JOIN pg_language l ON p.prolang = l.oid
            WHERE p.pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
        ),
        triggers_result AS (
            SELECT
                'triggers' as result_type,
                jsonb_build_object(
                    'name', t.trigger_name::text,
                    'table', t.event_object_table::text,
                    'timing', t.action_timing::text,
                    'event', t.event_manipulation::text,
                    'action_statement', t.action_statement::text,
                    'function_name', p.proname::text
                )::text as data
            FROM information_schema.triggers t
            LEFT JOIN pg_trigger pg_t ON t.trigger_name = pg_t.tgname
            LEFT JOIN pg_proc p ON pg_t.tgfoid = p.oid
            WHERE t.trigger_schema = 'public'
        )
        SELECT result_type, data
        FROM (
            SELECT * FROM tables_result
            UNION ALL SELECT * FROM policies_result
            UNION ALL SELECT * FROM functions_result
            UNION ALL SELECT * FROM triggers_result
        ) combined_results
        ORDER BY result_type;
        """
        results = await self.execute_query(query)

        # Initialize result containers
        info: dict[str, list[dict[str, Any]]] = {
            "tables": [],
            "policies": [],
            "functions": [],
            "triggers": [],
        }

        # Parse results
        for result in results:
            try:
                data = json.loads(result.get("data", "{}"))
                result_type = result.get("result_type")
                if result_type in info:
                    info[result_type].append(data)
            except json.JSONDecodeError:
                continue

        return info

    async def integrate_supabase(self) -> None:
        """Integrate Supabase with a project"""
        # Prepare the supabase folder for the supabase code. The supabase CLI will be used to deploy the edge functions, migrations and other supabase related code.
        supabase_folder = Path(self.project_root) / "supabase"
        supabase_folder.mkdir(exist_ok=True)
        # Generate a supabase config file
        supabase_config = supabase_folder / "config.toml"
        supabase_project_id = await self._fetch_supabase_project_id()
        with open(supabase_config, "w") as f:
            f.write(
                textwrap.dedent(
                    f"""
                    project_id = "{supabase_project_id}"
                    """
                )
            )
            f.flush()

        # Install necessary packages with retry handling
        try:
            for package in [
                "@supabase/supabase-js",
                "@supabase/auth-ui-react",
                "@supabase/auth-ui-shared",
            ]:
                await add_dependency(self.project_root, package, restart_runner=False)
        except RetryError as e:
            raise RuntimeError(
                f"Failed to install Supabase dependencies after retries: {str(e)}"
            )

        # Initialize Supabase client
        file_path = Path(self.project_root) / "src" / "lib" / "supabaseClient.ts"
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write content directly
        ts_code = textwrap.dedent(
            f"""
            import {{ createClient }} from '@supabase/supabase-js';

            const supabaseUrl = 'https://{supabase_project_id}.supabase.co';
            const supabaseAnonKey = '{await self._get_anon_key()}';

            export const supabase = createClient(supabaseUrl, supabaseAnonKey);
            """
        ).lstrip()

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(ts_code)
            f.flush()

        # We restart the runner server after adding the dependencies
        runner_client = RunnerClient()
        project_id = Path(self.project_root).name

        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=4, max=10),
        )
        async def restart_project_with_retry() -> None:
            await runner_client.restart_project(project_id)

        try:
            await restart_project_with_retry()
        except RetryError as e:
            logger.warning(
                f"Failed to restart project after multiple attempts: {str(e)}"
            )
            # Continue execution even if restart fails

    async def is_supabase_integrated(self) -> bool:
        """
        Check if Supabase is integrated with a project.

        Args:
            project_root: The root directory of the project

        Returns:
            bool: True if Supabase is integrated, False otherwise
        """
        project_path = Path(self.project_root)

        # Check for supabase directory and config file
        supabase_folder = project_path / "supabase"
        supabase_config = supabase_folder / "config.toml"

        # Check for supabase client file
        supabase_client_file = project_path / "src" / "lib" / "supabaseClient.ts"

        # Check if the essential files and directories exist
        is_integrated = (
            supabase_folder.exists()
            and supabase_config.exists()
            and supabase_client_file.exists()
        )

        return is_integrated

    async def deploy_migration(
        self,
        migration_sql: str = "",
        name: Optional[str] = None,
        file_path: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Deploy a database migration by executing SQL against the Supabase database.

        Args:
            migration_sql: The SQL query string to execute
            name: A descriptive name for the migration (defaults to timestamp if not provided)
            file_path: If provided, reads SQL from this file instead of using migration_sql param

        Returns:
            dict: Information about the migration execution including success status and results
        """
        try:
            # If file path is provided, read SQL from file
            if file_path:
                with open(file_path, "r") as f:
                    migration_sql = f.read()

            if not migration_sql.strip():
                raise ValueError("Migration SQL cannot be empty")

            # Generate migration name if not provided
            migration_name = (
                name or f"migration_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            )

            logger.info(f"Deploying migration '{migration_name}'")

            # Execute the query
            result = await self.execute_query(migration_sql)

            logger.info(f"Successfully deployed migration '{migration_name}'")

            return {
                "name": migration_name,
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "result": result,
            }
        except Exception as e:
            error_msg = f"Error deploying migration: {str(e)}"
            logger.error(error_msg)
            return {
                "name": name or "unknown_migration",
                "success": False,
                "timestamp": datetime.now().isoformat(),
                "error": error_msg,
            }
