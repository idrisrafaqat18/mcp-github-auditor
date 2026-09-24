import os
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration settings for the MCP GitHub Auditor server."""
    
    github_personal_access_token: str = Field(
        default="",
        alias="GITHUB_PERSONAL_ACCESS_TOKEN",
        description="GitHub Personal Access Token (PAT) with read permissions."
    )
    log_level: str = Field(
        default="INFO",
        alias="LOG_LEVEL",
        description="Application logging level."
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def headers(self) -> dict[str, str]:
        """Generate default headers for GitHub API requests."""
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "MCP-GitHub-Auditor/0.1.0",
        }
        if self.github_personal_access_token:
            headers["Authorization"] = f"Bearer {self.github_personal_access_token}"
        return headers


settings = Settings()