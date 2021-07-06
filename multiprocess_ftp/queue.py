import multiprocessing
from multiprocessing import JoinableQueue


class BetterQueue(JoinableQueue):
    """A better implementation of Queue."""

    def __init__(self):
        super().__init__(ctx=multiprocessing.get_context())
        self.size = SharedCounter(0)

    def __getstate__(self):
        """Help to make MyQueue instance serializable."""
        return {
            "parent_state": super().__getstate__(),
            "size": self.size,
        }

    def __setstate__(self, state):
        super().__setstate__(state["parent_state"])
        self.size = state["size"]

    def put(self, *args, **kwargs):
        super().put(*args, **kwargs)
        self.size.increment(1)

    def get(self, *args, **kwargs):
        item = super().get(*args, **kwargs)
        self.size.increment(-1)
        return item

    def qsize(self):
        """Reliable implementation of multiprocessing.Queue.qsize()"""
        return self.size.value

    def all_tasks_done(self):
        return super().all_tasks_done


class SharedCounter(object):
    """A synchronized shared counter."""

    def __init__(self, n=0):
        self.count = multiprocessing.Value("i", n)

    def increment(self, n=1):
        """Increment the counter by n (default = 1)"""
        with self.count.get_lock():
            self.count.value += n

    @property
    def value(self):
        """Return the value of the counter"""
        return self.count.value
