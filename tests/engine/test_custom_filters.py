import pytest

from foxops.engine.custom_filters import ip_add_integer


@pytest.mark.parametrize(
    "ip,n,expected",
    [
        ("192.168.0.0", -1, "192.167.255.255"),
        ("192.168.0.0", 0, "192.168.0.0"),
        ("192.168.0.0", 1, "192.168.0.1"),
        ("192.168.0.0", 256, "192.168.1.0"),
    ],
)
async def test_ip_add_integer(ip, n, expected):
    assert ip_add_integer(ip, n) == expected
