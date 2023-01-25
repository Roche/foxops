import ipaddress

from foxops.logger import get_logger

#: Holds the module logger
logger = get_logger(__name__)


def ip_add_increase(ip: str, inc: int = 1):
    """Get next consecutive IP"""
    next_ip = ipaddress.ip_address(ip) + inc
    return str(next_ip)
