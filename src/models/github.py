import os
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# This file stores the app's configuration in one place.
# In simple terms: it reads values like the GitHub token and log level from
# environment variables (such as a local .env file) so the program can run
# without putting secret values directly in the source code.
class Settings(BaseSettings):
    """Configuration settings for the MCP GitHub Auditor server."""

    # The token lets this app talk to GitHub on your behalf.
    # It is read from the environment variable GITHUB_PERSONAL_ACCESS_TOKEN.
    github_personal_access_token: str = Field(
        default="",
        alias="GITHUB_PERSONAL_ACCESS_TOKEN",
        description="GitHub Personal Access Token (PAT) with read permissions."
    )

    # Controls how noisy the logs are: INFO, DEBUG, WARNING, etc.
    log_level: str = Field(
        default="INFO",
        alias="LOG_LEVEL",
        description="Application logging level."
    )

    # Tell pydantic-settings to look for values in a .env file.
    # This is helpful during local development because the app can read secrets
    # without being hardcoded in the code.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def headers(self) -> dict[str, str]:
        """Generate default headers for GitHub API requests."""
        # These headers tell GitHub what kind of data we want and which API version
        # we are using. They also include a custom user-agent name for identification.
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "MCP-GitHub-Auditor/0.1.0",
        }

        # If a token exists, attach it to the request so GitHub knows who is asking.
        # This is the equivalent of presenting an ID card when visiting a secure area.
        if self.github_personal_access_token:
            headers["Authorization"] = f"Bearer {self.github_personal_access_token}"
        return headers


# Create one shared settings object that the rest of the app can use.
settings = Settings()
