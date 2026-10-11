#!/usr/bin/env python3
"""
Zabbix External Check Script: zabbix_ntp_check.py
Queries a remote NTP/SNTP server directly via UDP port 123
and returns time synchronization metrics in a single structured JSON.
Dependencies: Python standard library only (socket, struct, time, sys, json)
"""
import sys
import socket
import struct
import time
import json

sys.stdout.reconfigure(encoding='utf-8')

# NTP timestamp epoch starts at 1900-01-01 00:00:00 UTC
NTP_DELTA = 2208988800

def query_ntp(host: str, port: int = 123, timeout: float = 3.0) -> dict:
    # NTP request packet: LI=0, VN=4, Mode=3 (client)
    # First byte: 00 100 011 -> 0x23 (35 in decimal)
    packet = bytearray(48)
    packet[0] = 0x23

    # Client transmit timestamp (t1)
    t1 = time.time()
    t1_ntp = t1 + NTP_DELTA
    t1_sec = int(t1_ntp)
    t1_frac = int((t1_ntp - t1_sec) * (2 ** 32))
    struct.pack_into("!II", packet, 40, t1_sec, t1_frac)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)

    try:
        sock.sendto(packet, (host, port))
        data, _ = sock.recvfrom(48)
        # Client receive timestamp (t4)
        t4 = time.time()
    except socket.timeout:
        return {"status": "error", "error": f"Connection to {host}:{port} timed out after {timeout}s"}
    except Exception as e:
        return {"status": "error", "error": str(e)}
    finally:
        sock.close()

    if len(data) < 48:
        return {"status": "error", "error": f"Invalid NTP response length: {len(data)} bytes"}

    # Unpack header
    flags = data[0]
    li = (flags >> 6) & 0x03
    vn = (flags >> 3) & 0x07
    mode = flags & 0x07
    stratum = data[1]
    poll = data[2]
    precision = data[3]
    if precision > 127:
        precision = precision - 256

    # Timestamps
    # Server receive timestamp (t2)
    t2_sec, t2_frac = struct.unpack("!II", data[32:40])
    t2 = (t2_sec - NTP_DELTA) + (t2_frac / (2 ** 32))

    # Server transmit timestamp (t3)
    t3_sec, t3_frac = struct.unpack("!II", data[40:48])
    t3 = (t3_sec - NTP_DELTA) + (t3_frac / (2 ** 32))

    # Round trip delay: (t4 - t1) - (t3 - t2)
    delay = (t4 - t1) - (t3 - t2)
    # Clock offset: ((t2 - t1) + (t3 - t4)) / 2
    offset = ((t2 - t1) + (t3 - t4)) / 2.0

    return {
        "status": "ok",
        "server": host,
        "stratum": stratum,
        "leap_indicator": li,
        "version": vn,
        "poll_interval": 2 ** poll if poll > 0 else 0,
        "precision": precision,
        "offset_ms": round(offset * 1000.0, 4),
        "delay_ms": round(max(0.0, delay) * 1000.0, 4),
    }

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "error": "Usage: zabbix_ntp_check.py <target_host> [port] [timeout]"}, ensure_ascii=False))
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 123
    timeout = float(sys.argv[3]) if len(sys.argv) > 3 else 3.0

    result = query_ntp(host, port, timeout)
    print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    main()
