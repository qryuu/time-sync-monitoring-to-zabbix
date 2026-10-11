import csv
import io
import pytest

# Sample output of `chronyc -c tracking`
# Columns:
# 0: Reference ID
# 1: Stratum
# 2: Ref time (UTC)
# 3: System time offset (s)
# 4: Last offset (s)
# 5: RMS offset (s)
# 6: Frequency (ppm)
# 7: Residual freq (ppm)
# 8: Skew (ppm)
# 9: Root delay (s)
# 10: Root dispersion (s)
# 11: Update interval (s)
# 12: Leap status
SAMPLE_CHRONY_CSV_NORMAL = "85F3EEA3,2,Sun Oct 11 05:22:15 2026,-0.000042123,-0.000035000,0.000051234,12.345,-0.001,0.052,0.008234567,0.001234567,64.2,Normal\n"
SAMPLE_CHRONY_CSV_UNSYNC = "00000000,0,Sun Oct 11 05:00:00 2026,0.000000000,0.000000000,0.000000000,0.000,0.000,0.000,0.000000000,0.000000000,0.0,Not synchronized\n"

def parse_chrony_csv(raw_csv: str):
    reader = csv.reader(io.StringIO(raw_csv.strip()))
    row = next(reader)
    return {
        "ref_id": row[0],
        "stratum": int(row[1]),
        "ref_time": row[2],
        "system_time_ms": float(row[3]) * 1000.0,
        "last_offset_ms": float(row[4]) * 1000.0,
        "rms_offset_ms": float(row[5]) * 1000.0,
        "frequency_ppm": float(row[6]),
        "residual_freq": float(row[7]),
        "skew_ppm": float(row[8]),
        "root_delay_ms": float(row[9]) * 1000.0,
        "root_disp_ms": float(row[10]) * 1000.0,
        "update_interval": float(row[11]),
        "leap_status": row[12],
    }

def test_chrony_csv_normal():
    metrics = parse_chrony_csv(SAMPLE_CHRONY_CSV_NORMAL)
    assert metrics["ref_id"] == "85F3EEA3"
    assert metrics["stratum"] == 2
    assert abs(metrics["last_offset_ms"] - (-0.035)) < 1e-6
    assert abs(metrics["rms_offset_ms"] - 0.051234) < 1e-6
    assert abs(metrics["root_delay_ms"] - 8.234567) < 1e-6
    assert metrics["update_interval"] == 64.2
    assert metrics["leap_status"] == "Normal"

def test_chrony_csv_unsync():
    metrics = parse_chrony_csv(SAMPLE_CHRONY_CSV_UNSYNC)
    assert metrics["stratum"] == 0
    assert metrics["leap_status"] == "Not synchronized"
    assert metrics["last_offset_ms"] == 0.0
