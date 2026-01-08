"""Scheduler for parallel task execution."""

import asyncio
from collections.abc import Coroutine
from typing import Any


class Scheduler:
    """Scheduler for controlling parallel execution."""

    def __init__(self, max_parallel: int | None = None):
        """
        Initialize scheduler.

        Args:
            max_parallel: Maximum number of parallel tasks (None = unlimited)
        """
        self.max_parallel = max_parallel

    async def execute_tasks(self, tasks: list[Coroutine[Any, Any, None]]) -> None:
        """
        Execute tasks with parallelism control.

        Args:
            tasks: List of coroutines to execute
        """
        if self.max_parallel is None:
            # Execute all tasks in parallel
            await asyncio.gather(*tasks)
        else:
            # Execute with semaphore to limit parallelism
            semaphore = asyncio.Semaphore(self.max_parallel)

            async def execute_with_semaphore(task: Coroutine[Any, Any, None]) -> None:
                async with semaphore:
                    await task

            await asyncio.gather(*[execute_with_semaphore(task) for task in tasks])

