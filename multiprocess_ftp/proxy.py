from multiprocessing.managers import BaseProxy

from _queue import Empty


class BetterProxy(BaseProxy):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def qsize(self):
        return self._callmethod("qsize")

    def get(self):
        try:
            return self._callmethod("get_nowait")
        except Empty:
            pass

    def put(self, value):
        self._callmethod("put_nowait", kwds={"obj": value})

    def join(self):
        self._callmethod("join")

    def task_done(self):
        self._callmethod("task_done")

    def all_tasks_done(self):
        return self._callmethod("all_tasks_done")
