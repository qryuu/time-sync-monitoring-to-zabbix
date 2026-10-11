import re
import pytest

SAMPLE_NTPQ_STANDARD = """
     remote           refid      st t when poll reach   delay   offset  jitter
==============================================================================
*ntp1.jst.mfeed. 133.243.238.163  2 u   42   64  377    8.234   -0.042   0.051
+ntp2.jst.mfeed. 133.243.238.164  2 u   12   64  377   11.512    0.125   0.082
-ntp3.jst.mfeed. 133.243.238.165  2 u   15   64  377   15.100    1.200   0.100
"""

SAMPLE_NTPQ_PPS = """
     remote           refid      st t when poll reach   delay   offset  jitter
==============================================================================
oPPS(0)          .PPS.            0 l    4   16  377    0.000    0.001   0.002
*ntp.nict.jp     .NICT.           1 u   20   64  377   12.345   -1.234   0.456
"""

SAMPLE_NTPQ_IPV6 = """
     remote           refid      st t when poll reach   delay   offset  jitter
==============================================================================
*2001:df0:232:ee 133.243.238.163  2 u   10   64  377    5.678   -0.012   0.034
+2001:df0:232:ef 133.243.238.164  2 u    5   64  377    6.789    0.056   0.045
"""

# Regex patterns matching Zabbix preprocessing steps
PATTERNS = {
    "peer": r"(?m)^[*o]\s*(\S+)",
    "refid": r"(?m)^[*o]\s*\S+\s+(\S+)",
    "stratum": r"(?m)^[*o]\s*\S+\s+\S+\s+(\d+)",
    "poll": r"(?m)^[*o]\s*\S+\s+\S+\s+\d+\s+\S+\s+\S+\s+(\d+)",
    "reach": r"(?m)^[*o]\s*\S+\s+\S+\s+\d+\s+\S+\s+\S+\s+\d+\s+(\d+)",
    "delay": r"(?m)^[*o]\s*\S+\s+\S+\s+\d+\s+\S+\s+\S+\s+\d+\s+\d+\s+([-\d.]+)",
    "offset": r"(?m)^[*o]\s*\S+\s+\S+\s+\d+\s+\S+\s+\S+\s+\d+\s+\d+\s+[-\d.]+\s+([-\d.]+)",
    "jitter": r"(?m)^[*o]\s*\S+\s+\S+\s+\d+\s+\S+\s+\S+\s+\d+\s+\d+\s+[-\d.]+\s+[-\d.]+\s+([-\d.]+)",
}

def extract_metric(text: str, pattern_key: str) -> str:
    match = re.search(PATTERNS[pattern_key], text)
    if not match:
        raise ValueError(f"Pattern '{pattern_key}' did not match.")
    return match.group(1)

def test_ntpq_standard_extraction():
    assert extract_metric(SAMPLE_NTPQ_STANDARD, "peer") == "ntp1.jst.mfeed."
    assert extract_metric(SAMPLE_NTPQ_STANDARD, "refid") == "133.243.238.163"
    assert extract_metric(SAMPLE_NTPQ_STANDARD, "stratum") == "2"
    assert extract_metric(SAMPLE_NTPQ_STANDARD, "poll") == "64"
    assert extract_metric(SAMPLE_NTPQ_STANDARD, "reach") == "377"
    assert extract_metric(SAMPLE_NTPQ_STANDARD, "delay") == "8.234"
    assert extract_metric(SAMPLE_NTPQ_STANDARD, "offset") == "-0.042"
    assert extract_metric(SAMPLE_NTPQ_STANDARD, "jitter") == "0.051"

def test_ntpq_pps_extraction():
    assert extract_metric(SAMPLE_NTPQ_PPS, "peer") == "PPS(0)"
    assert extract_metric(SAMPLE_NTPQ_PPS, "refid") == ".PPS."
    assert extract_metric(SAMPLE_NTPQ_PPS, "stratum") == "0"
    assert extract_metric(SAMPLE_NTPQ_PPS, "delay") == "0.000"
    assert extract_metric(SAMPLE_NTPQ_PPS, "offset") == "0.001"
    assert extract_metric(SAMPLE_NTPQ_PPS, "jitter") == "0.002"

def test_ntpq_ipv6_extraction():
    assert extract_metric(SAMPLE_NTPQ_IPV6, "peer") == "2001:df0:232:ee"
    assert extract_metric(SAMPLE_NTPQ_IPV6, "delay") == "5.678"
    assert extract_metric(SAMPLE_NTPQ_IPV6, "offset") == "-0.012"
    assert extract_metric(SAMPLE_NTPQ_IPV6, "jitter") == "0.034"
