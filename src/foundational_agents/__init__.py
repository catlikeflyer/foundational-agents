"""foundational-agents: Async orchestration hub for specialized AI agent personas."""

from foundational_agents.core.coordinator import ProjectCoordinator
from foundational_agents.core.state import SharedStateMatrix, TaskEntry
from foundational_agents.core.workers import (
    CodeDocumenterWorker,
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
    "CodeDocumenterWorker",
]

__version__ = "0.1.0"
