"""Git snapshot utilities for generating commit messages using LLM."""

import shlex
import subprocess
from typing import List, Optional, cast

from litellm import acompletion
from litellm.types.utils import Choices, ModelResponse
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from cp_agent.config import settings


async def get_git_diff(path: str) -> str:
    """Get git diff for the specified path.

    Args:
        path: Path to get diff for

    Returns:
        The git diff output as a string.

    Raises:
        RuntimeError: If git command fails
    """
    try:
        cmd = f"cd {shlex.quote(path)} && git diff"
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        error_msg = f"Failed to get git diff: {e.stderr}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
)
async def generate_commit_message(diff: str) -> str:
    """Generate a commit message from a git diff using LLM.

    Args:
        diff: The git diff content to analyze

    Returns:
        Generated commit message

    Raises:
        RuntimeError: If LLM call fails after 3 retries
    """
    if not diff.strip():
        return "No changes to commit"

    prompt = f"""Given the following git diff, please generate a clear and concise commit message that follows best practices.
The message should:
- Start with a brief summary (50 chars or less)
- Use imperative mood ("Add feature" not "Added feature")
- Include relevant details in body if needed
- Focus on the "what" and "why", not the "how"

Git diff:
{diff}

Generate only the commit message without any additional text or explanation."""

    response = cast(
        ModelResponse,
        await acompletion(
            model=settings.DEFAULT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a commit message generator that follows git commit message best practices.",
                },
                {"role": "user", "content": prompt},
            ],
            api_base=settings.DEFAULT_LLM_URL,
            api_key=settings.DEFAULT_MODEL_API_KEY,
            temperature=0.7,
        ),
    )

    return cast(List[Choices], response.choices)[0].message.content or "misc changes"


async def create_snapshot(path: str, commit_message: Optional[str] = None) -> str:
    """Create a snapshot by staging changes, generating message and committing.

    This is a convenience function that handles the full git commit workflow.

    Args:
        path: Path to create snapshot for
        commit_message: Optional pre-defined commit message. If not provided,
                       one will be generated from the diff.

    Returns:
        Generated commit message

    Raises:
        RuntimeError: If git operations fail
    """
    try:
        # First get the diff to generate message if needed
        diff = await get_git_diff(path)
        if not diff.strip():
            return "No changes detected"

        # Use provided commit message or generate one
        if commit_message is None:
            commit_message = await generate_commit_message(diff)

        # Stage and commit changes using shell
        cmd = f"""cd {shlex.quote(path)} && git add . && git commit -m {shlex.quote(commit_message)}"""
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, check=True
        )

        logger.info(f"Created git commit: {result.stdout}")
        return commit_message

    except Exception as e:
        error_msg = f"Failed to create snapshot: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e
