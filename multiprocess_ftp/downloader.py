"""Multiprocessing orchestrators for downloading files from FTP."""
import logging
import time
from multiprocessing.managers import BaseManager
from typing import Any

from multiprocess_ftp.better_queue import BetterQueue
from multiprocess_ftp.proxy import BetterProxy
from multiprocess_ftp.workers import WorkerNumber


class MultiProcessDownloader:
    """Orchestrator for parallel downloads."""

    WORKER_NUMBER = WorkerNumber()
    WORKER_WAIT_INTERVAL = 10

    def __init__(
        self,
        source_connection_class: Any,
        worker_classes: Any,
        max_workers: int = 10,
    ):
        """Initialize the orchestrator."""
        self.worker_classes = worker_classes
        self.max_workers = max_workers
        self.source_connection_class = source_connection_class
        BaseManager.register("BetterQueue", BetterQueue, proxytype=BetterProxy)
        manager = BaseManager()
        manager.start()  # pylint: disable=consider-using-with
        self.download_queue = manager.BetterQueue()  # type: ignore
        self.walk_queue = manager.BetterQueue()  # type: ignore
        self.result_queue = manager.BetterQueue()  # type: ignore

    def queue_workers(self):
        """Initialize and start workers."""
        for worker_class in self.worker_classes:
            for _ in range(round(self.max_workers / len(self.worker_classes))):
                worker_num = next(self.WORKER_NUMBER)  # type: ignore
                logging.info(
                    "Starting %s%d.", worker_class.__name__, worker_num
                )
                worker_class(
                    worker_class.__name__ + str(worker_num),
                    self.source_connection_class,
                    self.download_queue,
                    self.walk_queue,
                    self.result_queue,
                ).start()

    def load_queue(self, source, destination):
        """Put items in the queue for directory worker to process."""
        self.walk_queue.put((source, destination))

    def wait_workers(self):
        """Wait for queues to be processed."""
        result_paths = []
        self.walk_queue.join()
        self.download_queue.join()
        time.sleep(self.WORKER_WAIT_INTERVAL)
        while not self.result_queue.empty():
            logging.info("Appending results.")
            result_paths.append(self.result_queue.get())
            self.result_queue.task_done()
        logging.info("Returning results.")
        return result_paths
