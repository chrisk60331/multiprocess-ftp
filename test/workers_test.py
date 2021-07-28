"""Tests for worker classes."""
import os
from unittest.mock import Mock, call, patch

import pytest

SOURCE_PATH = "multiprocess_ftp.workers"


def test_chunk_worker():
    from multiprocess_ftp.workers import ChunkWorker

    mock_open = Mock(
        return_value=Mock(
            __enter__=Mock(return_value=Mock(seek=Mock())),
            __exit__=Mock(return_value=9),
        )
    )
    mock_destination = Mock(put=Mock(return_value={"ETag": "foo"}))
    mock_host = Mock(
        open=mock_open,
    )
    mock_chunk_queue = Mock(
        get=Mock(
            side_effect=[
                [("spam", "eggs", (1, 1)), mock_destination],
                [],
                StopIteration,
            ]
        )
    )
    mock_ftp = Mock(
        return_value=Mock(
            __enter__=Mock(return_value=mock_host),
            __exit__=Mock(return_value=mock_host),
        )
    )
    mock_chunk_results_queue = Mock()
    chunky = ChunkWorker(
        mock_ftp,
        mock_chunk_queue,
        mock_chunk_results_queue,
        {},
        mock_destination,
        "spam",
    )
    with pytest.raises(StopIteration):
        chunky.run()
    mock_open.assert_called()
    mock_chunk_queue.task_done.assert_called_once_with()
    mock_chunk_results_queue.put.assert_called_once_with(("foo", "eggs"))


@pytest.mark.parametrize(
    "start, expected", [(10, 11), (100, 101), (-500, -499)]
)
def test_worker_number(start, expected):
    from multiprocess_ftp.downloader import WorkerNumber

    worker_number = WorkerNumber(start)

    assert expected == next(worker_number)


def test_download_worker_run():
    from multiprocess_ftp.better_queue import BetterQueue
    from multiprocess_ftp.workers import TransferWorker

    destination_mock = Mock(__enter__=Mock(), __exit__=Mock())
    mock_host = Mock(open=Mock(__enter__=Mock()))
    mock_ftp = Mock(return_value=Mock(__enter__=mock_host, __exit__=Mock()))
    mock_download_queue = Mock(
        get=Mock(
            side_effect=[
                [
                    {},
                    "eg.gz",
                    destination_mock,
                ],
                [],
                StopIteration,
            ]
        )
    )
    mock_walk_queue = BetterQueue()
    mock_result_queue = BetterQueue()
    mock_download_queue.put((None, {}))
    mock_chunk_result_queue = Mock(
        get=Mock(return_value=["eggs", "spam"]),
        empty=Mock(side_effect=[0, 1]),
    )
    with patch(f"{SOURCE_PATH}.ChunkWorker"), patch(
        f"{SOURCE_PATH}.TransferWorker.get_chunks", return_value=["foo"]
    ), patch(
        f"{SOURCE_PATH}.queue.Queue", return_value=mock_chunk_result_queue
    ):
        worker = TransferWorker(
            "spam_worker1",
            mock_ftp,
            mock_download_queue,
            mock_walk_queue,
            mock_result_queue,
        )

        with pytest.raises(StopIteration):
            worker.run()


def test_directory_worker_run():
    from multiprocess_ftp.workers import DirectoryWorker

    mock_walk_queue = Mock(
        get=Mock(side_effect=[[{"subdirectory": "foo"}, Mock()], []])
    )
    mock_result_queue = Mock()
    mock_download_queue = Mock()
    mock_walk_results = Mock(return_value=("foo", "bar", "baz"))
    mock_worker = DirectoryWorker(
        "eggs_worker3",
        Mock(),
        mock_download_queue,
        mock_walk_queue,
        mock_result_queue,
    )
    with patch(
        f"{SOURCE_PATH}.DirectoryWorker.walk_remote_directory",
        mock_walk_results,
    ):

        with pytest.raises(StopIteration):
            mock_worker.run()


@pytest.mark.parametrize(
    "expected",
    [
        ("foo", ["bar"], ["baz"]),
        ("foo", ["bar", "cheese"], ["baz"]),
        ("foo", ["bar"], ["rice", "vegetables"]),
        (
            "/app/test/data",
            [],
            [
                "/app/test/data/TNR2.md5",
                "/app/test/data/TNR2_202007.report.txt",
                "/app/test/data/TNR2_CA.txt.gpg",
            ],
        ),
    ],
)
def test_directory_worker_walk(expected):
    from multiprocess_ftp.workers import DirectoryWorker

    mock_connection = Mock(
        return_value=Mock(
            __enter__=Mock(
                return_value=Mock(walk=Mock(return_value=expected))
            ),
            __exit__=Mock(),
        )
    )
    mock_worker = DirectoryWorker(
        "foo_worker3", mock_connection, Mock(), Mock(), Mock()
    )
    mock_worker.subdirectory = "foo"
    mock_worker.source = {"foo": "bar"}

    actual = mock_worker.walk_remote_directory()

    assert expected == actual


@pytest.mark.parametrize(
    "expected",
    [
        ["bring", ["us"], ["a", "shrubbery"]],
        ("sour cream", ["yogurt", "cheese"], ["whey", "milk"]),
        ("quinoa", ["tofu"], ["rice", "vegetables"]),
        (
            "/app/test/data",
            [],
            [
                "/app/test/data/TNR2.md5",
                "/app/test/data/TNR2_202007.report.txt",
                "/app/test/data/TNR2_CA.txt.gpg",
            ],
        ),
    ],
)
def test_directory_worker_more(expected):
    from multiprocess_ftp.workers import DirectoryWorker

    mock_walk_queue = Mock(
        get=Mock(
            side_effect=[
                [{"subdirectory": "foo"}, "destination"],
                StopIteration,
            ]
        )
    )
    with patch(
        f"{SOURCE_PATH}.DirectoryWorker.walk_remote_directory",
        return_value=expected,
    ):
        mock_download_queue = Mock()
        mock_worker = DirectoryWorker(
            "foo_worker3",
            Mock(),
            mock_download_queue,
            mock_walk_queue,
            Mock(),
        )

        with pytest.raises(StopIteration):
            mock_worker.run()

        expected_root, expected_dirs, expected_files = expected

        calls = [
            call(
                (
                    {},
                    os.path.join(expected_root, directory),
                    "destination",
                )
            )
            for directory in expected_dirs
        ]
        mock_walk_queue.put.assert_has_calls(calls)

        calls = [
            call(
                (
                    {},
                    os.path.join(expected_root, file_name),
                    "destination",
                )
            )
            for file_name in expected_files
        ]
        mock_download_queue.put.assert_has_calls(calls)


@pytest.mark.parametrize(
    "st_size, expected_chunks",
    [
        (
            30000000,
            [
                ("spam", 1, (0, 10485760)),
                ("spam", 2, (10485760, 20971520)),
                ("spam", 3, (20971520, 30000000)),
            ],
        ),
        (10000000, [("spam", 1, (0, 10000000))]),
        (
            10,
            [
                ("spam", 1, (0, 10)),
            ],
        ),
    ],
)
def test_get_chunks(st_size, expected_chunks):
    from multiprocess_ftp.workers import TransferWorker

    worker = TransferWorker("peasant", Mock(), Mock(), Mock(), Mock(), 1)
    actual_chunks = worker.get_chunks("spam", st_size)

    assert expected_chunks == actual_chunks
