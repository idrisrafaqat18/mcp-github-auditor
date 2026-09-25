# Architectural Decisions Log

## ADR 001: Pydantic v2 Schema Boundary Validation
* **What:** Enforce strict Pydantic v2 parsing on all raw JSON responses returned by the GitHub REST API.
* **Why:** Prevents non-deterministic responses or unexpected schema shifts from polluting the MCP server tools or propagating broken payloads to LLM clients.
* **Trade-off:** Adds slight serialization overhead per request, requiring manual model maintenance when GitHub updates API schemas.

## ADR 002: Dedicated Exception Handling over Soft Failure
* **What:** Raise structured domain exceptions (`GitHubRateLimitError`, `GitHubNotFoundError`) rather than returning empty payloads or untyped dictionaries.
* **Why:** Allows the MCP tool layer to serialize meaningful error contexts directly back to the LLM agent without terminating the process stream.
* **Trade-off:** Requires explicit `try/except` blocks in tool implementations.

## ADR 003: In-Memory Metric Diagnostics for MCP Tool Handlers
* **What:** Implement a lightweight `ToolMetrics` accumulator tracking call counts, successes, and failures across tool invocations.
* **Why:** Provides measurable insight into tool usage patterns, failure rates, and LLM agent misdirections without requiring external observability infrastructure during local development.
* **Trade-off:** Metrics reset upon server restart. (Future expansion: persistent storage or Prometheus endpoint).