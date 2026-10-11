import re
import pytest

# Sample output of `chronyc -c tracking`
# Legacy 13-column format (Chrony 3.x / CentOS 7, RHEL 7, Ubuntu 18.04)
SAMPLE_CHRONY_CSV_LEGACY = "85F3EEA3,2,Sun Oct 11 05:22:15 2026,-0.000042123,-0.000035000,0.000051234,12.345,-0.001,0.052,0.008234567,0.001234567,64.2,Normal\n"

# Modern Chrony 4.x (14 columns including Reference Name/IP in column 2)
# Real output on Amazon Linux 2023 / Chrony 4.3:
SAMPLE_CHRONY_4X_CSV_NORMAL = (
    "A9FEA97B,169.254.169.123,4,Sun Oct 11 12:00:00 2026,"
    "-0.000004163,-0.000001554,0.000005164,-12.345,-0.001,0.052,"
    "0.000771621,0.000123456,16.3,Normal\n"
)
SAMPLE_CHRONY_4X_CSV_UNSYNC = (
    "00000000,,0,Sun Oct 11 05:00:00 2026,"
    "0.000000000,0.000000000,0.000000000,0.000,0.000,0.000,"
    "0.000000000,0.000000000,0.0,Not synchronized\n"
)

def parse_chrony_hybrid_js(raw_csv: str) -> dict:
    """
    Simulates Zabbix master item JavaScript preprocessing
    which automatically detects Chrony 3.x (13 columns) vs Chrony 4.x (14 columns).
    """
    parts = raw_csv.strip().split(',')
    is_v4 = len(parts) >= 14

    return {
        "ref_id": parts[0],
        "reference": parts[1] if is_v4 else parts[0],
        "stratum": int(parts[2] if is_v4 else parts[1]),
        "system_time_s": float(parts[4] if is_v4 else parts[3]),
        "system_time_ms": float(parts[4] if is_v4 else parts[3]) * 1000.0,
        "system_time_dir": "fast" if float(parts[4] if is_v4 else parts[3]) >= 0 else "slow",
        "last_offset_ms": float(parts[5] if is_v4 else parts[4]) * 1000.0,
        "rms_offset_ms": float(parts[6] if is_v4 else parts[5]) * 1000.0,
        "frequency_ppm": float(parts[7] if is_v4 else parts[6]),
        "root_delay_ms": float(parts[10] if is_v4 else parts[9]) * 1000.0,
        "update_interval_s": float(parts[12] if is_v4 else parts[11]),
        "leap_status": parts[13] if is_v4 else parts[12]
    }

def test_chrony_3x_legacy_csv():
    """Verify Chrony 3.x (13 columns) parses correctly without shifting columns."""
    metrics = parse_chrony_hybrid_js(SAMPLE_CHRONY_CSV_LEGACY)
    assert metrics["ref_id"] == "85F3EEA3"
    assert metrics["reference"] == "85F3EEA3"
    assert metrics["stratum"] == 2
    assert metrics["system_time_dir"] == "slow"
    assert abs(metrics["system_time_ms"] - (-0.042123)) < 1e-6
    assert abs(metrics["last_offset_ms"] - (-0.035)) < 1e-6
    assert abs(metrics["rms_offset_ms"] - 0.051234) < 1e-6
    assert abs(metrics["root_delay_ms"] - 8.234567) < 1e-6
    assert metrics["update_interval_s"] == 64.2
    assert metrics["leap_status"] == "Normal"

def test_chrony_4x_modern_csv():
    """Verify Chrony 4.x (14 columns) parses correctly with dedicated Reference IP/Name."""
    metrics = parse_chrony_hybrid_js(SAMPLE_CHRONY_4X_CSV_NORMAL)
    assert metrics["ref_id"] == "A9FEA97B"
    assert metrics["reference"] == "169.254.169.123"
    assert metrics["stratum"] == 4
    assert metrics["system_time_dir"] == "slow"
    assert abs(metrics["system_time_ms"] - (-0.004163)) < 1e-6
    assert abs(metrics["last_offset_ms"] - (-0.001554)) < 1e-6
    assert abs(metrics["rms_offset_ms"] - 0.005164) < 1e-6
    assert abs(metrics["root_delay_ms"] - 0.771621) < 1e-6
    assert metrics["update_interval_s"] == 16.3
    assert metrics["leap_status"] == "Normal"

def test_chrony_4x_unsync():
    metrics = parse_chrony_hybrid_js(SAMPLE_CHRONY_4X_CSV_UNSYNC)
    assert metrics["stratum"] == 0
    assert metrics["leap_status"] == "Not synchronized"
    assert metrics["last_offset_ms"] == 0.0

# Multi-unit LLD conversion simulation
def convert_unit_to_ms(val_str: str, unit_str: str) -> float:
    v = float(val_str)
    if unit_str == "ns":
        return v / 1000000.0
    elif unit_str == "us":
        return v / 1000.0
    elif unit_str == "ms":
        return v
    elif unit_str == "s":
        return v * 1000.0
    return v

SAMPLE_SOURCES_OUTPUT = """
210 Number of sources = 2
MS Name/IP address         Stratum Poll Reach LastRx Last sample               
===============================================================================
^* 169.254.169.123               3   4   377     5   -552ns[ -603ns] +/-  716us
^+ ntp.example.com               2   6   377    12  +1.234ms[+1.200ms] +/- 5.678ms
"""

def test_lld_multi_unit_parsing():
    delay_pattern = re.compile(r"(?m)^[\^\#\=][\*\+\-\?\~x]\s+169\.254\.169\.123\s+.*?\+/-\s*([+-]?[\d.]+)(ns|us|ms|s)")
    offset_pattern = re.compile(r"(?m)^[\^\#\=][\*\+\-\?\~x]\s+169\.254\.169\.123\s+.*?\s+([+-]?[\d.]+)(ns|us|ms|s)\[")

    m_delay = delay_pattern.search(SAMPLE_SOURCES_OUTPUT)
    assert m_delay is not None
    delay_ms = convert_unit_to_ms(m_delay.group(1), m_delay.group(2))
    assert abs(delay_ms - 0.716) < 1e-6  # 716us -> 0.716ms

    m_offset = offset_pattern.search(SAMPLE_SOURCES_OUTPUT)
    assert m_offset is not None
    offset_ms = convert_unit_to_ms(m_offset.group(1), m_offset.group(2))
    assert abs(offset_ms - (-0.000552)) < 1e-6  # -552ns -> -0.000552ms
