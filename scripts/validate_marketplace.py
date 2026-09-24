from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
marketplace = json.loads((ROOT / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8"))
plugins = marketplace.get("plugins")
if not isinstance(plugins, list):
    raise SystemExit("marketplace.json must define a plugins array")

entry = next((item for item in plugins if item.get("name") == "agent-switchboard"), None)
if entry is None:
    raise SystemExit("agent-switchboard is missing from the marketplace")
source = entry.get("source", {})
if source.get("source") != "local":
    raise SystemExit("agent-switchboard must use a local repository path")

plugin_root = (ROOT / source.get("path", "")).resolve()
expected = (ROOT / "plugins" / "agent-switchboard").resolve()
if plugin_root != expected:
    raise SystemExit("marketplace path must point to plugins/agent-switchboard")

manifest = json.loads((plugin_root / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
if manifest.get("name") != entry["name"]:
    raise SystemExit("marketplace and plugin manifest names do not match")
for required in (
    plugin_root / ".mcp.json",
    plugin_root / "agent_switchboard" / "ui_bundle.js",
    plugin_root / "assets" / "icon.svg",
):
    if not required.is_file():
        raise SystemExit(f"required plugin file is missing: {required.relative_to(ROOT)}")

policy = entry.get("policy", {})
if policy.get("installation") not in {"NOT_AVAILABLE", "AVAILABLE", "INSTALLED_BY_DEFAULT"}:
    raise SystemExit("invalid marketplace installation policy")
if policy.get("authentication") not in {"ON_INSTALL", "ON_USE"}:
    raise SystemExit("invalid marketplace authentication policy")
if not entry.get("category"):
    raise SystemExit("marketplace category is required")

print("Marketplace package structure is valid.")