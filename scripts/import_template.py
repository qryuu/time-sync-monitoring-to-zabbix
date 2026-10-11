#!/usr/bin/env python3
"""
Zabbix Template Importer (Python)
Imports time synchronization accuracy templates to Zabbix Server 7.0/6.0.
Supports bilingual selection, OS language auto-detection, and host.create.
Dependencies: Python standard library only.
"""
import sys
import os
import json
import argparse
import urllib.request
import locale
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

def call_zabbix_api(url: str, token: str, method: str, params: dict) -> dict:
    endpoint = url.rstrip('/') + "/api_jsonrpc.php"
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "auth": token,
        "id": 1
    }
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode('utf-8'),
        headers={"Content-Type": "application/json-rpc"}
    )
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode('utf-8'))
    if "error" in res:
        raise RuntimeError(f"Zabbix API Error ({method}): {res['error'].get('message')} - {res['error'].get('data')}")
    return res.get("result")

def main():
    parser = argparse.ArgumentParser(description="Import time synchronization templates into Zabbix 7.0/6.0")
    parser.add_argument("--url", required=True, help="Zabbix Web URL (e.g. http://localhost/zabbix)")
    parser.add_argument("--token", required=True, help="Zabbix API Token")
    parser.add_argument("--type", choices=["chrony", "ntp"], default="chrony", help="Template type to import")
    parser.add_argument("--language", choices=["auto", "ja", "en"], default="auto", help="Template language")
    parser.add_argument("--host", default="", help="Optional hostname to link/create")

    args = parser.parse_args()

    # 1. Determine Language
    if args.language == "auto":
        default_locale, _ = locale.getdefaultlocale()
        env_lang = os.environ.get("LANG", "")
        if (default_locale and default_locale.lower().startswith("ja")) or "ja" in env_lang.lower():
            resolved_lang = "ja"
        else:
            resolved_lang = "en"
    else:
        resolved_lang = args.language

    print(f"[INFO] Importing {args.type.upper()} template in '{resolved_lang}' language...")

    # 2. Locate Template File
    repo_root = Path(__file__).parent.parent
    tmpl_folder = repo_root / args.type / "templates"
    tmpl_file = tmpl_folder / f"template_{args.type}_accuracy_{resolved_lang}.yaml"

    if not tmpl_file.exists():
        sys.exit(f"[ERROR] Template file not found: {tmpl_file}")

    template_content = tmpl_file.read_text(encoding="utf-8")
    tech_name = f"template_{args.type}_accuracy"

    # 3. Check for existing or legacy templates
    try:
        existing_tmpls = call_zabbix_api(args.url, args.token, "template.get", {
            "filter": {"host": [tech_name]},
            "selectHosts": ["hostid", "host"]
        })
        if existing_tmpls:
            linked_count = len(existing_tmpls[0].get("hosts", []))
            print(f"[INFO] Existing template '{tech_name}' found ({linked_count} linked hosts). Updating safely with historical data preserved...")

        legacy_names = ["chrony_Monitoring-Japanese", "NTP_Monitoring-Japanese", "NTP-remote-Japanese"]
        legacy_tmpls = call_zabbix_api(args.url, args.token, "template.get", {
            "filter": {"host": legacy_names},
            "selectHosts": ["hostid", "host"]
        })
        if legacy_tmpls:
            for lt in legacy_tmpls:
                l_count = len(lt.get("hosts", []))
                print(f"[NOTICE] Legacy template '{lt['host']}' detected ({l_count} linked hosts). Safe coexistence ensured. Consider migrating hosts to '{tech_name}'.")
    except Exception as e:
        print(f"[WARN] Pre-import template check skipped: {e}")

    # 4. Call configuration.import (Strict Zabbix 7.0 camelCase templateDashboards)
    rules = {
        "template_groups": {"createMissing": True, "updateExisting": True},
        "templates": {"createMissing": True, "updateExisting": True},
        "items": {"createMissing": True, "updateExisting": True},
        "triggers": {"createMissing": True, "updateExisting": True},
        "discoveryRules": {"createMissing": True, "updateExisting": True},
        "graphs": {"createMissing": True, "updateExisting": True},
        "templateDashboards": {"createMissing": True, "updateExisting": True}
    }

    call_zabbix_api(args.url, args.token, "configuration.import", {
        "format": "yaml",
        "source": template_content,
        "rules": rules
    })
    print(f"[SUCCESS] Template '{tmpl_file.name}' imported successfully!")

    # 5. Link or create host
    if args.host:
        # Search by technical host name first, then by visible display name
        hosts = call_zabbix_api(args.url, args.token, "host.get", {
            "filter": {"host": [args.host]},
            "selectParentTemplates": ["templateid"]
        })
        if not hosts:
            hosts = call_zabbix_api(args.url, args.token, "host.get", {
                "filter": {"name": [args.host]},
                "selectParentTemplates": ["templateid"]
            })

        tmpl_objs = call_zabbix_api(args.url, args.token, "template.get", {"filter": {"host": [tech_name]}})
        if not tmpl_objs:
            sys.exit(f"[ERROR] Template '{tech_name}' not found in Zabbix after import.")
        tmpl_id = tmpl_objs[0]["templateid"]

        if not hosts:
            print(f"[INFO] Host '{args.host}' does not exist. Creating new host...")
            groups = call_zabbix_api(args.url, args.token, "hostgroup.get", {"filter": {"name": ["Linux servers", "Templates/Applications"]}})
            gid = groups[0]["groupid"] if groups else "2"
            call_zabbix_api(args.url, args.token, "host.create", {
                "host": args.host,
                "groups": [{"groupid": gid}],
                "templates": [{"templateid": tmpl_id}],
                "interfaces": [{
                    "type": 1,
                    "main": 1,
                    "useip": 1,
                    "ip": "127.0.0.1",
                    "dns": "",
                    "port": "10050"
                }]
            })
            print(f"[SUCCESS] Created host '{args.host}' and linked template!")
        else:
            target_host = hosts[0]
            hid = target_host["hostid"]
            hname = target_host.get("name") or target_host.get("host")
            # Preserve existing parent templates to avoid unlinking OS/DB templates
            existing_tmpl_ids = {t["templateid"] for t in target_host.get("parentTemplates", [])}
            if tmpl_id in existing_tmpl_ids:
                print(f"[INFO] Template '{tech_name}' is already linked to host '{hname}'.")
            else:
                existing_tmpl_ids.add(tmpl_id)
                merged_templates = [{"templateid": tid} for tid in sorted(existing_tmpl_ids)]
                call_zabbix_api(args.url, args.token, "host.update", {
                    "hostid": hid,
                    "templates": merged_templates
                })
                preserved_count = len(existing_tmpl_ids) - 1
                print(f"[SUCCESS] Safely linked template to existing host '{hname}' (preserved {preserved_count} existing templates)!")

if __name__ == "__main__":
    main()
