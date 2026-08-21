class ParserError(Exception):
    """Base exception for parser and scraper operations."""

    pass


class UnsupportedVendorError(ParserError):
    """Raised when the vendor is not supported."""

    pass
