import ftplib

import ftputil


class FTPSession(ftplib.FTP):
    """Act like ftplib.FTP constructor but connect to another port."""

    def __init__(self, host, user, passwd, port):
        """Initialize the session."""
        ftplib.FTP.__init__(self)
        self.connect(host, port)
        self.login(user, passwd)


class Connection:
    """Generic source connection."""


class FTPConnection(Connection):
    """FTP session as context manager."""

    def __init__(self, **kwargs):
        """Setup connection details."""
        self.kwargs = kwargs

    def __enter__(self):
        """Establish the connection."""
        self._connection = ftputil.FTPHost(**self.kwargs, session_factory=FTPSession)
        return self._connection

    def __exit__(self, *args):
        """Close the connection."""
        self._connection.close()
