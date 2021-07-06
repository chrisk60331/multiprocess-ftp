from unittest.mock import patch

SOURCE_PATH = "multiprocess__ftp.sources"


def test_ftp_session():
    from multiprocess_ftp.sources import FTPSession

    with patch(f"{SOURCE_PATH}.FTPSession.connect"), patch(
        f"{SOURCE_PATH}.FTPSession.login"
    ):
        FTPSession("bring", "us", "a_shrubbery", 99)


def test_ftp_connection():
    from multiprocess_ftp.sources import FTPConnection

    with patch(f"{SOURCE_PATH}.ftplib"), patch(f"{SOURCE_PATH}.FTPSession"):
        with FTPConnection(spam="spam", eggs="eggs") as mock_ftp:
            mock_ftp.open("mock_file", "r")
