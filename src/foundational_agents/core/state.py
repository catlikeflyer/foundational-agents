"""Shared state tracking matrix for cross-worker coordination.

The SharedStateMatrix provides a thread-safe, async-compatible data structure
that workers read from and write to during orchestrated execution. It tracks
project context, individual task progress, accumulated artifacts, and the
current workflow phase.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TaskStatus(Enum):
    """Lifecycle states for a tracked task."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class TaskEntry:
    """A single unit of work tracked by the state matrix.

    Attributes:
        task_id: Unique identifier for this task.
        description: Human-readable summary of what needs to be done.
        assigned_worker: Name of the worker class handling this task.
        status: Current lifecycle status.
        output: Result text produced by the worker, if complete.
        metadata: Arbitrary key-value pairs for worker-specific data.
    """

    task_id: str
    description: str
    assigned_worker: str = ""
    status: TaskStatus = TaskStatus.PENDING
    output: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def mark_in_progress(self, worker: str) -> None:
        """Assign a worker and transition to in-progress."""
        self.assigned_worker = worker
        self.status = TaskStatus.IN_PROGRESS

    def mark_complete(self, output: str) -> None:
        """Record output and transition to complete."""
        self.output = output
        self.status = TaskStatus.COMPLETE

    def mark_failed(self, reason: str) -> None:
        """Record failure reason and transition to failed."""
        self.output = reason
        self.status = TaskStatus.FAILED


@dataclass
class SharedStateMatrix:
    """Centralized state shared across all workers in an orchestration run.

    Provides async-safe access to project context, task registry,
    accumulated artifacts, and current workflow phase.

    Attributes:
        project_context: High-level description of the project being worked on.
        tasks: Registry mapping task IDs to their TaskEntry records.
        artifacts: Ordered list of output artifact strings produced by workers.
        phase: Current workflow phase label (e.g. 'planning', 'execution', 'review').
    """

    project_context: str = ""
    tasks: dict[str, TaskEntry] = field(default_factory=dict)
    artifacts: list[str] = field(default_factory=list)
    phase: str = "initialized"
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)

    async def add_task(
        self,
        task_id: str,
        description: str,
        assigned_worker: str = "",
    ) -> TaskEntry:
        """Register a new task in the state matrix.

        Args:
            task_id: Unique identifier for the task.
            description: What the task entails.
            assigned_worker: Optional worker name to pre-assign.

        Returns:
            The newly created TaskEntry.
        """
        async with self._lock:
            entry = TaskEntry(
                task_id=task_id,
                description=description,
                assigned_worker=assigned_worker,
            )
            self.tasks[task_id] = entry
            return entry

    async def update_task(
        self,
        task_id: str,
        status: TaskStatus | None = None,
        output: str | None = None,
        worker: str | None = None,
    ) -> TaskEntry:
        """Update fields on an existing task.

        Args:
            task_id: The task to update.
            status: New status, if changing.
            output: New output text, if available.
            worker: New worker assignment, if changing.

        Returns:
            The updated TaskEntry.

        Raises:
            KeyError: If task_id is not found.
        """
        async with self._lock:
            entry = self.tasks[task_id]
            if status is not None:
                entry.status = status
            if output is not None:
                entry.output = output
            if worker is not None:
                entry.assigned_worker = worker
            return entry

    async def add_artifact(self, artifact: str) -> None:
        """Append a completed artifact to the collection."""
        async with self._lock:
            self.artifacts.append(artifact)

    async def set_phase(self, phase: str) -> None:
        """Transition the workflow to a new phase."""
        async with self._lock:
            self.phase = phase

    def build_context_summary(self) -> str:
        """Build a text summary of the current state for worker context injection.

        Returns:
            A formatted string summarizing project context, task statuses,
            and accumulated artifacts.
        """
        lines: list[str] = []
        lines.append(f"## Project Context\n{self.project_context}")
        lines.append(f"\n## Current Phase: {self.phase}")

        if self.tasks:
            lines.append("\n## Task Registry")
            for tid, entry in self.tasks.items():
                status_icon = {
                    TaskStatus.PENDING: "⏳",
                    TaskStatus.IN_PROGRESS: "🔄",
                    TaskStatus.COMPLETE: "✅",
                    TaskStatus.FAILED: "❌",
                }.get(entry.status, "❓")
                worker_info = f" [{entry.assigned_worker}]" if entry.assigned_worker else ""
                lines.append(f"- {status_icon} `{tid}`{worker_info}: {entry.description}")
                if entry.output:
                    # Truncate long outputs for context injection
                    preview = entry.output[:500]
                    if len(entry.output) > 500:
                        preview += "..."
                    lines.append(f"  Output: {preview}")

        if self.artifacts:
            lines.append(f"\n## Artifacts ({len(self.artifacts)} total)")
            for i, artifact in enumerate(self.artifacts, 1):
                preview = artifact[:200]
                if len(artifact) > 200:
                    preview += "..."
                lines.append(f"### Artifact {i}\n{preview}")

        return "\n".join(lines)
