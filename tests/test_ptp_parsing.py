import json
import re
import pytest

SAMPLE_PMC_OUTPUT = """
sending: GET TIME_STATUS_NP
sending: GET CURRENT_DATA_SET
sending: GET PORT_DATA_SET
\t000000.fffe.000000-0 seq 0 RESPONSE MANAGEMENT TIME_STATUS_NP 
\t\tmaster_offset              -15
\t\tingress_time               1700000000123456789
\t\tcumulativeScaledRateOffset +0.000000000
\t\tscaledLastGmPhaseChange    0
\t\tgmTimeBaseIndicator        0
\t\tlastGmPhaseChange          0x0000'0000000000000000.0000
\t\tgmPresent                  true
\t\tgmIdentity                 000000.fffe.000001
\t000000.fffe.000000-0 seq 1 RESPONSE MANAGEMENT CURRENT_DATA_SET 
\t\tstepsRemoved     1
\t\toffsetFromMaster -15.0
\t\tmeanPathDelay    1420.5
\t000000.fffe.000000-1 seq 2 RESPONSE MANAGEMENT PORT_DATA_SET 
\t\tportIdentity            000000.fffe.000000-1
\t\tportState               SLAVE
\t\tlogMinDelayReqInterval  0
\t\tpeerMeanPathDelay       0
\t\tlogAnnounceInterval     1
\t\tannounceReceiptTimeout  3
\t\tlogSyncInterval         0
\t\tdelayMechanism          1
\t\tlogMinPdelayReqInterval 0
\t\tversionNumber           2
"""

SAMPLE_PMC_UNSYNC = """
sending: GET TIME_STATUS_NP
sending: GET CURRENT_DATA_SET
sending: GET PORT_DATA_SET
\t000000.fffe.000000-0 seq 0 RESPONSE MANAGEMENT TIME_STATUS_NP 
\t\tmaster_offset              0
\t\tingress_time               0
\t\tcumulativeScaledRateOffset +0.000000000
\t\tscaledLastGmPhaseChange    0
\t\tgmTimeBaseIndicator        0
\t\tlastGmPhaseChange          0x0000'0000000000000000.0000
\t\tgmPresent                  false
\t\tgmIdentity                 000000.fffe.000000
\t000000.fffe.000000-0 seq 1 RESPONSE MANAGEMENT CURRENT_DATA_SET 
\t\tstepsRemoved     0
\t\toffsetFromMaster 0.0
\t\tmeanPathDelay    0.0
\t000000.fffe.000000-1 seq 2 RESPONSE MANAGEMENT PORT_DATA_SET 
\t\tportIdentity            000000.fffe.000000-1
\t\tportState               LISTENING
\t\tlogMinDelayReqInterval  0
\t\tpeerMeanPathDelay       0
\t\tlogAnnounceInterval     1
\t\tannounceReceiptTimeout  3
\t\tlogSyncInterval         0
\t\tdelayMechanism          1
\t\tlogMinPdelayReqInterval 0
\t\tversionNumber           2
"""

def parse_pmc_output_to_dict(raw_output: str) -> dict:
    """Simulates Zabbix JavaScript preprocessing for pmc multi-GET output."""
    res = {}
    for line in raw_output.splitlines():
        line = line.strip()
        if not line or "RESPONSE" in line or line.startswith("sending:"):
            continue
        match = re.match(r"^([a-zA-Z0-9_]+)\s+(.+)$", line)
        if match:
            res[match.group(1)] = match.group(2).strip()
    return res

def test_parse_pmc_synchronized():
    data = parse_pmc_output_to_dict(SAMPLE_PMC_OUTPUT)
    assert data["master_offset"] == "-15"
    assert data["gmPresent"] == "true"
    assert data["gmIdentity"] == "000000.fffe.000001"
    assert data["stepsRemoved"] == "1"
    assert data["offsetFromMaster"] == "-15.0"
    assert data["meanPathDelay"] == "1420.5"
    assert data["portState"] == "SLAVE"
    assert data["portIdentity"] == "000000.fffe.000000-1"

def test_parse_pmc_unsynchronized():
    data = parse_pmc_output_to_dict(SAMPLE_PMC_UNSYNC)
    assert data["master_offset"] == "0"
    assert data["gmPresent"] == "false"
    assert data["gmIdentity"] == "000000.fffe.000000"
    assert data["stepsRemoved"] == "0"
    assert data["offsetFromMaster"] == "0.0"
    assert data["meanPathDelay"] == "0.0"
    assert data["portState"] == "LISTENING"

def test_numeric_extractions():
    data = parse_pmc_output_to_dict(SAMPLE_PMC_OUTPUT)
    offset_ns = float(data["offsetFromMaster"])
    delay_ns = float(data["meanPathDelay"])
    steps = int(data["stepsRemoved"])
    assert abs(offset_ns) == 15.0
    assert delay_ns > 1000.0
    assert steps == 1
