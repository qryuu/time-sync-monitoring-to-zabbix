import re
import yaml
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
UUIDV4_RE = re.compile(r"^[0-9a-f]{12}4[0-9a-f]{3}[89ab][0-9a-f]{15}$", re.IGNORECASE)
OFFICIAL_APP_GROUP_UUID = "a571c0d144b14fd4a87a9d9b2aa9fcd6"

def get_template_files():
    return list(REPO_ROOT.glob("**/templates/*.yaml"))

def test_template_files_exist():
    templates = get_template_files()
    assert len(templates) >= 2, "At least 2 templates should be present."

@pytest.mark.parametrize("yaml_path", get_template_files())
def test_template_syntax_and_conventions(yaml_path):
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert "zabbix_export" in data, f"{yaml_path} must have 'zabbix_export' root"
    export_data = data["zabbix_export"]

    # 1. Version must be 7.0
    assert export_data.get("version") == "7.0", f"{yaml_path} version must be 7.0"

    # 2. Date tag must NOT exist (Zabbix 7.0 schema violation)
    assert "date" not in export_data, f"{yaml_path} must not have 'date' tag in Zabbix 7.0"

    # 3. Root must use template_groups instead of groups
    assert "template_groups" in export_data, f"{yaml_path} root must use template_groups"
    assert "groups" not in export_data, f"{yaml_path} root must not use legacy 'groups'"

    # 4. Official group UUID check for Templates/Applications
    for tg in export_data["template_groups"]:
        if tg.get("name") == "Templates/Applications":
            assert tg.get("uuid") == OFFICIAL_APP_GROUP_UUID, (
                f"{yaml_path}: 'Templates/Applications' must use official UUID '{OFFICIAL_APP_GROUP_UUID}'"
            )

    templates = export_data.get("templates", [])
    assert len(templates) > 0, f"{yaml_path} must contain at least one template"

    for t in templates:
        # 5. Technical template name must start with template_
        t_name = t.get("template", "")
        assert t_name.startswith("template_"), f"Template technical name '{t_name}' must start with 'template_'"

        # 6. Inside template, group reference must be groups (Zabbix 7.0 specification)
        assert "groups" in t, f"Template '{t_name}' in {yaml_path} must contain 'groups'"
        assert "template_groups" not in t, f"Template '{t_name}' in {yaml_path} must not contain 'template_groups'"

        # 7. Check for deprecated 'LINE' in graph prototypes or graphs
        all_graphs = t.get("graphs", [])
        for disc in t.get("discovery_rules", []):
            all_graphs.extend(disc.get("graph_prototypes", []))
        if "graphs" in export_data:
            all_graphs.extend(export_data["graphs"])

        for g in all_graphs:
            for gi in g.get("graph_items", []):
                drawtype = gi.get("drawtype")
                assert drawtype != "LINE", f"Legacy drawtype 'LINE' found in graph '{g.get('name')}'. Use 'SINGLE_LINE' instead."

        # 8. Check macros defined
        defined_macros = {m.get("macro") for m in t.get("macros", [])}
        for item in t.get("items", []):
            for trig in item.get("triggers", []):
                expr = trig.get("expression", "")
                if "{$NTP_OFFSET_SMALL}" in expr:
                    assert "{$NTP_OFFSET_SMALL}" in defined_macros, f"Macro {{$NTP_OFFSET_SMALL}} used in trigger but not defined in {t_name}"
                if "{$NTP_OFFSET_LARGE}" in expr:
                    assert "{$NTP_OFFSET_LARGE}" in defined_macros, f"Macro {{$NTP_OFFSET_LARGE}} used in trigger but not defined in {t_name}"

    # 9. Verify that all UUIDs across the entire document comply strictly with UUIDv4
    def verify_uuids(node, path=""):
        if isinstance(node, dict):
            for k, v in node.items():
                if k == "uuid" and isinstance(v, str):
                    assert UUIDV4_RE.match(v), f"Invalid UUIDv4 '{v}' found at {path}.uuid in {yaml_path}"
                else:
                    verify_uuids(v, f"{path}.{k}" if path else k)
        elif isinstance(node, list):
            for i, elem in enumerate(node):
                verify_uuids(elem, f"{path}[{i}]")

    verify_uuids(data)
