"""The exceptions used by AIOSkybell."""


class SkybellException(Exception):
    """Class to throw general skybell exception."""


class SkybellAuthenticationException(SkybellException):
    """Class to throw authentication exception."""
