"""Proxy that lets process workers talk to a shared queue."""
from multiprocessing.managers import BaseProxy
from queue import Empty


class BetterProxy(BaseProxy):
    """Better because it lets us use BetterQueue, which actually is better."""

    def __init__(self, *args, **kwargs):
        """Initialize the proxy."""
        super().__init__(*args, **kwargs)

    def qsize(self):
        """Proxy handler for size of queue."""
        return self._callmethod("qsize")

    def get(self):
        """Proxy handler for getting objects from a shared queue."""
        try:
            return self._callmethod("get_nowait")
        except Empty:
            return []

    def put(self, value):
        """Proxy handler for putting objects in a shared queue."""
        self._callmethod("put_nowait", kwds={"obj": value})

    def join(self):
        """Proxy handler for closing a shared queue."""
        self._callmethod("join")

    def task_done(self):
        """Proxy handler for telling a shared queue a task is complete."""
        self._callmethod("task_done")

    def all_tasks_done(self):
        """Proxy handler for determining if a queue has been exhausted."""
        return self._callmethod("all_tasks_done")

    def empty(self):
        """Proxy handler for determining if a queue has been exhausted."""
        return self._callmethod("empty")
