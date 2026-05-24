"""my-foundational-agents: Async orchestration hub for specialized AI agent personas."""

from my_foundational_agents.core.coordinator import ProjectCoordinator
from my_foundational_agents.core.state import SharedStateMatrix, TaskEntry
from my_foundational_agents.core.workers import (
    MarketingAnalystWorker,
    PresentationMakerWorker,
    ProjectManagerWorker,
    SystemDesignerWorker,
)

__all__ = [
    "ProjectCoordinator",
    "SharedStateMatrix",
    "TaskEntry",
    "PresentationMakerWorker",
    "ProjectManagerWorker",
    "SystemDesignerWorker",
    "MarketingAnalystWorker",
]

__version__ = "0.1.0"
