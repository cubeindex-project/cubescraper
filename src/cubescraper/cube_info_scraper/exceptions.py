from cubescraper.common.exceptions import ParserError


class InvalidURLError(ParserError):
    """Raised when the URL is invalid or has no hostname."""

    pass


class ParsingFailedError(ParserError):
    """Raised when the parser exists but fails to extract cube details."""

    pass
