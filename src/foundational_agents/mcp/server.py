"""FastMCP server exposing foundational agent tools via stdio transport.

This module registers each agent persona as a standalone MCP tool, plus a
full orchestration tool that delegates across all workers. Designed to be
consumed by host environments like Claude Desktop, Claude Code, or any
MCP-compatible client.

Run directly::

    python -m foundational_agents.mcp.server

Or configure in Claude Desktop's ``claude_desktop_config.json``::

    {
      "mcpServers": {
        "foundational-agents": {
          "command": "python",
          "args": ["-m", "foundational_agents.mcp.server"]
        }
      }
    }
"""

from __future__ import annotations

import os
import sys
from typing import Annotated

from mcp.server.fastmcp import FastMCP

from foundational_agents.core.coordinator import ProjectCoordinator
from foundational_agents.core.state import SharedStateMatrix
from foundational_agents.core.workers import (
    MarketingAnalystWorker,
    PresentationMakerWorker,
    ProjectManagerWorker,
    SystemDesignerWorker,
)


# ---------------------------------------------------------------------------
# Pre-flight check: ensure API key is available
# ---------------------------------------------------------------------------

def _check_api_key() -> None:
    """Warn (but don't crash) if GEMINI_API_KEY is missing."""
    if not os.environ.get("GEMINI_API_KEY"):
        print(
            "[foundational-agents] WARNING: GEMINI_API_KEY not set. "
            "Agent tools will fail at runtime. "
            "Get a key at https://aistudio.google.com/app/api-keys",
            file=sys.stderr,
        )

def _get_model() -> str | None:
    """Get the model to use from the environment. Returns None to use the SDK default."""
    return os.environ.get("FOUNDATIONAL_AGENTS_MODEL")


# ---------------------------------------------------------------------------
# FastMCP Server Instance
# ---------------------------------------------------------------------------

mcp = FastMCP("foundational-agents")


# ---------------------------------------------------------------------------
# Full Orchestration Tool
# ---------------------------------------------------------------------------

@mcp.tool()
async def coordinate_project(
    request: Annotated[str, "A detailed project request to orchestrate across multiple specialist agents."],
) -> str:
    """Orchestrate a multi-agent team to fulfill a complex project request.

    The Project Coordinator analyzes the request, delegates to relevant
    specialists (Presentation Maker, Project Manager, System Designer,
    Marketing Analyst), and synthesizes their outputs into a unified response.

    Best for: complex, multi-faceted requests that span multiple domains.
    """
    _check_api_key()
    coordinator = ProjectCoordinator(model=_get_model())
    return await coordinator.run(request)


# ---------------------------------------------------------------------------
# Individual Worker Tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def create_presentation(
    request: Annotated[str, "What kind of presentation, deck, or outline to create. Include audience, purpose, and constraints."],
) -> str:
    """Build presentation structures, slide deck templates, or outlines.

    The Presentation Maker designs narrative-driven slide decks with proper
    visual hierarchy, speaker notes, and audience-adaptive formatting.
    """
    _check_api_key()
    worker = PresentationMakerWorker(model=_get_model())
    state = SharedStateMatrix(project_context=request, phase="direct_execution")
    return await worker.execute(request, state)


@mcp.tool()
async def manage_project(
    request: Annotated[str, "The project planning task: timeline creation, resource allocation, risk assessment, sprint planning, etc."],
) -> str:
    """Plan timelines, track milestones, allocate resources, and manage workflows.

    The Project Manager produces work breakdown structures, Gantt-style
    timelines, RACI matrices, risk registers, and sprint plans.
    """
    _check_api_key()
    worker = ProjectManagerWorker(model=_get_model())
    state = SharedStateMatrix(project_context=request, phase="direct_execution")
    return await worker.execute(request, state)


@mcp.tool()
async def design_system(
    request: Annotated[str, "The system design challenge: architecture, API design, data modeling, scalability, etc."],
) -> str:
    """Architect systems, design APIs, model data flows, and produce technical specs.

    The System Design Engineer follows a structured methodology from
    requirements through high-level and detailed design, with trade-off
    analysis and capacity estimates.
    """
    _check_api_key()
    worker = SystemDesignerWorker(model=_get_model())
    state = SharedStateMatrix(project_context=request, phase="direct_execution")
    return await worker.execute(request, state)


@mcp.tool()
async def analyze_market(
    request: Annotated[str, "The market analysis task: competitive landscape, market sizing, positioning, GTM strategy, etc."],
) -> str:
    """Analyze markets, competitive landscapes, positioning strategies, and campaigns.

    The Marketing Analyst delivers data-grounded analysis with TAM/SAM/SOM
    sizing, competitor matrices, customer personas, and actionable recommendations.
    """
    _check_api_key()
    worker = MarketingAnalystWorker(model=_get_model())
    state = SharedStateMatrix(project_context=request, phase="direct_execution")
    return await worker.execute(request, state)


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the FastMCP server in stdio transport mode."""
    _check_api_key()
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
