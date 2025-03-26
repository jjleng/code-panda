"""Project summary generation utilities using LLM."""

from typing import List, cast

from litellm import acompletion
from litellm.types.utils import Choices, ModelResponse
from loguru import logger
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

from cp_agent.config import settings


class ProjectSummaryResponse(BaseModel):
    """Project summary response from LLM."""

    name: str
    description: str


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
)
async def generate_project_summary(message: str) -> ProjectSummaryResponse:
    """Generate a project name and description based on the user's first message.

    Args:
        message: The user's first message to the assistant

    Returns:
        ProjectSummaryResponse with name and description

    Raises:
        RuntimeError: If LLM call fails after retries
    """
    if not message.strip():
        return ProjectSummaryResponse(
            name="Unnamed Project", description="No description available."
        )

    prompt = f"""Based on the user's first message below, generate a concise project name and a brief description.

User's message:
{message}

Your response should be in JSON format with two fields:
- "name": A concise, descriptive project name (max 30 characters)
- "description": A brief summary of what the project is about (max 100 characters)

Only return valid JSON with no additional text."""

    response = cast(
        ModelResponse,
        await acompletion(
            model=settings.DEFAULT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that generates project names and descriptions based on user inputs.",
                },
                {"role": "user", "content": prompt},
            ],
            api_base=settings.DEFAULT_LLM_URL,
            api_key=settings.DEFAULT_MODEL_API_KEY,
            temperature=0.7,
            response_format={"type": "json_object"},
        ),
    )

    # Extract the JSON response from the LLM
    content = cast(List[Choices], response.choices)[0].message.content or "{}"

    try:
        # Parse the response and create ProjectSummaryResponse
        result = ProjectSummaryResponse.model_validate_json(content)
        logger.info(f"Generated project summary: {result}")
        return result
    except Exception as e:
        logger.error(f"Error parsing project summary response: {e}")
        # Fallback in case of parsing error
        return ProjectSummaryResponse(
            name="AI Generated Project",
            description="Project created with AI assistance.",
        )
