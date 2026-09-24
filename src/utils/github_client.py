import logging
from typing import Any, Optional
import httpx
from pydantic import ValidationError

from ..config import settings
from ..models.github import IssueSummary, RateLimitStatus, RepositoryOverview

logger = logging.getLogger("mcp_github_auditor")


class GitHubAPIError(Exception):
    """Base exception for GitHub API errors."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class GitHubRateLimitError(GitHubAPIError):
    """Raised when GitHub API rate limits are exceeded."""
    pass


class GitHubNotFoundError(GitHubAPIError):
    """Raised when a requested repository, issue, or resource is not found."""
    pass


class GitHubClient:
    """Async client for interacting with the GitHub REST API securely."""

    def __init__(self, token: Optional[str] = None, timeout: float = 10.0):
        self.headers = settings.headers
        if token:
            self.headers["Authorization"] = f"Bearer {token}"
        self.base_url = "https://api.github.com"
        self.timeout = timeout

    async def _request(self, method: str, endpoint: str, params: Optional[dict[str, Any]] = None) -> dict[str, Any] | list[Any]:
        url = f"{self.base_url}{endpoint}"
        async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout) as client:
            try:
                response = await client.request(method, url, params=params)
                
                # Check rate limits explicitly
                if response.status_code == 403 and "X-RateLimit-Remaining" in response.headers:
                    if response.headers.get("X-RateLimit-Remaining") == "0":
                        reset_time = response.headers.get("X-RateLimit-Reset", "Unknown")
                        raise GitHubRateLimitError(
                            f"GitHub API rate limit exceeded. Resets at timestamp: {reset_time}",
                            status_code=403
                        )

                if response.status_code == 404:
                    raise GitHubNotFoundError(f"Resource not found at {endpoint}", status_code=404)

                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error on {url}: {e.response.status_code} - {e.response.text}")
                raise GitHubAPIError(f"GitHub API error: {e.response.status_code}", status_code=e.response.status_code)
            except httpx.RequestError as e:
                logger.error(f"Request connection error on {url}: {str(e)}")
                raise GitHubAPIError(f"Failed to connect to GitHub API: {str(e)}")

    async def get_repository(self, owner: str, repo: str) -> RepositoryOverview:
        """Fetch details for a given repository."""
        data = await self._request("GET", f"/repos/{owner}/{repo}")
        try:
            return RepositoryOverview.model_validate(data)
        except ValidationError as e:
            logger.error(f"Schema validation error for repo {owner}/{repo}: {e}")
            raise GitHubAPIError("Failed to parse GitHub repository response model.")

    async def list_open_issues(self, owner: str, repo: str, limit: int = 10) -> list[IssueSummary]:
        """Fetch open issues for a repository."""
        params = {"state": "open", "per_page": min(limit, 100)}
        data = await self._request("GET", f"/repos/{owner}/{repo}/issues", params=params)
        
        issues = []
        for item in data:
            # Skip Pull Requests (GitHub REST API includes PRs in issues endpoint)
            if "pull_request" in item:
                continue
            try:
                labels = [label["name"] for label in item.get("labels", []) if isinstance(label, dict)]
                item["labels"] = labels
                issues.append(IssueSummary.model_validate(item))
            except ValidationError as e:
                logger.warning(f"Skipping malformed issue entry: {e}")
                continue
        return issues

    async def get_rate_limit(self) -> RateLimitStatus:
        """Fetch current API rate limit status."""
        data = await self._request("GET", "/rate_limit")
        core = data.get("resources", {}).get("core", {})
        return RateLimitStatus(
            limit=core.get("limit", 0),
            remaining=core.get("remaining", 0),
            reset_timestamp=core.get("reset", 0),
            used=core.get("used", 0)
        )