"""Sources to load data from."""
import ftplib  # nosec
from base64 import b64decode

import ftputil  # nosec
import paramiko
import pysftp


class FTPSession(ftplib.FTP):
    """Act like ftplib.FTP constructor but connect to another port."""

    def __init__(self, host, user, passwd, port):
        """Initialize the session."""
        ftplib.FTP.__init__(self)  # nosec
        self.connect(host, port)
        self.login(user, passwd)


class Connection:
    """Generic source connection."""

    def __init__(self, *args, **kwargs):
        """Setup connection details."""
        self.args = args
        self.kwargs = kwargs
        self._connection = None

    def __enter__(self):
        """Establish the connection."""
        self._connection = open(*self.args)
        return self._connection

    def __exit__(self, *args):
        """Close the connection."""
        self._connection.close()


class FTPConnection(Connection):
    """FTP session as context manager."""

    def __enter__(self):
        """Establish the connection."""
        self._connection = ftputil.FTPHost(
            **self.kwargs, session_factory=FTPSession
        )
        return self._connection


class SFTPConnection(Connection):
    """SFTP session as context manager."""

    def __enter__(self):
        """Initialize the session."""
        self._connection = SFTPSession(**self.kwargs)
        return self._connection


class SFTPSession(pysftp.Connection):
    """Extension of pysftp.Connection that we can use as child connection class."""

    def __init__(self, **kwargs):
        """Initialize the session."""
        if kwargs.get("host_name"):
            host, typ = kwargs.pop("host_name"), kwargs.pop("typ")
            pubkey = kwargs.pop("pubkey")
            cnopts = pysftp.CnOpts()
            cnopts.hostkeys.add(
                host, typ, paramiko.RSAKey(data=b64decode(pubkey))
            )
            kwargs["cnopts"] = cnopts
        super().__init__(**kwargs)

    def walk(self, directory):
        """Recurse a directory."""
        files = []
        dirs = []
        un_name = []

        self.walktree(
            directory,
            files.append,
            dirs.append,
            un_name.append,
        )

        return directory, dirs, files
