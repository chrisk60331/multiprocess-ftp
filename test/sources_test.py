"""Test suite for source classes."""
import base64
import tempfile
from unittest.mock import Mock, patch

SOURCE_PATH = "multiprocess_ftp.sources"


def test_ftp_session():
    from multiprocess_ftp.sources import FTPSession

    with patch(f"{SOURCE_PATH}.FTPSession.connect"), patch(
        f"{SOURCE_PATH}.FTPSession.login"
    ):
        FTPSession("bring", "us", "a_shrubbery", 99)


def test_ftp_connection():
    from multiprocess_ftp.sources import FTPConnection

    with patch(f"{SOURCE_PATH}.ftputil"), patch(
        f"{SOURCE_PATH}.FTPSession"
    ) as mock_session:
        mock_session.return_value = Mock(encoding="UTF-8")
        with FTPConnection(spam="spam", eggs="eggs") as mock_ftp:
            mock_ftp.keep_alive()


def test_sftp_connection():
    from multiprocess_ftp.sources import SFTPConnection

    with patch(f"{SOURCE_PATH}.SFTPSession"):
        with SFTPConnection(host="spam") as mock_sftp:
            mock_sftp.keep_alive()


def test_base_connection():
    from multiprocess_ftp.sources import Connection

    with tempfile.NamedTemporaryFile() as test_file:
        with Connection(test_file.name) as mock_conn:
            mock_conn.read()


def test_sftp_session():
    from multiprocess_ftp.sources import SFTPSession

    with patch(f"{SOURCE_PATH}.pysftp.Connection"), patch(
        f"{SOURCE_PATH}.paramiko.pkey.PKey._check_type_and_load_cert"
    ), patch(f"{SOURCE_PATH}.paramiko.Transport"), patch(
        "cryptography.hazmat.primitives.asymmetric.rsa._check_public_key_components"
    ), patch(
        f"{SOURCE_PATH}.pysftp.CnOpts.get_hostkey"
    ), patch(
        f"{SOURCE_PATH}.paramiko.SFTPClient", autospec=True
    ):
        with SFTPSession(
            host="spam",
            host_name="eggs",
            typ="ham",
            pubkey=base64.b64encode(b"shrubbery"),
        ) as mock_sftp:
            mock_sftp.walk("foo")
