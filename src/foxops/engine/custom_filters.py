import base64
import ipaddress

from foxops.logger import get_logger

#: Holds the module logger
logger = get_logger(__name__)


def ip_add_integer(ip: str, n: int = 1):
    """Add the integer n to the given IP address"""
    next_ip = ipaddress.ip_address(ip) + n
    return str(next_ip)


def base64encode(data: str | bytes) -> str:
    """Encode the given data as base64"""

    if isinstance(data, str):
        data = data.encode()

    return base64.b64encode(data).decode()
