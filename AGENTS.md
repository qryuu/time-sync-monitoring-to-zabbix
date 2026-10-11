# AGENTS.md: AI Assistant Setup & Operations Protocol

This document defines the autonomous operational guidelines, diagnostic wizard, and guardrails for AI coding assistants (such as Antigravity, Gemini, Claude, Cursor) working with `time-sync-monitoring-to-zabbix`.

---

## 1. Safety Guardrails & Principles (MUST FOLLOW)

### Rule 1: Host Management & Prohibition of Unrelated Host Reuse
- **Strict Prohibition**: When configuring or importing templates, NEVER inspect, borrow, or reuse unrelated existing hosts (e.g., test hosts, other services) in the user's Zabbix environment.
- **Auto-Creation (`host.create`)**: If the designated target host (e.g., `-HostName "NTP-Server-01"`) does not exist in Zabbix, ALWAYS create a new dedicated host via `host.create` with appropriate interface settings (IP: `127.0.0.1` / port `10050` or remote target IP).

### Rule 2: Autonomous CLI Tool Installation Allowed
- When `chronyc` or `ntpq` is not found on the local or target operating system:
  - Do NOT pause or ask the user for manual intervention immediately.
  - The AI assistant is explicitly authorized to autonomously detect the package manager (`apt-get`, `dnf`, `yum`, `winget`, `choco`) and install the necessary client utilities (`chrony` or `ntp` / `ntpstat`), followed by a quick verification command (`chronyc tracking` or `ntpq -p`).

### Rule 3: Task Scheduler & Background Process Execution (Error 0x80070002 Prevention)
- When registering scheduled tasks on Windows via PowerShell (`setup.ps1` or `Register-ScheduledTask`):
  - NEVER use relative executable names like `pwsh.exe` or `powershell.exe`.
  - ALWAYS resolve and specify the **complete absolute path** (e.g., `"$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"` or explicitly resolved `(Get-Command pwsh.exe).Source`).
  - This prevents failure code `0x80070002` ("The system cannot find the file specified") in non-interactive system service contexts.

### Rule 4: Zabbix 7.0 / 6.0 Strict Specifications
- **Template Dashboards**: API parameter `rules.templateDashboards` must be in camelCase.
- **Classic Graph Drawtype**: Must use `SINGLE_LINE` or `BOLD_LINE` (never use `LINE`, which causes an `unexpected constant` error in 7.0).
- **Template Technical Name Prefix**: Always maintain the `template_` prefix (e.g., `template_ntp_accuracy`, `template_chrony_accuracy`) to prevent collision with actual hostname records.

### Rule 5: Bilingual Support & Auto Language Detection
- Zabbix templates do not support runtime string translation for item/trigger/dashboard names.
- Always offer or select both `_ja.yaml` (Japanese) and `_en.yaml` (English).
- Import scripts (`import_template.ps1` and `import_template.py`) must inspect the OS locale (`Get-Culture` / `$LANG`) when `-Language Auto` is passed.

### Rule 6: Existing Template Handling & Safe Upgrade Protocol
- **Pre-Import Query (`template.get`)**: Before calling `configuration.import`, check whether `template_ntp_accuracy` or `template_chrony_accuracy` already exists.
- **Historical Data Preservation**:
  - Always use `updateExisting: true` without `deleteMissing: true` so that existing item history/trends are strictly preserved.
  - If existing templates are linked to production hosts, notify the user with linked host counts before major schema updates.
- **Legacy Version Coexistence**:
  - Legacy templates (`chrony_Monitoring-Japanese`, `NTP_Monitoring-Japanese`) use different technical names and will safely coexist without collision.
  - When legacy templates are detected on target hosts, assist the user in adding the new template and safely unlinking (without clearing history) the legacy template.

---

## 2. Interactive Setup & Diagnostics Wizard

When a user asks to "set up time synchronization monitoring" or "link to Zabbix":

```
Step 1: Environment Detection
  ├─ Check OS: Linux vs Windows
  ├─ Check Installed Daemons: chrony (active?) vs ntpd (active?) vs w32time
  └─ Test CLI Output: `chronyc -c tracking` or `ntpq -p`

Step 2: Zabbix Agent Security Check
  ├─ Verify zabbix_agentd.conf / zabbix_agent2.conf:
  │   - Ensure `AllowKey=system.run[*]` is enabled (or `EnableRemoteCommands=1`)
  └─ Test agent execution: `zabbix_agentd -t "system.run[chronyc -c tracking]"`

Step 3: Zabbix Template Import
  ├─ Determine language (`ja` vs `en`)
  ├─ Execute: `python scripts/import_template.py --url <URL> --token <TOKEN> --type chrony --host <TARGET>`
  │  (or PowerShell: `.\scripts\import_template.ps1 -ZabbixUrl <URL> -ApiToken <TOKEN> -TemplateType Chrony`)
  └─ Verify templateDashboards and discovery rules created

Step 4: Real-time Verification
  ├─ Wait 60 seconds for initial polling
  ├─ Check latest item values: System Offset, Root Delay, Leap Status
  └─ Open template dashboard in Zabbix Web UI
```
