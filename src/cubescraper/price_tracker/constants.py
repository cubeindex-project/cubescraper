import httpx

SCS_DEFAULT_CURRENCY = "USD"
ATOUTCUBES_DEFAULT_CURRENCY = "EUR"

JSON_LD_AVAILABLE_KEYWORDS = [
    "schema.org/InStock",
    "schema.org/MadeToOrder",
    "schema.org/OnlineOnly",
    "schema.org/PreOrder",
    "schema.org/PreSale",
]
JSON_LD_UNAVAILABLE_KEYWORDS = [
    "schema.org/SoldOut",
    "schema.org/OutOfStock",
    "schema.org/Discontinued",
    "schema.org/Reserved",
    "schema.org/LimitedAvailability",
    "schema.org/InStoreOnly",
    "schema.org/BackOrder",
]

DEAD_LINK_STATUS_CODES = {301, 302, 404, 410}
DEAD_LINK_EXCEPTIONS = (
    httpx.HTTPStatusError,  # Server responded with a fatal HTTP status
    httpx.ConnectError,  # Domain doesn't exist or connection refused
    httpx.ConnectTimeout,  # Server is down or completely unresponsive
    httpx.TooManyRedirects,  # Circular or infinite redirect loop
    httpx.UnsupportedProtocol,  # URL has a broken schema structure
    httpx.RemoteProtocolError,  # Server sent broken, corrupted HTTP packets
    httpx.ReadTimeout,  # Server accepted connection but then froze
    httpx.ReadError,  # Server dropped connection mid-transmission
)
