"""Test suite for proxy classes."""
from multiprocessing.managers import BaseManager

from multiprocess_ftp import better_queue
from multiprocess_ftp.proxy import BetterProxy


def test_better_proxy():
    BaseManager.register(
        "BetterQueue", better_queue.BetterQueue, proxytype=BetterProxy
    )
    manager = BaseManager()
    manager.start()
    better_proxy = manager.BetterQueue()

    assert not better_proxy.qsize()

    expected_object = ["foo"]
    better_proxy.put(expected_object)

    actual_tasks_done = better_proxy.all_tasks_done()

    assert not actual_tasks_done

    better_proxy.get()
    better_proxy.task_done()

    actual_tasks_done = better_proxy.all_tasks_done()

    assert not better_proxy.qsize()
    assert actual_tasks_done

    assert not better_proxy.get()
    better_proxy.join()
