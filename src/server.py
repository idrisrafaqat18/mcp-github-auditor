import logging
from typing import Any
from pydantic import BaseModel, Field

from ..utils.github_client import (
    GitHubAPIError,
    GitHubClient,
    GitHubNotFoundError,
    GitHubRateLimitError,
)

logger = logging.getLogger("mcp_github_auditor")


# This is a simple in-memory tracker.
# It remembers how many times each tool was called, how many succeeded, and how many
# failed. This helps the server report basic operational health without needing a
# database or external monitoring system.
class ToolMetrics:
    def __init__(self):
        self.invocations: dict[str, int] = {}
        self.successes: dict[str, int] = {}
        self.failures: dict[str, int] = {}

    def record_call(self, tool_name: str):
        # Each time a tool is requested, add one count for that tool.
        self.invocations[tool_name] = self.invocations.get(tool_name, 0) + 1

    def record_success(self, tool_name: str):
        # Count successful executions for the same tool.
        self.successes[tool_name] = self.successes.get(tool_name, 0) + 1

    def record_failure(self, tool_name: str):
        # Count failed executions, so the server can tell operators how often a tool
        # is running into issues.
        self.failures[tool_name] = self.failures.get(tool_name, 0) + 1

    def get_summary(self) -> dict[str, Any]:
        # Build a quick snapshot of the tool activity.
        return {
            "total_invocations": sum(self.invocations.values()),
            "tools": {
                name: {
                    "calls": self.invocations.get(name, 0),
                    "successes": self.successes.get(name, 0),
                    "failures": self.failures.get(name, 0),
                }
                for name in self.invocations
            },
        }


metrics = ToolMetrics()


# These classes define the inputs expected by the MCP tools.
# They act like a checklist: when an LLM or client calls a tool, Python checks that
# the arguments are in the right shape before the function runs.
class AuditRepoArgs(BaseModel):
    owner: str = Field(description="GitHub repository owner or organization (e.g., 'pydantic').")
    repo: str = Field(description="GitHub repository name (e.g., 'pydantic').")


class ListIssuesArgs(BaseModel):
    owner: str = Field(description="GitHub repository owner or organization.")
    repo: str = Field(description="GitHub repository name.")
    limit: int = Field(default=5, ge=1, le=25, description="Number of open issues to retrieve (1-25).")


# These are the actual tool handlers that the MCP server exposes.
# Each function receives a validated argument object, uses the GitHub client to fetch
# data, and then turns the raw data into an easy-to-read text message.
async def audit_repository_handler(args: AuditRepoArgs) -> str:
    """Audit core repository metrics including stars, forks, language, and issue count."""
    metrics.record_call("audit_repository")
    client = GitHubClient()
    try:
        data = await client.get_repository(args.owner, args.repo)
        metrics.record_success("audit_repository")

        # Format the results in a clean text summary that an LLM or app can read.
        return (
            f"### Repository Audit: {data.full_name}\n"
            f"- **Description:** {data.description or 'N/A'}\n"
            f"- **Primary Language:** {data.language or 'Unknown'}\n"
            f"- **Stars:** {data.stargazers_count:,}\n"
            f"- **Forks:** {data.forks_count:,}\n"
            f"- **Open Issues/PRs:** {data.open_issues_count:,}\n"
            f"- **Default Branch:** {data.default_branch}\n"
            f"- **Created At:** {data.created_at.strftime('%Y-%m-%d')}\n"
            f"- **Last Updated:** {data.updated_at.strftime('%Y-%m-%d')}\n"
        )
    except GitHubNotFoundError:
        metrics.record_failure("audit_repository")
        return f"Error: Repository '{args.owner}/{args.repo}' was not found."
    except GitHubRateLimitError as e:
        metrics.record_failure("audit_repository")
        return f"Error: Rate limit exceeded. {str(e)}"
    except GitHubAPIError as e:
        metrics.record_failure("audit_repository")
        return f"Error auditing repository: {str(e)}"


async def list_open_issues_handler(args: ListIssuesArgs) -> str:
    """Fetch and summarize recent open issues for a target repository."""
    metrics.record_call("list_open_issues")
    client = GitHubClient()
    try:
        issues = await client.list_open_issues(args.owner, args.repo, limit=args.limit)
        metrics.record_success("list_open_issues")

        if not issues:
            return f"No open issues found for repository '{args.owner}/{args.repo}'."

        # Build a neat human-readable list of issues.
        output = [f"### Open Issues for {args.owner}/{args.repo} (Top {len(issues)}):\n"]
        for issue in issues:
            labels_str = f" [{', '.join(issue.labels)}]" if issue.labels else ""
            output.append(
                f"- **#{issue.number}**: {issue.title}{labels_str}\n"
                f"  - Author: @{issue.user.login} | Comments: {issue.comments}\n"
                f"  - URL: {issue.html_url}\n"
            )
        return "\n".join(output)
    except GitHubNotFoundError:
        metrics.record_failure("list_open_issues")
        return f"Error: Repository '{args.owner}/{args.repo}' not found."
    except GitHubRateLimitError as e:
        metrics.record_failure("list_open_issues")
        return f"Error: Rate limit exceeded. {str(e)}"
    except GitHubAPIError as e:
        metrics.record_failure("list_open_issues")
        return f"Error listing issues: {str(e)}"


async def get_metrics_handler() -> str:
    """Retrieve operational tool execution metrics."""
    metrics.record_call("get_metrics")
    summary = metrics.get_summary()
    metrics.record_success("get_metrics")

    # Summarize everything in plain language for debugging and monitoring.
    output = ["### MCP Server Metrics Summary:\n"]
    output.append(f"- **Total Tool Calls:** {summary['total_invocations']}\n")
    for tool, stats in summary["tools"].items():
        output.append(
            f"- **{tool}**: {stats['calls']} calls | "
            f"{stats['successes']} successes | {stats['failures']} failures"
        )
    return "\n".join(output)
