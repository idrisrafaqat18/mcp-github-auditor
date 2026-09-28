import logging
import sys
from mcp.server.mcpserver import MCPServer

from .config import settings
from .tools.read_only import (
    AuditRepoArgs,
    ListIssuesArgs,
    audit_repository_handler,
    get_metrics_handler,
    list_open_issues_handler,
)

# Configure logging explicitly to stderr to prevent stdio protocol corruption
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("mcp_github_auditor")

# Initialize MCPServer Instance (MCP 2.x)
mcp = MCPServer("mcp-github-auditor")


@mcp.tool()
async def audit_repository(owner: str, repo: str) -> str:
    """Audit core metrics of a GitHub repository (stars, forks, open issues, primary language)."""
    args = AuditRepoArgs(owner=owner, repo=repo)
    return await audit_repository_handler(args)


@mcp.tool()
async def list_open_issues(owner: str, repo: str, limit: int = 5) -> str:
    """List recent open issues for a target GitHub repository."""
    args = ListIssuesArgs(owner=owner, repo=repo, limit=limit)
    return await list_open_issues_handler(args)


@mcp.tool()
async def get_metrics() -> str:
    """Retrieve operational tool invocation and error metrics for this MCP server session."""
    return await get_metrics_handler()


if __name__ == "__main__":
    logger.info("Starting MCP GitHub Auditor Server via stdio transport...")
    mcp.run()