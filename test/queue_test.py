"""Test suite for queue classes."""
from unittest.mock import Mock

import pytest

from multiprocess_ftp.better_queue import BetterQueue


def test_better_queue():
    better_queue = BetterQueue()
    expected_object, expected_count = ["foo"], 1
    better_queue.put(expected_object)

    actual_count = better_queue.qsize()

    assert expected_count == actual_count

    better_queue.put(expected_object)
    expected_count += 1

    actual_count = better_queue.qsize()

    assert expected_count == actual_count

    expected_count -= 1

    actual_object = better_queue.get()
    actual_count = better_queue.qsize()

    assert expected_object == actual_object
    assert expected_count == actual_count


def test_better_queue_all_tasks_done():
    better_queue = BetterQueue()
    expected_object = ["foo"]
    better_queue.put(expected_object)

    actual_tasks_done = better_queue.all_tasks_done()

    assert not actual_tasks_done

    better_queue.get()

    actual_tasks_done = better_queue.all_tasks_done()

    assert not better_queue.qsize()
    assert actual_tasks_done


def test_better_queue_raises_runtime_error():
    better_queue = BetterQueue()
    with pytest.raises(RuntimeError):
        assert not better_queue.__getstate__()


def test_better_queue_set_state():
    better_queue = BetterQueue()
    better_queue.__setstate__(
        {
            "parent_state": [
                Mock(),
                Mock(),
                Mock(),
                Mock(),
                Mock(),
                Mock(),
                Mock(),
                Mock(),
                Mock(),
                Mock(),
            ]
        }
    )

    better_queue.size.increment(1)

    assert better_queue.qsize() == 1
