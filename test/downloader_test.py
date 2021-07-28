"""Test suite for download orchestrator classes."""
from unittest.mock import Mock, patch

from multiprocess_ftp.sources import FTPConnection

SOURCE_PATH = "multiprocess_ftp.downloader"


def test_multiprocess_downloader_puts_expected_in_results_queue():
    from multiprocess_ftp.downloader import MultiProcessDownloader

    expected = "blessed are the cheese makers"
    mock_worker = Mock(__name__="Bryan")
    with patch(f"{SOURCE_PATH}.BaseManager"), patch(
        "multiprocess_ftp.workers.ChunkWorker"
    ):
        mpd = MultiProcessDownloader(FTPConnection, [mock_worker])
        mpd.WORKER_WAIT_INTERVAL = 0.2
    mpd.result_queue = Mock(
        empty=Mock(side_effect=[0, 1]),
        get=Mock(return_value=expected),
    )

    actual = mpd.wait_workers()
    mpd.result_queue.empty.assert_called_with()
    mpd.result_queue.get.assert_called_once_with()
    assert [expected] == actual


def test_multiprocess_downloader_waits_queue():
    from multiprocess_ftp.downloader import MultiProcessDownloader

    mock_worker = Mock(__name__="Bryan")
    mpd = MultiProcessDownloader(FTPConnection, [mock_worker])

    mpd.walk_queue = Mock(all_tasks_done=Mock(side_effect=[False, True]))
    mpd.wait_workers()


def test_queue_workers():
    from multiprocess_ftp.downloader import MultiProcessDownloader

    mpd = MultiProcessDownloader(
        Mock(), [Mock(__name__="repressed_peasant")], max_workers=1
    )
    mpd.queue_workers()
    with patch("multiprocessing.reduction.ForkingPickler.dumps"), patch(
        "multiprocessing.connection.Connection"
    ), patch("multiprocessing.connection.answer_challenge"), patch(
        "multiprocessing.connection.deliver_challenge"
    ), patch(
        "multiprocessing.managers.dispatch"
    ), patch(
        "multiprocessing.managers.BaseProxy._callmethod"
    ):
        mpd.load_queue(Mock(), Mock())
