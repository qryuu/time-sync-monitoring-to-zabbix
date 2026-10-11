# time-sync-monitoring-to-zabbix

Enterprise-grade time synchronization accuracy and quality monitoring template suite for **Zabbix 7.0 / 6.0 LTS**.  
Comprehensive observability for **Chrony**, **NTP (ntpd)**, and **remote NTP appliances** (Agentless / External check), with future roadmap support for **PTP (IEEE 1588)**.

---

## Key Highlights

1. **Master Items Architecture (8x Load Reduction)**:
   - Queries `chronyc` or `ntpq` once per polling cycle as a master item.
   - Drastically cuts process forking and network overhead while guaranteeing strict atomic time correlation across all extracted metrics.
2. **LLD (Low-Level Discovery) for All Synchronized Sources**:
   - Automatically discovers all configured upstream peers (masters, backups, and pools).
   - Tracks per-peer reachability, round-trip delay, and offset to catch silent upstream network failures before failover occurs.
3. **Grafana-Inspired Modern SVG Aggregate Dashboards**:
   - Built with native Zabbix 7.0 `type: svggraph` and single-value stat cards (`type: item`).
   - Displays client system offset trends with translucent gradient area fills and overlays delay comparisons across all peers in one clean view.
4. **Agentless External Check Script**:
   - Includes standalone script `ntp/scripts/zabbix_ntp_check.py` requiring zero external Python packages.
   - Directly measures remote NTP servers, GPS grandmasters, and network appliances from the Zabbix Server or Proxy.
5. **Out-of-the-Box Bilingual Support (`_ja.yaml` / `_en.yaml`)**:
   - Fully separate Japanese and English templates avoiding UI localization limitations.
   - Built-in OS language detection in PowerShell and Python automation scripts.

---

## Directory Layout

```text
time-sync-monitoring-to-zabbix/
├── chrony/
│   └── templates/
│       ├── template_chrony_accuracy_en.yaml  # English template
│       └── template_chrony_accuracy_ja.yaml  # Japanese template
├── ntp/
│   ├── templates/
│   │   ├── template_ntp_accuracy_en.yaml     # English template (Local & Remote)
│   │   └── template_ntp_accuracy_ja.yaml     # Japanese template
│   └── scripts/
│       └── zabbix_ntp_check.py               # External check script
├── ptp/
│   └── README.md                             # Future PTP (IEEE 1588) roadmap
├── scripts/
│   ├── import_template.ps1                   # Automated importer (PowerShell)
│   └── import_template.py                    # Automated importer (Python)
├── tests/                                    # Automated pytest suite & YAML validator
├── AGENTS.md                                 # AI assistant setup protocol
├── README.md                                 # Documentation (Japanese)
├── README_EN.md                              # Documentation (English)
└── LICENSE                                   # MIT License
```

---

## Quick Start

### 1. Import Template via API

#### Using PowerShell:
```powershell
.\scripts\import_template.ps1 -ZabbixUrl "http://zabbix-server/zabbix" -ApiToken "<API_TOKEN>" -TemplateType Chrony -HostName "App-Server-01"
```

#### Using Python:
```bash
python scripts/import_template.py --url "http://zabbix-server/zabbix" --token "<API_TOKEN>" --type chrony --host "App-Server-01"
```

*Note: If the specified host does not exist in Zabbix, it is automatically created via `host.create` with default interfaces.*

### 2. Zabbix Agent Permissions
Ensure the following key is permitted in your `zabbix_agentd.conf` or `zabbix_agent2.conf`:
```ini
AllowKey=system.run[*]
```
Restart the Zabbix agent daemon after updating the configuration.

---

## Monitored Metrics

| Metric | Description | Collection Method |
| :--- | :--- | :--- |
| **System time offset** | Current clock offset relative to active reference peer (ms) | Master / Dependent item |
| **RMS offset** | Long-term root-mean-square offset estimate (ms) | Master / Dependent item |
| **Network root delay** | Total network round-trip latency to Stratum-1 server (ms) | Master / Dependent item |
| **Stratum** | Clock hierarchy level (Stratum 1 to 16) | Master / Dependent item |
| **Leap status** | Leap second warning status and synchronization state | Master / Dependent item |
| **Source Reachability** | 8-bit octal reach register indicating poll replies over last 8 attempts | LLD / Dependent item |
| **Source Delay / Offset** | Per-peer estimated round-trip delay and time offset | LLD / Dependent item |

---

## License
Distributed under the [MIT License](LICENSE).
