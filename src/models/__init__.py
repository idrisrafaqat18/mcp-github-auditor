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

# The server logs go to stderr instead of stdout.
# This matters because the app uses a stdio protocol for communication.
# If logs accidentally go to stdout, the JSON-RPC protocol can get mixed with raw log
# text and break the connection between the AI client and the tool server.
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("mcp_github_auditor")

# This is the actual MCP server object.
# It is the central entry point that exposes tool functions to LLM clients such as
# Claude Desktop, Cursor, or a custom AI agent.
mcp = MCPServer("mcp-github-auditor")


@mcp.tool()
async def audit_repository(owner: str, repo: str) -> str:
    """Audit core metrics of a GitHub repository (stars, forks, open issues, primary language)."""
    # Convert the raw arguments into a validated schema object before calling the
    # handler. This helps keep the tool interface strict and predictable.
    args = AuditRepoArgs(owner=owner, repo=repo)
    return await audit_repository_handler(args)


@mcp.tool()
async def list_open_issues(owner: str, repo: str, limit: int = 5) -> str:
    """List recent open issues for a target GitHub repository."""
    # This tool accepts a small limit so the response stays readable and does not
    # flood the user with too many issues at once.
    args = ListIssuesArgs(owner=owner, repo=repo, limit=limit)
    return await list_open_issues_handler(args)


@mcp.tool()
async def get_metrics() -> str:
    """Retrieve operational tool invocation and error metrics for this MCP server session."""
    return await get_metrics_handler()


if __name__ == "__main__":
    # This is the startup point when the server is launched directly.
    # It tells the MCP framework to begin listening for incoming tool calls.
    logger.info("Starting MCP GitHub Auditor Server via stdio transport...")
    mcp.run()
