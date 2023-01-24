import ipaddress

from foxops.logger import get_logger

#: Holds the module logger
logger = get_logger(__name__)


def first_ip_address_is_greater_than(first_ip, second_ip):
    """Checks with of the two IP addresses is greater

    Returns True if first one is greater. Otherwise False.
    """
    return ipaddress.ip_address(first_ip) > ipaddress.ip_address(second_ip)


def increase_ip_add(ip: str, inc: int = 1):
    """Get next consecutive IP"""
    next_ip = ipaddress.ip_address(ip) + inc
    return str(next_ip)
