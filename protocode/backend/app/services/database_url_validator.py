import ipaddress
import re
from urllib.parse import urlsplit


_DATABASE_SCHEMES = {
    "postgres",
    "postgresql",
    "mysql",
    "mariadb",
    "mongodb",
    "sqlite",
    "mssql",
    "sqlserver",
    "oracle",
    "redis",
}
_HOST_LABEL = re.compile(r"^[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$")


def validate_database_url(value: str) -> str:
    url = value.strip()
    if not url:
        raise ValueError("A database URL is required.")
    if any(character.isspace() for character in url):
        raise ValueError("Database URL must not contain unescaped whitespace.")

    try:
        parsed = urlsplit(url)
        scheme = parsed.scheme.lower()
        base_scheme = scheme.split("+", 1)[0]
        if base_scheme not in _DATABASE_SCHEMES:
            raise ValueError

        if base_scheme == "sqlite":
            if parsed.netloc or not parsed.path or parsed.path == "/":
                raise ValueError
            return url

        hostname = parsed.hostname
        if not hostname:
            raise ValueError
        if parsed.port is not None and not 1 <= parsed.port <= 65535:
            raise ValueError

        try:
            ipaddress.ip_address(hostname)
        except ValueError:
            ascii_hostname = hostname.encode("idna").decode("ascii").rstrip(".")
            labels = ascii_hostname.split(".")
            if not ascii_hostname or any(not _HOST_LABEL.fullmatch(label) for label in labels):
                raise ValueError
    except (UnicodeError, ValueError) as error:
        raise ValueError(
            "Enter a valid database URL with a supported database scheme and hostname."
        ) from error

    return url
