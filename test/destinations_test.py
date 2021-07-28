"""Test suite for destinations classes."""
from unittest.mock import Mock, patch

import pytest

SOURCE_PATH = "multiprocess_ftp.destinations"


@pytest.mark.parametrize(
    "expected, bucket, key, suffix",
    [
        ("spam/eggs", "eggs", "spam", "eggs"),
        (
            "blessed/are/the/chesemakers",
            "eggs",
            "blessed/are/the/",
            "chesemakers",
        ),
        ("bring/us/a/shrubbery", "spam", "bring/us/a/", "/shrubbery/"),
    ],
)
def test_s3_destination_join_path(expected, bucket, key, suffix):
    from multiprocess_ftp.destinations import S3Destination

    actual = S3Destination(bucket, key, suffix)

    assert expected == actual.key


def test_s3_destination_put():
    from multiprocess_ftp.destinations import S3Destination

    mock_s3 = Mock(
        create_multipart_upload=Mock(
            return_value={
                "UploadId": "123",
                "Bucket": "cheese",
                "Key": "eggs/spam",
            }
        )
    )
    with patch(f"{SOURCE_PATH}.boto3.client", return_value=mock_s3):
        with S3Destination("cheese", "eggs", "spam") as dest:
            dest.put(1, b"body")

    mock_s3.create_multipart_upload.assert_called_once_with(
        Bucket="cheese", Key="eggs/spam"
    )


def test_s3_destination_raises_destination_exception():
    from multiprocess_ftp.destinations import (
        DestinationException,
        S3Destination,
    )

    with patch(f"{SOURCE_PATH}.boto3"):

        with pytest.raises(DestinationException):

            with S3Destination("cheese", "eggs", "spam") as dest:
                dest.put(part="l", body=None)
