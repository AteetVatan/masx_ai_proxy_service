"""
CPU executor utilities for concurrent operations.
"""

import asyncio
import concurrent.futures
from typing import Any, Callable, Coroutine
from functools import partial


class CPUExecutors:
    """Manages CPU-bound operations using thread pools."""
    
    def __init__(self, max_workers: int = None):
        """Initialize CPU executors with optional max workers."""
        self.max_workers = max_workers
        self._executor = None
    
    @property
    def executor(self) -> concurrent.futures.ThreadPoolExecutor:
        """Get or create thread pool executor."""
        if self._executor is None:
            self._executor = concurrent.futures.ThreadPoolExecutor(
                max_workers=self.max_workers
            )
        return self._executor
    
    async def run_in_thread(
        self, 
        func: Callable[..., Any], 
        *args, 
        **kwargs
    ) -> Any:
        """Run a function in a thread pool executor."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            partial(func, *args, **kwargs)
        )
    
    async def run_batch(
        self,
        func: Callable[..., Any],
        items: list,
        *args,
        **kwargs
    ) -> list:
        """Run a function on multiple items concurrently."""
        tasks = [
            self.run_in_thread(func, item, *args, **kwargs)
            for item in items
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    def shutdown(self):
        """Shutdown the executor."""
        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()
