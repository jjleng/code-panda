import json
import textwrap
from typing import Any

from storage3._async.bucket import AsyncBucket as StorageAsyncBucket  # type: ignore

from cp_agent.utils.supabase_utils import SupabaseUtil


async def integration_instructions() -> str:
    """Used when Supabase setup was not done"""
    return textwrap.dedent(
        """
Currently, Supabase is not integrated.

When users request features related to database or backend functionality:

1. Check if the request involves any of these topics:
- Database integration or setup
- Authentication/login systems
- Backend API development
- Data storage
- Server-side functionality
- File storage solutions
- Stripe Payments

2. If the request matches any of these topics, DO NOT provide code or technical solutions. Instead:
   - Inform the user about our native Supabase integration
   - Explain that they need to integrate Supabase first for their needs
   - Direct them to documentation using this format:
     <resources>
     <resource-link url="https://github.com/jjleng/code-panda">View Supabase integration guide</resource-link>
     </resources>
   - Only provide the the resources when you finish the conversation.

3. Monitor Supabase connection status:
   After integration is activated, you can access and discuss:
   - Database tables
   - Security policies
   - Project credentials
   - Backend functions
   - Edge function deployments

4. For unconnected users:
   If they haven't connected Supabase yet, instruct them to:
   - Navigate to the Supabase menu in the top-right corner
   - Complete the connection process
   - Return for further assistance

Remember: Never provide direct code solutions for these requests - always guide users to the native integration path.
"""
    )


async def general_instructions(supabase_project_id: str) -> str:
    """Used when general usage is requested"""

    return textwrap.dedent(
        f"""
This project is connected to a Supabase project with the project ID: {supabase_project_id}.
Change Management Process:

1. Initial Assessment:
   - THOROUGHLY review existing <supabase-report>
   - Understand current database state, RLS policies and security rules in detail
   - Analyze if request requires schema changes

2. Database Changes:
   If schema updates needed:
   - Provide SQL commands in single <sql-block>. Example:
     <sql-block>
     CREATE TABLE new_table (
         id SERIAL PRIMARY KEY,
         name TEXT NOT NULL
     );
     </sql-block>
   - Wait for user approval
   - NEVER combine <sql-block> with code updates in the same message
   - Ensure RLS policies align with changes
   - Always set default and nullable values for new table columns to avoid insertion errors
   - For user data: NEVER use foreign key references to auth.users; create a profiles table in public schema instead

3. Implementation After DB Changes:
   Once SQL is approved:
   a. Update Backend:
      - Modify Edge Functions if needed (they are automatically deployed)
      - For simple CRUD, prefer supabase's built-in API over Edge Functions
      - Update third-party API connections
      - Verify function permissions

   b. Update Frontend:
      - Modify UI components
      - Update data fetching logic
      - Adjust state management

4. Resource Management:
   When creating/updating resources:
   - Add appropriate RLS policies
   - Set up necessary triggers
   - Configure storage buckets if needed
   - Manage secrets appropriately

5. Documentation:
   In the end of your message, provide relevant dashboard links with following format:
   <resources>
    <resource-link url="[RESOURCE_LINK]">Resource Name</resource-link>
   </resources>

   Common links:
   - SQL Editor: {{project_id}}/sql/new
   - Authentication providers: {{project_id}}/auth/providers
   - Users: {{project_id}}/auth/users
   - Edge Functions: {{project_id}}/functions
   - Edge Functions secrets: {{project_id}}/settings/functions
   - Edge Function logs: {{project_id}}/functions/{{function_name}}/logs (good to share every time you update an edge function or when you think the user might want to check the logs)
   - Storage : {{project_id}}/storage/buckets

   Examples:
   <resources>
    <resource-link url="https://supabase.com/dashboard/project/{{project_id}}/auth/providers">Auth providers</resource-link>
    <resource-link url="https://supabase.com/dashboard/project/{{project_id}}/sql/new">SQL Editor</resource-link>
    ...
   </resources>

6. Secret Management:
   When working with sensitive information or environment variables:
   - Never hardcode secrets in edge functions
   - Use the secret-input tag to prompt the user to securely add secrets
   - Format secret requests using this syntax:
     <secret-input name="SECRET_NAME" description="Brief description of what this secret is for">Secret Display Name</secret-input>

   Examples:
   <secret-input name="OPENAI_API_KEY" description="Required for AI functionality in the chatbot edge function">OpenAI API Key</secret-input>
   <secret-input name="STRIPE_SECRET_KEY" description="Used for payment processing in the checkout function">Stripe Secret Key</secret-input>

Critical Rules:
- NEVER mix SQL and code updates in same message
- Only ONE SQL block per message
- Always review RLS policies before implementation
- Wait for SQL approval before any code changes
- Never include database alter statements
- Keep SQL commands in single block
- Don't put instructions inside code blocks
- For simple CRUD, prefer built-in supabase API over Edge Functions
"""
    )


def _format_list_item(value: str, indent_level: int = 1) -> str:
    """Format a list item with proper indentation"""
    indent = "    " * indent_level
    return f"{indent}- {value}"


def _format_section(title: str, description: str, content: str) -> str:
    """Format a section with consistent indentation"""
    return f"""
## {title}
{description}
{content}""".strip()


def _format_item_details(details: dict[str, Any], indent_level: int = 1) -> str:
    """Format item details with consistent indentation"""
    indent = "    " * indent_level
    return "\n".join(
        f"{indent}{key}: {value if value is not None else 'Not specified'}"
        for key, value in details.items()
    )


async def supabase_report(project_root: str) -> str:
    """Generate a report of the current Supabase project state"""
    api = SupabaseUtil(project_root)

    # Get additional information
    buckets = await api.get_storage_buckets()
    project_secrets = await api.get_project_secrets()
    # Get edge functions with details for full report
    edge_functions = await api.get_edge_functions()

    # Get database info (tables, policies, functions, triggers)
    db_info = await api.get_database_info()

    # Format table and column info
    formatted_tables = []
    for table in db_info.get("tables", []):
        name = table.get("name", "")
        description = table.get("description", "No description")
        columns = []
        try:
            columns_data = table.get("columns", [])
            if isinstance(columns_data, str):
                columns_data = json.loads(columns_data)
            for col in columns_data:
                nullable = (
                    "Nullable: Yes"
                    if col.get("is_nullable") == "YES"
                    else "Nullable: No"
                )
                default = (
                    f"Default: {col.get('column_default')}"
                    if col.get("column_default")
                    else "Default: None"
                )
                columns.append(
                    f"    {col.get('column_name')} | {col.get('data_type')} | {nullable} | {default}"
                )
        except (json.JSONDecodeError, TypeError):
            columns = ["    No column information available"]

        formatted_tables.append(
            {"name": name, "description": description, "columns": columns}
        )

    # Format policies
    policies = [
        {
            "name": policy.get("name", ""),
            "table": policy.get("table", ""),
            "command": policy.get("command", ""),
            "permissive": policy.get("permissive", True),
            "definition": policy.get("definition", ""),
        }
        for policy in db_info.get("policies", [])
    ]

    # Format functions
    functions = []
    for func in db_info.get("functions", []):
        source_code = func.get("source_code", "")
        if source_code:
            source_code = textwrap.dedent(source_code).strip()

        functions.append(
            {
                "name": func.get("name", ""),
                "description": func.get("description", "No description provided"),
                "arguments": func.get("arguments", "No arguments"),
                "return_type": func.get("return_type", "void"),
                "language": func.get("language", "unknown"),
                "volatility": func.get("volatility", "VOLATILE"),
                "source_code": source_code,
            }
        )

    # Format triggers
    triggers = [
        {
            "name": trigger.get("name", ""),
            "table": trigger.get("table", ""),
            "timing": trigger.get("timing", ""),
            "event": trigger.get("event", ""),
            "function_name": trigger.get("function_name", ""),
            "action_statement": trigger.get("action_statement", ""),
        }
        for trigger in db_info.get("triggers", [])
    ]

    # Format the report
    tables_section = (
        "\n".join(
            f"- {table['name']}: {table.get('description', 'No description')}\n"
            + "  Columns:\n"
            + "\n".join(table["columns"])
            for table in formatted_tables
        )
        if formatted_tables
        else "No tables found"
    )

    policies_section = (
        "\n".join(
            f"Table: {policy['table']}\n"
            + _format_item_details(
                {
                    "Policy Name": policy["name"],
                    "Command": policy.get("command", "UNKNOWN"),
                    "Permissive": "Yes" if policy.get("permissive", True) else "No",
                    "Using Expression": policy.get("definition"),
                }
            )
            for policy in policies
        )
        if policies
        else "No RLS policies found"
    )

    functions_section = (
        "\n".join(
            f"Function: {func['name']}\n"
            + _format_item_details(
                {
                    "Description": func.get("description"),
                    "Arguments": func.get("arguments", "None"),
                    "Returns": func.get("return_type", "void"),
                    "Language": func.get("language", "unknown"),
                    "Volatility": func.get("volatility", "VOLATILE"),
                    "Source Code": "\n"
                    + textwrap.indent(
                        func.get("source_code", "No source code available"), "        "
                    ),
                },
                indent_level=2,
            )
            for func in functions
        )
        if functions
        else "No functions found"
    )

    triggers_section = (
        "\n".join(
            f"Trigger: {trigger['name']}\n"
            + _format_item_details(
                {
                    "On Table": trigger.get("table", "unknown"),
                    "Execution": f"{trigger.get('timing', 'UNKNOWN')} {trigger.get('event', 'UNKNOWN')}",
                    "Using Function": trigger.get("function_name", "unknown"),
                    "Action Statement": trigger.get(
                        "action_statement", "No statement available"
                    ),
                }
            )
            for trigger in triggers
        )
        if triggers
        else "No triggers found"
    )

    # Format storage buckets with more details
    bucket_lines: list[str] = []
    if buckets:
        for bucket in buckets:
            if isinstance(bucket, StorageAsyncBucket):
                try:
                    bucket_info = [
                        f"- {bucket.id}:",
                        f"  Access: {'Public' if bucket.public else 'Private'}",
                        f"  Max File Size: {bucket.file_size_limit}",
                        f"  Allowed Types: {', '.join(bucket.allowed_mime_types or ['*'])}",
                    ]
                    bucket_lines.extend(bucket_info)
                except Exception as e:
                    print(f"Error formatting bucket info: {str(e)}")
                    bucket_lines.extend([f"- {bucket.id}: Error getting details"])

    # String type for final section output
    buckets_section: str = (
        "\n".join(bucket_lines) if bucket_lines else "No storage buckets found"
    )

    # Format edge functions with better code presentation
    function_lines: list[str] = []
    if edge_functions:
        for func in edge_functions:
            code = func.get("code", "No code available")
            if code:
                # Clean up the code formatting
                code = textwrap.dedent(code).strip()

            func_info = [
                f"- {func.get('name', 'Unknown')}:",
                f"  Status: {func.get('status', 'Unknown')}",
                f"  Version: {func.get('version', 'Unknown')}",
                f"  Runtime: {func.get('runtime', 'Unknown')}",
                f"  Entrypoint: {func.get('entrypoint_url', 'Unknown')}",
                f"  Last Updated: {func.get('updated_at', 'Unknown')}",
                "  Code:",
                textwrap.indent(code, "    "),
            ]
            function_lines.extend(func_info)

    # String type for final section output
    edge_functions_section: str = (
        "\n".join(function_lines) if function_lines else "No edge functions found"
    )

    return textwrap.dedent(
        f"""
{_format_section("Database Tables and Schema",
                "Overview of all database tables, their structure, and relationships",
                tables_section)}

{_format_section("Row Level Security (RLS) Policies",
                "Security policies controlling access to database tables",
                policies_section)}

{_format_section("Database Functions",
                "SQL functions defined in the database",
                functions_section)}

{_format_section("Storage Configuration",
                "Storage bucket configuration and access settings",
                buckets_section)}

{_format_section("Serverless Edge Functions",
                "Deployed edge functions and their current status",
                edge_functions_section)}

{_format_section("Secrets",
                "Secrets available for use in edge functions",
                "\n".join(f"- {secret['name']}" for secret in project_secrets) if project_secrets else "No project secrets found")}

    """
    )
