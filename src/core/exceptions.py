class ProtocolError(Exception):
    """Raised when a RESP message is malformed."""


class NeedMoreData(ProtocolError):
    """Raised when the current socket buffer does not contain a full command yet."""
