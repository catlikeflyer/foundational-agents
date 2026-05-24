"""ProjectCoordinator — the central orchestrator for multi-agent delegation.

The coordinator exposes each persona worker as a callable *tool* to an
Antigravity Agent. When prompted, the coordinator agent autonomously decides
which worker(s) to invoke, in what order, and how to synthesize their outputs
into a cohesive final response.
"""

from __future__ import annotations

from google.antigravity import Agent, LocalAgentConfig, ToolContext
from mcp.server.fastmcp import Context

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

    def _build_delegation_tools(self, ctx: Context | None = None) -> list:
        """Create tool functions that the coordinator agent can call.

        Each tool function wraps a worker's ``execute()`` method, injecting
        the shared state matrix automatically. The coordinator agent sees these
        as callable tools with clear docstrings.

        Args:
            ctx: The MCP FastMCP Context for sampling back to client LLM.

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
            return await workers["presentation_maker"].execute(task, state, ctx=ctx)

        async def delegate_to_project_manager(task: str) -> str:
            """Delegate a task to the Project Manager specialist.

            Use this tool when the request involves planning timelines,
            creating work breakdown structures, tracking milestones,
            allocating resources, or assessing risks.

            Args:
                task: A clear description of what the Project Manager should produce.
            """
            return await workers["project_manager"].execute(task, state, ctx=ctx)

        async def delegate_to_system_designer(task: str) -> str:
            """Delegate a task to the System Design Engineer specialist.

            Use this tool when the request involves architecting systems,
            designing APIs, modeling data flows, creating technical specs,
            or evaluating scalability trade-offs.

            Args:
                task: A clear description of what the System Designer should produce.
            """
            return await workers["system_designer"].execute(task, state, ctx=ctx)

        async def delegate_to_marketing_analyst(task: str) -> str:
            """Delegate a task to the Marketing Analyst specialist.

            Use this tool when the request involves market research,
            competitive analysis, customer segmentation, positioning
            strategies, or go-to-market planning.

            Args:
                task: A clear description of what the Marketing Analyst should produce.
            """
            return await workers["marketing_analyst"].execute(task, state, ctx=ctx)

        return [
            delegate_to_presentation_maker,
            delegate_to_project_manager,
            delegate_to_system_designer,
            delegate_to_marketing_analyst,
        ]

    async def run(self, request: str, ctx: Context | None = None) -> str:
        """Execute a full orchestration cycle.

        The coordinator agent analyzes the request, decides which workers to
        engage, delegates via tool calls, and synthesizes a unified response.

        Args:
            request: The user's project request or question.
            ctx: The MCP FastMCP Context for sampling back to client LLM.

        Returns:
            The coordinator's synthesized text response.
        """
        # Initialize state with the project context
        self.state = SharedStateMatrix(project_context=request, phase="orchestrating")

        # 1. Try to orchestrate using the host's native LLM via sampling
        if ctx is not None:
            try:
                await ctx.info("[coordinator] Performing initial request decomposition via host LLM sampling...")
                
                planning_system_prompt = (
                    "You are the Planning Module of the Project Coordinator. Your job is to analyze a user's request "
                    "and decompose it into a sequence of tasks that must be executed by specialized workers. "
                    "You have the following workers available:\n"
                    "- `presentation_maker`: For slides, outlines, decks, and visual structure.\n"
                    "- `project_manager`: For sprint plans, Gantt charts, risk matrices, and timelines.\n"
                    "- `system_designer`: For system architecture, API specifications, and database schemas.\n"
                    "- `marketing_analyst`: For competitor analysis, market sizing, and marketing strategy.\n\n"
                    "Analyze the request and return a JSON list of tasks to execute. "
                    "Each task in the list MUST be a JSON object with the following fields:\n"
                    "1. `worker`: The worker key (one of the 4 strings listed above)\n"
                    "2. `task`: A descriptive task instruction containing all context needed for that worker.\n\n"
                    "Rules:\n"
                    "- Determine the logical sequence (e.g., design system before planning project timeline).\n"
                    "- Only return a valid JSON array. Do not wrap it in markdown code blocks like ```json."
                )
                
                from mcp.types import SamplingMessage, TextContent
                
                planning_msg = [
                    SamplingMessage(
                        role="user",
                        content=TextContent(type="text", text=f"Analyze and decompose the following request:\n\n{request}"),
                    )
                ]
                
                planning_result = await ctx.session.create_message(
                    messages=planning_msg,
                    system_prompt=planning_system_prompt,
                    max_tokens=2000,
                )
                
                planning_text = planning_result.content.text.strip()
                
                # Parse JSON tasks. If it has markdown code blocks, strip them.
                if planning_text.startswith("```"):
                    lines = planning_text.splitlines()
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines and lines[-1].startswith("```"):
                        lines = lines[:-1]
                    planning_text = "\n".join(lines).strip()
                
                import json
                try:
                    tasks = json.loads(planning_text)
                except Exception:
                    # Fallback regex extraction of JSON list
                    import re
                    match = re.search(r"\[\s*\{.*\}\s*\]", planning_text, re.DOTALL)
                    if match:
                        tasks = json.loads(match.group(0))
                    else:
                        raise ValueError("No JSON array found in planner output")
                
                await ctx.info(f"[coordinator] Decomposed request into {len(tasks)} task(s). Executing workers...")
                
                # Execute each task in sequence using sampling
                for item in tasks:
                    worker_key = item["worker"]
                    worker_task = item["task"]
                    
                    if worker_key in self.workers:
                        await ctx.info(f"[coordinator] Delegating task to {worker_key}...")
                        await self.workers[worker_key].execute(worker_task, self.state, ctx=ctx)
                    else:
                        await ctx.warning(f"[coordinator] Unknown worker key '{worker_key}' returned by planner. Skipping.")
                
                # Synthesize the final response
                await ctx.info("[coordinator] Synthesizing worker outputs via host LLM sampling...")
                
                synthesis_system_prompt = (
                    "You are the Project Coordinator. You have orchestrated a team of specialists to work on a request. "
                    "Your job is to synthesize all their outputs and compile a final, comprehensive response for the user. "
                    "Format your response professionally with clear sections:\n"
                    "1. Request Analysis\n"
                    "2. Delegation Summary\n"
                    "3. Integrated Results (synthesizing all the specialized sections)\n"
                    "4. Next Steps"
                )
                
                context_summary = self.state.build_context_summary()
                synthesis_prompt = (
                    f"Original Request:\n{request}\n\n"
                    f"Specialists Outputs:\n{context_summary}\n\n"
                    "Please synthesize these outputs into a single, cohesive, premium final response."
                )
                
                synthesis_msg = [
                    SamplingMessage(
                        role="user",
                        content=TextContent(type="text", text=synthesis_prompt),
                    )
                ]
                
                synthesis_result = await ctx.session.create_message(
                    messages=synthesis_msg,
                    system_prompt=synthesis_system_prompt,
                    max_tokens=4000,
                )
                
                return synthesis_result.content.text
                
            except Exception as e:
                await ctx.warning(
                    f"[coordinator] Sampling planning failed. Falling back to local google-antigravity Agent. Error: {e}"
                )

        # 2. Fallback / direct run via google-antigravity Agent
        # Build delegation tools bound to current state (and passing ctx so workers can still try sampling!)
        delegation_tools = self._build_delegation_tools(ctx)

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

    async def run_single_worker(self, worker_key: str, task: str, ctx: Context | None = None) -> str:
        """Execute a task against a single specific worker.

        Bypasses the coordinator agent and directly invokes one worker.
        Useful when the caller already knows which specialist to engage.

        Args:
            worker_key: One of 'presentation_maker', 'project_manager',
                'system_designer', or 'marketing_analyst'.
            task: The task description.
            ctx: The MCP FastMCP Context for sampling back to client LLM.

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
        return await worker.execute(task, self.state, ctx=ctx)
