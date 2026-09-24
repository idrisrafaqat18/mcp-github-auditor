from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl


class GitHubUser(BaseModel):
    login: str
    id: int
    avatar_url: HttpUrl
    html_url: HttpUrl


class RepositoryOverview(BaseModel):
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
    limit: int
    remaining: int
    reset_timestamp: int
    used: int