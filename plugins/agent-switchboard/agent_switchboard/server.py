"""MCP entry point for Agent Switchboard."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
import sys
import threading
import time
from pathlib import Path
from typing import Any, Literal

from mcp.server.apps import Apps
from mcp.server.mcpserver import MCPServer

from . import engine

UI_URI = "ui://agent-switchboard/settings/v2.html"
PACKAGE_DIR = Path(__file__).resolve().parent
LOG_MAX_BYTES = 512 * 1024
LOG_MAX_ENTRIES = 200
_LOG_LOCK = threading.Lock()

apps = Apps()


def _log_path() -> Path:
    return engine.codex_home() / "logs" / "agent-switchboard.jsonl"


def _record_log(
    event: str,
    result: str,
    scope: str | None = None,
    target: str | None = None,
    error_code: str | None = None,
    duration_ms: int | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    """Append local operation metadata and explicitly filtered write details."""
    entry: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "event": event,
        "result": result,
    }
    if scope in {"global", "project"}:
        entry["scope"] = scope
    if target in {"main", "subagents", "role"}:
        entry["target"] = target
    if error_code in {"configuration", "file_access", "internal", "operation_failed"}:
        entry["errorCode"] = error_code
    if isinstance(duration_ms, int) and not isinstance(duration_ms, bool):
        entry["durationMs"] = max(0, duration_ms)
    if details:
        entry["details"] = details

    try:
        path = _log_path()
        line = json.dumps(entry, ensure_ascii=False, separators=(",", ":")) + "\n"
        with _LOG_LOCK:
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists() and path.stat().st_size + len(line.encode("utf-8")) > LOG_MAX_BYTES:
                rotated = path.with_name(f"{path.name}.1")
                rotated.unlink(missing_ok=True)
                os.replace(path, rotated)
            with path.open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(line)
    except OSError:
        # Logging must never interrupt a configuration operation.
        return


def _read_logs(limit: int = 100) -> dict[str, Any]:
    if isinstance(limit, bool) or not isinstance(limit, int):
        return {"ok": False, "error": "limit must be an integer."}
    requested = max(1, min(limit, LOG_MAX_ENTRIES))
    path = _log_path()
    entries: list[dict[str, Any]] = []
    try:
        with _LOG_LOCK:
            for source in (path.with_name(f"{path.name}.1"), path):
                if not source.is_file():
                    continue
                for line in source.read_text(encoding="utf-8").splitlines():
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(entry, dict) and isinstance(entry.get("timestamp"), str):
                        entries.append(entry)
    except OSError:
        return {"ok": False, "error": "Plugin logs could not be read."}
    return {"ok": True, "entries": entries[-requested:][::-1]}


def _safe_call(
    function: Any,
    *args: Any,
    log_event: str | None = None,
    log_scope: str | None = None,
    log_target: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        result = function(*args, **kwargs)
        if isinstance(result, dict):
            payload = result
        else:
            payload = {"ok": True, "result": result}
        if log_event:
            elapsed = round((time.perf_counter() - started) * 1000)
            details = _operation_log_details(payload) if payload.get("filesWritten") else None
            _record_log(
                log_event,
                "error" if payload.get("ok") is False else "success",
                log_scope,
                log_target,
                "operation_failed" if payload.get("ok") is False else None,
                elapsed,
                details,
            )
        return payload
    except engine.ConfigError as exc:
        if log_event:
            _record_log(log_event, "error", log_scope, log_target, "configuration", round((time.perf_counter() - started) * 1000))
        return {"ok": False, "error": str(exc)}
    except OSError:
        if log_event:
            _record_log(log_event, "error", log_scope, log_target, "file_access", round((time.perf_counter() - started) * 1000))
        return {
            "ok": False,
            "error": "The configuration file could not be accessed or written. Check the path and file permissions.",
        }
    except Exception:
        if log_event:
            _record_log(log_event, "error", log_scope, log_target, "internal", round((time.perf_counter() - started) * 1000))
        return {
            "ok": False,
            "error": "An unexpected error occurred. Read the configuration again to confirm its current state.",
        }


def _operation_log_details(payload: dict[str, Any]) -> dict[str, Any] | None:
    """Keep paths plus only the managed Codex setting fields in the log."""
    details: dict[str, Any] = {}
    for key in ("filesWritten", "filesDeleted", "changedSettings", "settingsRemoved", "removedSettings"):
        value = payload.get(key)
        if isinstance(value, list) and value:
            details[key] = [item for item in value if isinstance(item, str)][:8]
    for key in ("preservedConfigFile", "orphanedRoleConfig", "roleName"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            details[key] = value[:1024]
    for field in ("settingsWritten", "settingsBeforeRemoval"):
        values = payload.get(field)
        if isinstance(values, dict):
            allowed = engine.TOML_FIELDS
            safe_values = {key: value for key, value in values.items() if key in allowed and isinstance(value, (str, int, float, bool))}
            if safe_values:
                details[field] = safe_values
    return details or None


def _read_ui() -> str:
    template_path = PACKAGE_DIR / "ui_template.html"
    bundle_path = PACKAGE_DIR / "ui_bundle.js"
    if not template_path.is_file() or not bundle_path.is_file():
        raise RuntimeError("Agent Switchboard UI assets are missing. Run npm run build:ui in the plugin directory.")
    template = template_path.read_text(encoding="utf-8")
    bundle = bundle_path.read_text(encoding="utf-8")
    bundle = bundle.replace("</script", "<\\/script")
    return template.replace("/* AGENT_SWITCHBOARD_BUNDLE */", bundle)


@apps.tool(
    resource_uri=UI_URI,
    title="Open Agent Switchboard",
    description=(
        "Open the visual settings panel for Codex project or global model configuration. "
        "When available, pass the current project root; the panel opens on that project and its default subagents. "
        "The panel can also edit named agent roles."
    ),
)
def open_switchboard(project_root: str | None = None) -> dict[str, Any]:
    """Open the interactive Agent Switchboard settings panel."""
    started = time.perf_counter()
    requested = engine.normalize_project_root(project_root)
    if requested:
        resolved = engine.detect_project_root(requested)
        root = str(resolved) if resolved else None
    else:
        root = None
    result = {
        "ok": True,
        "message": "Agent Switchboard is ready.",
        "projectRoot": root,
        "defaultScope": "project" if root else "global",
        "defaultTarget": "subagents",
    }
    _record_log("open_switchboard", "success", result["defaultScope"], "subagents", duration_ms=round((time.perf_counter() - started) * 1000))
    return result


apps.add_html_resource(
    UI_URI,
    _read_ui(),
    name="Agent Switchboard",
    title="Agent Switchboard",
description="Codex agent model, reasoning, speed, context, and compaction settings.",
    prefers_border=True,
)

server = MCPServer("Agent Switchboard", extensions=[apps])


@server.tool()
def get_resolved_config(
    project_root: str | None = None,
    profile: str | None = None,
    include_roles: bool = True,
) -> dict[str, Any]:
    """Read safe settings from Codex layers; set include_roles false to skip role-file reads."""
    return _safe_call(
        engine.get_resolved_config,
        project_root,
        profile,
        include_roles=include_roles,
        log_event="get_resolved_config",
        log_scope="project" if project_root else "global",
    )


@server.tool()
def get_model_catalog(refresh: bool = False) -> dict[str, Any]:
    """List models, reasoning levels, context limits, and speed tiers advertised by the local Codex CLI."""
    return _safe_call(engine.load_model_catalog, refresh, log_event="get_model_catalog")


@server.tool()
def get_plugin_logs(limit: int = 100) -> dict[str, Any]:
    """Read recent local Agent Switchboard operation metadata."""
    return _read_logs(limit)


@server.tool()
def validate_config(
    scope: Literal["global", "project"],
    target: Literal["main", "subagents", "role"],
    settings: dict[str, Any],
    project_root: str | None = None,
    role_name: str | None = None,
) -> dict[str, Any]:
    """Validate proposed model settings without writing any configuration files."""
    return _safe_call(
        engine.validate_config_request,
        scope,
        target,
        settings,
        project_root,
        role_name,
        log_event="validate_config",
        log_scope=scope,
        log_target=target,
    )


@server.tool()
def diff_config(
    scope: Literal["global", "project"],
    target: Literal["main", "subagents", "role"],
    settings: dict[str, Any],
    project_root: str | None = None,
    role_name: str | None = None,
) -> dict[str, Any]:
    """Preview persistent setting changes and the affected config files."""
    return _safe_call(
        engine.diff_config_request,
        scope,
        target,
        settings,
        project_root,
        role_name,
        log_event="diff_config",
        log_scope=scope,
        log_target=target,
    )


@server.tool()
def set_global_config(
    target: Literal["main", "subagents"],
    settings: dict[str, Any],
) -> dict[str, Any]:
    """Write main-agent or default-subagent settings to CODEX_HOME/config.toml."""
    return _safe_call(
        engine.apply_config,
        "global",
        target,
        settings,
        log_event="set_global_config",
        log_scope="global",
        log_target=target,
    )


@server.tool()
def set_project_config(
    project_root: str,
    target: Literal["main", "subagents"],
    settings: dict[str, Any],
) -> dict[str, Any]:
    """Write project overrides to the selected project's .codex/config.toml."""
    return _safe_call(
        engine.apply_config,
        "project",
        target,
        settings,
        project_root,
        log_event="set_project_config",
        log_scope="project",
        log_target=target,
    )


@server.tool()
def set_agent_role(
    scope: Literal["global", "project"],
    role_name: str,
    settings: dict[str, Any],
    project_root: str | None = None,
) -> dict[str, Any]:
    """Write a named agent role and its config_file reference using official Codex TOML settings."""
    return _safe_call(
        engine.apply_agent_role,
        scope,
        role_name,
        settings,
        project_root,
        log_event="set_agent_role",
        log_scope=scope,
        log_target="role",
    )


@server.tool()
def delete_agent_role(
    scope: Literal["global", "project"],
    role_name: str,
    project_root: str | None = None,
) -> dict[str, Any]:
    """Remove one named role from a Codex config layer, preserving custom/shared role files."""
    return _safe_call(
        engine.delete_agent_role,
        scope,
        role_name,
        project_root,
        log_event="delete_agent_role",
        log_scope=scope,
        log_target="role",
    )


@server.tool()
def reset_override(
    scope: Literal["global", "project"],
    target: Literal["main", "subagents", "role"] = "main",
    project_root: str | None = None,
    role_name: str | None = None,
    keys: list[str] | None = None,
) -> dict[str, Any]:
    """Remove selected overrides so Codex inherits the next applicable config layer."""
    if target not in {"main", "subagents", "role"}:
        return {"ok": False, "error": "target must be main, subagents, or role."}
    return _safe_call(
        engine.reset_override,
        scope,
        target,
        project_root,
        role_name,
        keys,
        log_event="reset_override",
        log_scope=scope,
        log_target=target,
    )


def main() -> None:
    """Run the local stdio MCP server."""
    server.run()


if __name__ == "__main__":
    main()
