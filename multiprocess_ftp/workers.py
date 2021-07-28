"""Classes of workers."""
import logging
import os
import queue
import threading
from multiprocessing import Process

from multiprocess_ftp import better_queue

CHUNK_SIZE_IN_BYTES = 1024 ** 2 * 10  # 10MB


class DirectoryWorker(Process):
    """A process worker that enumerates directories and files."""

    def __init__(
        self,
        name: str,
        source_connection_class,
        download_queue: better_queue.BetterQueue,
        walk_queue: better_queue.BetterQueue,
        result_queue: better_queue.BetterQueue,
    ):
        """Initialize the worker."""
        Process.__init__(self)
        self.name = str(name)
        self.download_queue = download_queue
        self.walk_queue = walk_queue
        self.result_queue = result_queue
        self.source_connection_class = source_connection_class

    def run(self):
        """Make the worker run."""
        while True:
            queue_item = self.walk_queue.get()
            if not queue_item:
                continue
            self.source, destination = queue_item
            self.subdirectory = self.source.pop("subdirectory")
            root, dirs, files = self.walk_remote_directory()
            for item in dirs:
                self.walk_queue.put(
                    (self.source, os.path.join(root, item), destination)
                )
            for item in files:
                if os.path.sep in item:
                    item = item.split(os.path.sep)[-1]
                self.download_queue.put(
                    (self.source, os.path.join(root, item), destination)
                )
            self.walk_queue.task_done()

    def walk_remote_directory(self):
        """Walk remote directory and generate directory and files names."""
        logging.info(
            "Worker: %s, Walking directory %s.",
            self.name,
            self.subdirectory,
        )
        with self.source_connection_class(**self.source) as host:
            root, dirs, files = host.walk(self.subdirectory)
            logging.info(
                "Worker: %s, Finished walking directory %s.",
                self.name,
                self.subdirectory,
            )
            return root, dirs, files


class TransferWorker(Process):
    """A Process worker that downloads files."""

    def __init__(
        self,
        name: str,
        source_connection_class,
        download_queue: better_queue.BetterQueue,
        walk_queue: better_queue.BetterQueue,
        result_queue: better_queue.BetterQueue,
        max_workers: int = 10,
    ):
        """Initialize the worker."""
        Process.__init__(self)
        self.name = str(name)
        self.download_queue = download_queue
        self.walk_queue = walk_queue
        self.result_queue = result_queue
        self.source_connection_class = source_connection_class
        self.max_workers = max_workers

    def run(self):
        """Download a file."""
        while True:
            queue_item = self.download_queue.get()
            if not queue_item:
                continue
            self.source, remote_path, destination = queue_item
            logging.info(
                "Worker: %s, Extracting file %s.", self.name, remote_path
            )
            logging.info(
                "Worker: %s, Starting chunk queue",
                self.name,
            )
            self.chunk_queue = queue.Queue()
            self.chunk_result_queue = queue.Queue()
            with self.source_connection_class(**self.source) as host:
                st_size = host.stat(remote_path).st_size
            destination.suffix = remote_path
            chunks = self.get_chunks(remote_path, st_size)
            for chunk in chunks:
                self.chunk_queue.put((chunk, destination))
            logging.info(
                "Worker: %s, found chunks: %d.",
                self.name,
                len(chunks),
            )
            with destination as upload:
                for num in range(self.max_workers):
                    logging.info(
                        "Worker: %s, starting chunk worker %d.",
                        self.name,
                        num,
                    )
                    ChunkWorker(
                        self.source_connection_class,
                        self.chunk_queue,
                        self.chunk_result_queue,
                        self.source,
                        upload,
                        remote_path,
                    ).start()
                logging.info(
                    "Worker: %s, Joining chunk queue.",
                    self.name,
                )
                self.chunk_queue.join()
                while not self.chunk_result_queue.empty():
                    etag, part = self.chunk_result_queue.get()
                    destination.finished_parts.append(
                        {"PartNumber": part, "ETag": etag}
                    )
                    self.chunk_result_queue.task_done()
                logging.info(
                    "Worker: %s, Finished uploading parts %s.",
                    self.name,
                    destination.finished_parts,
                )
            logging.info(
                "Worker: %s, Finished extracting file %s.",
                self.name,
                remote_path,
            )
            self.result_queue.put((destination.key, st_size))
            self.download_queue.task_done()

    @staticmethod
    def get_chunks(file_name, st_size):
        """Determine chunks in a file."""
        chunks = []
        part = 1
        chunk_size = (
            st_size if (CHUNK_SIZE_IN_BYTES > st_size) else CHUNK_SIZE_IN_BYTES
        )
        for i in range(0, st_size + 1, chunk_size):
            if i + chunk_size > st_size:
                chunk_size = st_size - i
            chunks.append((file_name, part, (i, i + chunk_size)))
            if i + chunk_size == st_size:
                break
            part += 1
        return chunks


class ChunkWorker(threading.Thread):
    """Transfer file chunks."""

    def __init__(
        self,
        source_connection_class,
        chunk_queue: queue.Queue,
        result_queue: queue.Queue,
        creds,
        destination,
        remote_path,
    ):
        """Initialize the worker."""
        super().__init__()
        self.source_connection_class = source_connection_class
        self.chunk_queue = chunk_queue
        self.result_queue = result_queue
        self.creds = creds
        self.destination = destination
        self.remote_path = remote_path

    def run(self):
        """Make the worker run."""
        while True:
            queue_item = self.chunk_queue.get()
            if not queue_item:
                continue
            (remote_file, part, (start, end)), destination = queue_item
            with self.source_connection_class(**self.creds) as host:
                with host.open(remote_file, "rb") as file_object:
                    file_object.seek(start, 0)
                    result = destination.put(
                        part, file_object.read(end - start)
                    )
                    self.chunk_queue.task_done()
                    self.result_queue.put((result["ETag"], part))


class WorkerNumber:
    """A counter to keep track of how many workers are spun up."""

    def __init__(self, start: int = -1):
        """Initialize the counter."""
        self.counter = start

    def __next__(self):
        """Get the next value."""
        self.counter += 1
        return self.counter
