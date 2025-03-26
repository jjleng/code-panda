from typing import List, cast

from litellm import Choices, acompletion
from litellm.types.utils import ModelResponse

from cp_agent.config import settings


async def merge_diff(original_code: str, diff_content: str) -> tuple[str, bool]:
    """
    Merge original code with a diff using GPT-4-mini via litellm.

    Args:
        original_code: The original source code
        diff_content: The diff content to merge

    Returns:
        Tuple of (merged code, success boolean)
    """
    try:
        prompt = f"""You are a code merging assistant. Merge the following diff content into the original code:

Original code:
```
{original_code}
```

Diff content:
```
{diff_content}
```

Return ONLY the merged code without any explanation or formatting. The output should be valid source code that could be saved directly to a file."""

        response = cast(
            ModelResponse,
            await acompletion(
                model=settings.DEFAULT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                api_base=settings.DEFAULT_LLM_URL,
                api_key=settings.DEFAULT_MODEL_API_KEY,
            ),
        )

        assistant_message = cast(List[Choices], response.choices)[0].message.content

        if assistant_message:
            merged_code = assistant_message.strip()
            return merged_code, True

        return original_code, False

    except Exception as e:
        print(f"Error merging diff: {e}")
        return original_code, False
