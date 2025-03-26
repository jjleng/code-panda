"""Development server runner.

This module provides a convenient way to run the application in different environments.
The environment is determined by the ENV environment variable:

Usage:
    # Run in development (default)
    $ ENV=development poetry run dev

    # Run in production
    $ ENV=production poetry run dev

Configuration Loading Order:
1. Environment variables (highest priority)
2. Environment-specific file (.env.development or .env.production)
3. Default values in Settings class (lowest priority)
"""

import uvicorn

from cp_agent.config import Settings


def main() -> None:
    """Run the server with environment-specific settings."""
    settings = Settings()

    uvicorn.run(
        "cp_agent.main:app",
        host="0.0.0.0",
        port=8000,
        log_level=settings.LOG_LEVEL.lower(),
        reload=settings.RELOAD,
    )


if __name__ == "__main__":
    main()
