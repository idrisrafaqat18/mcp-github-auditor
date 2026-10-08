from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl


# This file defines the "blueprints" for data returned by the GitHub API.
# Each class below tells Python what a GitHub user, repository, issue, or rate-limit
# summary should look like. In simple terms: it validates the data so the app does not
# accidentally crash when values are missing or shaped differently.


class GitHubUser(BaseModel):
    # A GitHub account holder, such as the repository owner or issue author.
    login: str
    id: int
    avatar_url: HttpUrl
    html_url: HttpUrl


class RepositoryOverview(BaseModel):
    # This model represents the main summary of a GitHub repository.
    # It contains the information we usually care about when auditing a repo:
    # name, owner, stars, issues, and important timestamps.
    id: int
    name: str
    full_name: str
    private: bool
    owner: GitHubUser
    description: Optional[str] = None
    html_url: HttpUrl
    stargazers_count: int = Field(default=0)
    forks_count: int = Field(default=0)
    open_issues_count: int = Field(default=0)
    language: Optional[str] = None
    default_branch: str = "main"
    created_at: datetime
    updated_at: datetime


class IssueSummary(BaseModel):
    # This model reshapes a GitHub issue into a simpler, cleaner summary.
    # It keeps the relevant fields needed by the audit tools without exposing all
    # of GitHub's raw API details.
    number: int
    title: str
    state: str
    user: GitHubUser
    comments: int
    created_at: datetime
    updated_at: datetime
    html_url: HttpUrl
    body: Optional[str] = None
    labels: list[str] = Field(default_factory=list)


class RateLimitStatus(BaseModel):
    # GitHub limits how often we can call its API in a time window.
    # This model stores the current limit numbers so the app can warn the user
    # when it is close to being blocked.
    limit: int
    remaining: int
    reset_timestamp: int
    used: int
