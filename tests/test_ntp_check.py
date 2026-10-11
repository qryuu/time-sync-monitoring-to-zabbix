import struct
import time
import sys
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))
from ntp.scripts.zabbix_ntp_check import query_ntp, NTP_DELTA

def test_query_ntp_success():
    # Build fake 48-byte NTP response
    # flags: LI=0, VN=4, Mode=4 (server) -> 0x24
    # stratum = 2, poll = 6, precision = -20
    header = bytearray(48)
    header[0] = 0x24
    header[1] = 2
    header[2] = 6
    header[3] = 236 # -20 in signed 8-bit

    # Timestamps
    now = time.time()
    t2_ntp = now + NTP_DELTA + 0.005 # Server received 5ms after client sent
    t3_ntp = t2_ntp + 0.001          # Server replied 1ms later

    struct.pack_into("!II", header, 32, int(t2_ntp), int((t2_ntp - int(t2_ntp)) * 2**32))
    struct.pack_into("!II", header, 40, int(t3_ntp), int((t3_ntp - int(t3_ntp)) * 2**32))

    mock_socket = MagicMock()
    mock_socket.recvfrom.return_value = (bytes(header), ("127.0.0.1", 123))

    with patch("socket.socket", return_value=mock_socket):
        result = query_ntp("127.0.0.1", 123, timeout=1.0)

    assert result["status"] == "ok"
    assert result["stratum"] == 2
    assert result["version"] == 4
    assert "offset_ms" in result
    assert "delay_ms" in result

def test_query_ntp_timeout():
    mock_socket = MagicMock()
    import socket
    mock_socket.recvfrom.side_effect = socket.timeout("Timed out")

    with patch("socket.socket", return_value=mock_socket):
        result = query_ntp("192.0.2.1", 123, timeout=0.1)

    assert result["status"] == "error"
    assert "timed out" in result["error"].lower()
