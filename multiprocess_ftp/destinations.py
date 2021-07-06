import logging
import re

import boto3


class Destination:
    """Generic download destination class."""


class S3Destination(Destination):
    """Saves files to s3."""

    PATH_SEPARATOR = "/"

    def __init__(self, bucket, prefix):
        """Initialize the destination."""
        self.bucket = bucket
        self.prefix = prefix

    def join_path(self, suffix):
        """Create a key from prefix and suffix."""
        return self.PATH_SEPARATOR.join(
            [
                re.sub(r"(^/)|(/$)", "", str(self.prefix)),
                re.sub(r"(^/)|(/$)", "", suffix),
            ]
        )

    def put(self, suffix: str, data: bytes):
        """Save the file to s3"""
        key = self.join_path(suffix)
        logging.info(
            "Putting file %s in %s as %s.",
            suffix,
            self.bucket,
            key,
        )
        boto3.client("s3").put_object(
            Bucket=self.bucket,
            Key=key,
            Body=data,
        )
        logging.info(
            "Finished putting file %s in %s as %s.",
            suffix,
            self.bucket,
            key,
        )
        return key
