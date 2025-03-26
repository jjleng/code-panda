"""Context enricher for enhancing agent capabilities with environmental information."""

import textwrap
from pathlib import Path
from typing import Any, Callable, Coroutine

from cp_agent.config import settings
from cp_agent.context.supabase import (
    general_instructions,
    integration_instructions,
    supabase_report,
)
from cp_agent.storage.list_store import ListStore
from cp_agent.utils.code_checks import perform_code_checks
from cp_agent.utils.file_reading import read_file_content
from cp_agent.utils.message_formats import Message, create_text_block
from cp_agent.utils.runner_client import RunnerClient
from cp_agent.utils.supabase_utils import SupabaseUtil


async def async_lambda(value: str) -> str:
    """Helper function to create an async lambda."""
    return value


class ContextEnricher:
    """Enriches agent context with environmental information.

    This class is responsible for enriching the agent's context by gathering,
    caching, and providing access to information about files, project structure,
    and other relevant environmental details. It maintains this information in
    memory to improve performance and provides a consistent interface for
    accessing contextual data.
    """

    def __init__(self, memory: ListStore, cwd: str):
        """Initialize the context enricher.

        Args:
            memory: Persistent storage for contextual information
        """
        self.memory = memory
        self.cwd = cwd
        self.current_supabase_setup = ""
        self.runner = RunnerClient()
        self.supabase_util = SupabaseUtil(cwd)

    def _check_message_contains_tag(self, msg: dict, tag: str) -> bool:
        """Check if a message contains the specified tag.

        Args:
            msg: The message to check
            tag: The tag to look for

        Returns:
            bool: True if the message contains the tag at the start of any block
        """
        content = msg.get("content", "")
        if isinstance(content, list):
            # Check each block in the list
            for block in content:
                if isinstance(block, dict) and block.get(
                    "text", ""
                ).lstrip().startswith(tag):
                    return True
        elif isinstance(content, str) and content.lstrip().startswith(tag):
            return True
        return False

    def scan_messages_for_tag(self, tag: str) -> bool:
        """Scan messages for a specific tag.

        Args:
            tag: The tag to scan for in message content

        Returns:
            bool: True if tag was found at the start of any message block
        """
        stored_messages = self.memory.lrange("messages")
        return any(
            self._check_message_contains_tag(msg, tag) for msg in stored_messages
        )

    def delete_memory_by_tag(self, tag: str) -> bool:
        """Delete all memory items containing the specified tag.

        Args:
            tag: The tag to search for and delete messages containing it

        Returns:
            bool: True if any messages were deleted, False otherwise
        """
        stored_messages = self.memory.lrange("messages")
        indices_to_remove = [
            i
            for i, msg in enumerate(stored_messages)
            if self._check_message_contains_tag(msg, tag)
        ]

        if not indices_to_remove:
            return False

        # Remove tagged messages in reverse order to maintain correct indices
        for index in sorted(indices_to_remove, reverse=True):
            stored_messages.pop(index)

        # Only update storage if we actually removed messages
        self.memory.delete("messages")
        for msg in stored_messages:
            self.memory.rpush("messages", msg)

        return True

    async def _prime_content(
        self,
        tag: str,
        content_generator: Callable[[], Coroutine[Any, Any, str]],
        skip_if_exists: bool = True,
    ) -> None:
        """Generic method to prime content with a specific tag.

        Args:
            tag: The XML-style tag to wrap the content in
            content_generator: Async function that generates the content
            skip_if_exists: If True, skip if content with this tag already exists
        """
        exists = self.scan_messages_for_tag(f"<{tag}>")
        if exists and skip_if_exists:
            return

        content = await content_generator()
        content_data = create_text_block(f"<{tag}>{content}</{tag}>")
        msg = Message(content=[content_data], role="user")
        self.memory.rpush(
            "messages",
            {
                "role": "user",
                "content": msg.content,
            },
        )

    async def _generate_project_info(self) -> str:
        """Generate project information content."""
        no_access_files = textwrap.dedent(
            """
            ## File Update Access Denied
            You MUST NOT update the following files:
            - Files under src/components/ui are components from shadcn. Note, you can create components in src/components, but not in src/components/ui.
            - package.json. Use the `add_dependency` tool when you need to add a new package.
            - src/tsconfig.json.
            - src/lib/supabaseClient.ts (if exists). NEVER try to replace supabaseUrl and supabaseAnonKey with environment variables.
            """
        )

        current_files = """
## Important Files and Their Contents
1. package.json
```json
{0}
```
2. src/App.tsx
```tsx
{1}
```
            """.format(
            read_file_content(
                str(Path(self.cwd) / "package.json"), add_line_numbers=False
            ),
            read_file_content(
                str(Path(self.cwd) / "src" / "App.tsx"), add_line_numbers=True
            ),
        )

        project_id = Path(self.cwd).name  # Extract project_id from workspace path
        _, check_results = await perform_code_checks(project_id, self.runner)

        error_checks = f"""
## Error Checks
{"\n\n".join(check_results)}
            """

        return no_access_files + "\n" + current_files + "\n" + error_checks

    async def prime_project_info(self, skip_if_exists: bool = True) -> None:
        """Prime the project information cache."""
        await self._prime_content(
            "project-info", self._generate_project_info, skip_if_exists
        )

    async def prime_supabase_integration_instructions(
        self, skip_if_exists: bool = True
    ) -> None:
        """Prime Supabase integration instructions."""
        await self._prime_content(
            "supabase-integration-instructions",
            integration_instructions,
            skip_if_exists,
        )

    async def prime_supabase_general_instructions(
        self, skip_if_exists: bool = True
    ) -> None:
        """Prime Supabase general instructions."""
        tag = "supabase-general-instructions"
        exists = self.scan_messages_for_tag(f"<{tag}>")
        if exists and skip_if_exists:
            return

        content = await general_instructions(self.supabase_util.supabase_project_id)
        content_data = create_text_block(f"<{tag}>{content}</{tag}>")
        msg = Message(content=[content_data], role="user")
        self.memory.rpush(
            "messages",
            {
                "role": "user",
                "content": msg.content,
            },
        )

    async def prime_supabase_report(self, with_cache: bool) -> None:
        """Prime the Supabase report with optional caching.

        Args:
            with_cache: If True, use cached data if available. If False, always fetch fresh data.
        """
        should_fetch_new_data = not with_cache or not self.current_supabase_setup

        if should_fetch_new_data:
            try:
                current_supabase_setup = await supabase_report(self.cwd)
                if current_supabase_setup != self.current_supabase_setup:
                    self.current_supabase_setup = current_supabase_setup
                    self.delete_memory_by_tag("<supabase-report>")
                    await self._prime_content(
                        "supabase-report",
                        lambda: async_lambda(current_supabase_setup),
                        False,
                    )
            except Exception:
                # Silently handle any API errors - the report will simply not be updated
                pass

    async def auto_integrate_supabase(self) -> None:
        """
        Automatically integrate Supabase in local development environments
        if required environment variables are set and Supabase is not
        already integrated.
        """
        # Check if required environment variables are set
        if not settings.USER_SUPABASE_PAT or not settings.LINKED_SUPABASE_PROJECT_ID:
            return

        # Check if Supabase is already integrated
        is_integrated = await self.supabase_util.is_supabase_integrated()
        if is_integrated:
            return

        # All conditions met, integrate Supabase
        await self.supabase_util.integrate_supabase()

    async def prime_all(self, with_cache: bool = True) -> None:
        """Prime all available context information."""
        # Auto-integrate Supabase for local development if needed
        await self.auto_integrate_supabase()

        await self.prime_project_info()
        integrated = await self.supabase_util.is_supabase_integrated()
        if not integrated:
            await self.prime_supabase_integration_instructions()
        else:
            self.delete_memory_by_tag("<supabase-integration-instructions>")
            await self.prime_supabase_general_instructions()
            await self.prime_supabase_report(with_cache)
