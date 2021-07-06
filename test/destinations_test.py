from unittest.mock import patch

SOURCE_PATH = "multiprocess_ftp.destinations"


def test_s3_destination_join_path():
    from multiprocess_ftp.destinations import S3Destination

    expected = "spam/eggs"
    dest = S3Destination("eggs", "spam")

    actual = dest.join_path("eggs")

    assert expected == actual


def test_s3_destination_put():
    from multiprocess_ftp.destinations import S3Destination

    expected = "spam/eggs"
    dest = S3Destination("eggs", "spam")
    with patch(f"{SOURCE_PATH}.boto3.client"):
        actual = dest.put("eggs", b"spam")

    assert expected == actual
