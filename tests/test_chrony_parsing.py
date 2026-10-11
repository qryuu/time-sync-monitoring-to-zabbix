import csv
import io
import re
import pytest

# Sample output of `chronyc -c tracking`
# Legacy 13-column format
SAMPLE_CHRONY_CSV_LEGACY = "85F3EEA3,2,Sun Oct 11 05:22:15 2026,-0.000042123,-0.000035000,0.000051234,12.345,-0.001,0.052,0.008234567,0.001234567,64.2,Normal\n"

# Modern Chrony 4.x (14 columns including Reference Name/IP in column 2)
# Real output on Amazon Linux 2023 / Chrony 4.3:
# Col 1: Ref ID (A9FEA97B)
# Col 2: Ref IP/Name (169.254.169.123)
# Col 3: Stratum (4)
# Col 4: Ref time UTC (Sun Oct 11 12:00:00 2026)
# Col 5: System time (s) (-0.000004163)
# Col 6: Last offset (s) (-0.000001554)
# Col 7: RMS offset (s) (0.000005164)
# Col 8: Frequency (ppm) (-12.345)
# Col 9: Residual freq (ppm) (-0.001)
# Col 10: Skew (ppm) (0.052)
# Col 11: Root delay (s) (0.000771621)
# Col 12: Root disp (s) (0.000123456)
# Col 13: Update interval (s) (16.3)
# Col 14: Leap status (Normal)
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

# Zabbix CSV_TO_JSON(0) simulation:
# Produces a list containing an object whose keys are 1-based string indices: [{"1": ..., "2": ..., ...}]
def zabbix_csv_to_json(csv_str: str):
    reader = csv.reader(io.StringIO(csv_str.strip()))
    row = next(reader)
    return [{str(i + 1): val for i, val in enumerate(row)}]

def parse_chrony_4x_zabbix(csv_str: str):
    json_obj = zabbix_csv_to_json(csv_str)[0]
    return {
        "ref_id": json_obj["1"],
        "reference": json_obj["2"],
        "stratum": int(json_obj["3"]),
        "system_time_dir": "fast" if float(json_obj["5"]) >= 0 else "slow",
        "system_time_ms": float(json_obj["5"]) * 1000.0,
        "last_offset_ms": float(json_obj["6"]) * 1000.0,
        "rms_offset_ms": float(json_obj["7"]) * 1000.0,
        "root_delay_ms": float(json_obj["11"]) * 1000.0,
        "update_interval": float(json_obj["13"]),
        "leap_status": json_obj["14"],
    }

def test_chrony_4x_csv_normal():
    metrics = parse_chrony_4x_zabbix(SAMPLE_CHRONY_4X_CSV_NORMAL)
    assert metrics["ref_id"] == "A9FEA97B"
    assert metrics["reference"] == "169.254.169.123"
    assert metrics["stratum"] == 4
    assert metrics["system_time_dir"] == "slow"
    assert abs(metrics["system_time_ms"] - (-0.004163)) < 1e-6
    assert abs(metrics["last_offset_ms"] - (-0.001554)) < 1e-6
    assert abs(metrics["rms_offset_ms"] - 0.005164) < 1e-6
    assert abs(metrics["root_delay_ms"] - 0.771621) < 1e-6
    assert metrics["update_interval"] == 16.3
    assert metrics["leap_status"] == "Normal"

def test_chrony_4x_csv_unsync():
    metrics = parse_chrony_4x_zabbix(SAMPLE_CHRONY_4X_CSV_UNSYNC)
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

