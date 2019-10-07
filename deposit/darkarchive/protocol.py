from deposit.protocol import RepositoryProtocol


class DarkArchiveProtocol(RepositoryProtocol):
    """
    A protocol that does does directly sends data to a repository, but to an intermediata database
    """

    def __str__(self):
        """
        Return human readable class name
        """
        return "Dark Archive Protocol"
