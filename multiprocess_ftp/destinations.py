"""Definitions for different locations we can save files to."""
import logging
import re
from typing import Dict, List

import boto3


class Destination:
    """Generic download destination class."""


class DestinationException(Exception):
    """Raised when loading to destination is not successful."""


class S3Destination(Destination):
    """Saves files to s3."""

    PATH_SEPARATOR = "/"

    def __init__(self, bucket, prefix, suffix: str = "", **kwargs):
        """Initialize the destination."""
        self.bucket = bucket
        self.prefix = prefix
        self.suffix = suffix
        self.finished_parts: List[Dict[str, str]] = []
        self.key = self.join_path(self.suffix)
        self.kwargs = kwargs

    def __enter__(self):
        """Save the file to s3."""
        self.key = self.join_path(self.suffix)
        self.s3_client = boto3.client("s3", **self.kwargs)
        logging.info(
            "Putting file %s in %s as %s.",
            self.suffix,
            self.bucket,
            self.key,
        )
        self.upload = self.s3_client.create_multipart_upload(
            Bucket=self.bucket, Key=self.key
        )
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Handle context errors or complete the upload."""
        if exc_type is not None:
            self.s3_client.abort_multipart_upload(
                Bucket=self.upload["Bucket"],
                Key=self.upload["Key"],
                UploadId=self.upload["UploadId"],
            )
            raise DestinationException(exc_type, exc_value, traceback)
        self.s3_client.complete_multipart_upload(
            Bucket=self.upload["Bucket"],
            Key=self.upload["Key"],
            UploadId=self.upload["UploadId"],
            MultipartUpload={
                "Parts": sorted(
                    self.finished_parts, key=lambda i: i["PartNumber"]
                )
            },
        )
        logging.info(
            "Finished putting file %s in %s as %s.",
            self.suffix,
            self.bucket,
            self.key,
        )
        return self.key

    def put(self, part, body):
        """Save the part upload to the bucket."""
        if not part or not body:
            raise DestinationException(
                "Values for part and body are required."
            )
        return self.s3_client.upload_part(
            Bucket=self.upload["Bucket"],
            Key=self.upload["Key"],
            UploadId=self.upload["UploadId"],
            PartNumber=part,
            Body=body,
        )

    def join_path(self, suffix):
        """Create a key from prefix and suffix."""
        return self.PATH_SEPARATOR.join(
            [
                re.sub(r"(^/)|(/$)", "", str(self.prefix)),
                re.sub(r"(^/)|(/$)", "", suffix),
            ]
        )
