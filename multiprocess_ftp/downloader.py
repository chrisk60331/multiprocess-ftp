import gzip
import logging
import os
import queue
import time
from multiprocessing import Process
from multiprocessing.managers import BaseManager
from typing import Any

from multiprocess_ftp.proxy import BetterProxy
from multiprocess_ftp.sources import FTPConnection


class FTPDownloadDirectoryWorker(Process):
    """A process worker that enumerates directories and files."""

    def __init__(
        self,
        name: str,
        download_queue: queue,
        walk_queue: queue,
        result_queue: queue,
    ):
        """Initialize the worker."""
        Process.__init__(self)
        self.name = str(name)
        self.download_queue = download_queue
        self.walk_queue = walk_queue
        self.result_queue = result_queue

    def run(self):
        """Make the worker run."""
        while True:
            queue_item = self.walk_queue.get()
            if not queue_item:
                continue
            self.source, destination = queue_item
            self.subdirectory = self.source.pop("subdirectory")
            for root, dirs, files in self.walk_remote_directory():
                for item in dirs:
                    self.source["subdirectory"] = os.path.join(root, item)
                    self.walk_queue.put((self.source, destination))
                for file_name in files:
                    self.source["subdirectory"] = os.path.join(root, file_name)
                    self.download_queue.put((self.source, destination))
            self.walk_queue.task_done()

    def walk_remote_directory(self):
        """Walk remote directory and generate directory and files names."""
        logging.info("Worker: %s, Walking directory %s.", self.name, self.subdirectory)
        with FTPConnection(**self.source) as host:
            response = [
                (root, dirs, files)
                for root, dirs, files in host.walk(self.subdirectory, followlinks=True)
            ]
            logging.info(
                "Worker: %s, Finished walking directory %s.",
                self.name,
                self.subdirectory,
            )
            return response


class FTPDownloadTransferWorker(Process):
    """A Process worker that downloads files."""

    def __init__(
        self,
        name: str,
        download_queue: queue,
        walk_queue: queue,
        result_queue: queue,
    ):
        """Initialize the worker."""
        Process.__init__(self)
        self.name = str(name)
        self.download_queue = download_queue
        self.walk_queue = walk_queue
        self.result_queue = result_queue

    def run(self):
        """Download a file."""
        while True:
            queue_item = self.download_queue.get()
            if not queue_item:
                continue
            self.source, destination = queue_item
            remote_path = self.source.pop("subdirectory")
            logging.info("Worker: %s, Extracting file %s.", self.name, remote_path)
            with FTPConnection(**self.source) as host:
                with host.open(remote_path, "rb") as fp:
                    data = fp.read()
            if remote_path.endswith(".gz"):
                data = gzip.decompress(data)
            destination = destination.put(remote_path, data)
            logging.info(
                "Worker: %s, Finished extracting file %s.", self.name, remote_path
            )
            self.result_queue.put(destination)
            self.download_queue.task_done()


class WorkerNumber:
    def __init__(self, start: int = -1):
        self.counter = start

    def __next__(self):
        self.counter += 1
        return self.counter


class MultiProcessDownloader:
    """Orchestrator for parallel downloads."""

    MAX_WORKERS = 10
    WORKER_NUMBER = WorkerNumber()

    def __init__(self, workers: Any):
        """Initialize the orchestrator."""
        self.workers = workers
        BaseManager.register("BetterQueue", queue.BetterQueue, proxytype=BetterProxy)
        manager = BaseManager()
        manager.start()
        self.download_queue = manager.BetterQueue()
        self.walk_queue = manager.BetterQueue()
        self.result_queue = manager.BetterQueue()

    def queue_workers(self):
        """Create and start workers."""
        for worker_class in self.workers:
            for _ in range(round(self.MAX_WORKERS / 2)):
                worker_num = next(self.WORKER_NUMBER)
                logging.info("Starting %s%d.", worker_class.__name__, worker_num)
                worker_class(
                    worker_class.__name__ + str(worker_num),
                    self.download_queue,
                    self.walk_queue,
                    self.result_queue,
                ).start()

    def load_queue(self, source, destination):
        """Put items in the queue for directory worker to process."""
        self.walk_queue.put((source, destination))

    def wait_workers(self):
        """Wait for queues to be processed."""
        while (
            not self.walk_queue.all_tasks_done or not self.download_queue.all_tasks_done
        ):
            time.sleep(2)
        self.walk_queue.join()
        self.download_queue.join()
        result_paths = []
        for _ in range(self.result_queue.qsize()):
            result_paths.append(self.result_queue.get())
            self.result_queue.task_done()
        self.result_queue.join()
        return result_paths
