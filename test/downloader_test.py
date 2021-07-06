from unittest.mock import Mock, patch

import pytest

SOURCE_PATH = "multiprocess__ftp.downloader"


def test_directory_worker_run():
    from multiprocess_ftp.downloader import FTPDownloadDirectoryWorker

    mock_walk_queue = Mock(
        get=Mock(side_effect=[[{"subdirectory": "foo"}, Mock()], []])
    )
    mock_result_queue = Mock()
    mock_download_queue = Mock()
    mock_walk_results = Mock(return_value=[("foo", "bar", "baz")])
    mock_worker = FTPDownloadDirectoryWorker(
        "eggs_worker3", mock_download_queue, mock_walk_queue, mock_result_queue
    )
    with patch(f"{SOURCE_PATH}.FTPConnection"), patch(
        f"{SOURCE_PATH}.FTPDownloadDirectoryWorker.walk_remote_directory",
        mock_walk_results,
    ), pytest.raises(StopIteration):
        mock_worker.run()


def test_directory_worker_walk():
    from multiprocess_ftp.downloader import FTPDownloadDirectoryWorker

    expected = [("foo", "bar", "baz")]

    mock_worker = FTPDownloadDirectoryWorker("foo_worker3", Mock(), Mock(), Mock())
    mock_worker.subdirectory = "foo"
    mock_worker.source = {"foo": "bar"}
    with patch(
        f"{SOURCE_PATH}.FTPConnection",
    ) as mock_connection:
        mock_connection.return_value.__enter__.return_value = Mock(
            walk=Mock(return_value=expected)
        )
        actual = mock_worker.walk_remote_directory()

    assert expected == actual


def test_download_worker_run():
    from multiprocess_ftp.downloader import FTPDownloadTransferWorker

    with patch(f"{SOURCE_PATH}.FTPConnection") as mock_connection, patch(
        f"{SOURCE_PATH}.gzip.decompress"
    ):
        mock_download_queue = Mock(
            get=Mock(side_effect=[[{"subdirectory": "foo.gz"}, Mock()]])
        )
        mock_result_queue = Mock()
        mock_walk_queue = Mock()
        with pytest.raises(StopIteration):
            FTPDownloadTransferWorker(
                "spam_worker1",
                mock_download_queue,
                mock_walk_queue,
                mock_result_queue,
            ).run()


@pytest.mark.parametrize("start, expected", [(10, 11), (100, 101), (-500, -499)])
def test_worker_number(start, expected):
    from multiprocess_ftp.downloader import WorkerNumber

    worker_number = WorkerNumber(start)

    assert expected == next(worker_number)


def test_multiprocess_downloader_puts_expected_in_results_queue():
    from multiprocess_ftp.downloader import MultiProcessDownloader

    expected = "blessed are the cheese makers"
    mock_worker = Mock(__name__="Bryan")
    with patch(f"{SOURCE_PATH}.BaseManager"), patch(f"{SOURCE_PATH}.queue"):
        mpd = MultiProcessDownloader([mock_worker])
    mpd.result_queue = Mock(
        qsize=Mock(return_value=1),
        get=Mock(return_value=expected),
    )

    mpd.queue_workers()
    mpd.load_queue("eggs", "spam")
    actual = mpd.wait_workers()

    assert [expected] == actual
