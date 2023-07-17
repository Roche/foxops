import pytest

from foxops.engine.custom_filters import base64encode, ip_add_integer


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


@pytest.mark.parametrize(
    "value,expected",
    [
        ("", ""),
        ("test:user\n", "dGVzdDp1c2VyCg=="),
        (b"test:user\n", "dGVzdDp1c2VyCg=="),
        (b"\x00", "AA=="),
    ],
)
def test_base64_encode(value, expected):
    assert base64encode(value) == expected
