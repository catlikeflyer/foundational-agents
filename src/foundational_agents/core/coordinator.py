"""ProjectCoordinator — the central orchestrator for multi-agent delegation.

The coordinator exposes each persona worker as a callable *tool* to an
Antigravity Agent. When prompted, the coordinator agent autonomously decides
which worker(s) to invoke, in what order, and how to synthesize their outputs
into a cohesive final response.
"""

from __future__ import annotations

from google.antigravity import Agent, LocalAgentConfig, ToolContext

from foundational_agents.core.state import SharedStateMatrix
from foundational_agents.core.workers import (
    MarketingAnalystWorker,
    PresentationMakerWorker,
    ProjectManagerWorker,
    SystemDesignerWorker,
)


COORDINATOR_PROMPT = """\
You are the **Project Coordinator** — a senior orchestration agent responsible \
for analyzing complex, multi-faceted requests and delegating work to a team of \
specialized workers.

## Your Team
You have four specialized workers available as tools:

| Tool | Specialist | Use When |
|------|-----------|----------|
| `delegate_to_presentation_maker` | Presentation Maker | The request involves slides, decks, outlines, or visual storytelling. |
| `delegate_to_project_manager` | Project Manager | The request involves planning, timelines, milestones, resource allocation, or risk. |
| `delegate_to_system_designer` | System Design Engineer | The request involves architecture, APIs, data modeling, or technical design. |
| `delegate_to_marketing_analyst` | Marketing Analyst | The request involves market research, competitive analysis, positioning, or GTM. |

## Orchestration Rules
1. **Analyze first.** Before delegating, identify which aspects of the request \
map to which specialist(s).
2. **Delegate in logical order.** If tasks have dependencies (e.g., system design \
before project planning), respect the order.
3. **Use multiple workers** when the request spans multiple domains. Don't try to \
handle everything with a single worker.
4. **Synthesize results.** After all delegations complete, produce a unified \
executive summary that weaves together all worker outputs into a coherent response.
5. **Be explicit** about what you asked each worker and why.

## Output Structure
Your final response should follow this structure:
1. **Request Analysis** — brief breakdown of the request dimensions.
2. **Delegation Summary** — which workers were engaged and what they were asked.
3. **Integrated Results** — the synthesized output from all workers.
4. **Next Steps** — recommended follow-up actions.
"""


class ProjectCoordinator:
    """Orchestrate a team of specialized agent workers.

    The coordinator wraps each worker's ``execute()`` method in a tool function
    that the Antigravity coordinator agent can call autonomously. Shared state
    is tracked in a ``SharedStateMatrix`` that accumulates context across
    delegations within a single run.

    Args:
        model: The Gemini model identifier to use for all agents.

    Usage::

        coordinator = ProjectCoordinator()
        result = await coordinator.run("Design a microservices platform")
    """

    def __init__(self, model: str | None = None) -> None:
        self.model = model
        self.state = SharedStateMatrix()
        self.workers = {
            "presentation_maker": PresentationMakerWorker(model),
            "project_manager": ProjectManagerWorker(model),
            "system_designer": SystemDesignerWorker(model),
            "marketing_analyst": MarketingAnalystWorker(model),
        }

    def _build_delegation_tools(self) -> list:
        """Create tool functions that the coordinator agent can call.

        Each tool function wraps a worker's ``execute()`` method, injecting
        the shared state matrix automatically. The coordinator agent sees these
        as callable tools with clear docstrings.

        Returns:
            List of async tool functions.
        """
        state = self.state
        workers = self.workers

        async def delegate_to_presentation_maker(task: str) -> str:
            """Delegate a task to the Presentation Maker specialist.

            Use this tool when the request involves creating slide decks,
            presentation outlines, visual storytelling structures, or
            speaker-ready materials.

            Args:
                task: A clear description of what the Presentation Maker should produce.
            """
            return await workers["presentation_maker"].execute(task, state)

        async def delegate_to_project_manager(task: str) -> str:
            """Delegate a task to the Project Manager specialist.

            Use this tool when the request involves planning timelines,
            creating work breakdown structures, tracking milestones,
            allocating resources, or assessing risks.

            Args:
                task: A clear description of what the Project Manager should produce.
            """
            return await workers["project_manager"].execute(task, state)

        async def delegate_to_system_designer(task: str) -> str:
            """Delegate a task to the System Design Engineer specialist.

            Use this tool when the request involves architecting systems,
            designing APIs, modeling data flows, creating technical specs,
            or evaluating scalability trade-offs.

            Args:
                task: A clear description of what the System Designer should produce.
            """
            return await workers["system_designer"].execute(task, state)

        async def delegate_to_marketing_analyst(task: str) -> str:
            """Delegate a task to the Marketing Analyst specialist.

            Use this tool when the request involves market research,
            competitive analysis, customer segmentation, positioning
            strategies, or go-to-market planning.

            Args:
                task: A clear description of what the Marketing Analyst should produce.
            """
            return await workers["marketing_analyst"].execute(task, state)

        return [
            delegate_to_presentation_maker,
            delegate_to_project_manager,
            delegate_to_system_designer,
            delegate_to_marketing_analyst,
        ]

    async def run(self, request: str) -> str:
        """Execute a full orchestration cycle.

        The coordinator agent analyzes the request, decides which workers to
        engage, delegates via tool calls, and synthesizes a unified response.

        Args:
            request: The user's project request or question.

        Returns:
            The coordinator's synthesized text response.
        """
        # Initialize state with the project context
        self.state = SharedStateMatrix(project_context=request, phase="orchestrating")

        # Build delegation tools bound to current state
        delegation_tools = self._build_delegation_tools()

        kwargs = {
            "system_instructions": COORDINATOR_PROMPT,
            "tools": delegation_tools,
        }
        if self.model:
            kwargs["model"] = self.model

        config = LocalAgentConfig(**kwargs)

        async with Agent(config) as agent:
            response = await agent.chat(request)
            return await response.text()

    async def run_single_worker(self, worker_key: str, task: str) -> str:
        """Execute a task against a single specific worker.

        Bypasses the coordinator agent and directly invokes one worker.
        Useful when the caller already knows which specialist to engage.

        Args:
            worker_key: One of 'presentation_maker', 'project_manager',
                'system_designer', or 'marketing_analyst'.
            task: The task description.

        Returns:
            The worker's text response.

        Raises:
            KeyError: If worker_key is not recognized.
        """
        if worker_key not in self.workers:
            valid = ", ".join(sorted(self.workers.keys()))
            raise KeyError(
                f"Unknown worker '{worker_key}'. Valid keys: {valid}"
            )

        self.state = SharedStateMatrix(project_context=task, phase="direct_execution")
        worker = self.workers[worker_key]
        return await worker.execute(task, self.state)
