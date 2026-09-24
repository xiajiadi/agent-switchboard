"""Safe, comment-preserving edits to official Codex configuration layers."""

from __future__ import annotations

import copy
import difflib
import json
import os
import re
import shutil
import stat
import subprocess
import threading
import tempfile
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import tomlkit
from tomlkit.items import Table

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FALLBACK_CATALOG = PLUGIN_ROOT / "data" / "model_catalog.json"
FALLBACK_VISIBLE_MODEL_IDS = {
    "gpt-6-astra",
    "gpt-6-sol",
    "gpt-6-luna",
    "gpt-5.6-sol",
    "gpt-5.6-terra",
    "gpt-5.6-luna",
    "gpt-5.5",
}
NEVER_PICK_MODEL_IDS = {"auto", "codex-auto-review"}
MIN_MODEL_CONTEXT_WINDOW = 256_000
DEFAULT_AUTO_COMPACT_PERCENT = 90
MODEL_CATALOG_CACHE_SECONDS = 300
_MODEL_CATALOG_CACHE_LOCK = threading.Lock()
_MODEL_CATALOG_CACHE: tuple[float, dict[str, Any]] | None = None

SETTING_ALIASES = {
    "model": "model",
    "reasoning_effort": "model_reasoning_effort",
    "model_reasoning_effort": "model_reasoning_effort",
    "speed": "speed",
    "service_tier": "service_tier",
    "model_context_window": "model_context_window",
    "context_window": "model_context_window",
    "model_auto_compact_token_limit": "model_auto_compact_token_limit",
    "auto_compact_token_limit": "model_auto_compact_token_limit",
}
TOML_FIELDS = {
    "model",
    "model_reasoning_effort",
    "service_tier",
    "model_context_window",
    "model_auto_compact_token_limit",
}
SHARED_FIELDS = {
    "service_tier",
    "model_context_window",
    "model_auto_compact_token_limit",
}
REASONING_EFFORTS = {"none", "low", "medium", "high", "xhigh", "max", "ultra"}
RESERVED_AGENT_NAMES = {
    "enabled",
    "interrupt_message",
    "max_concurrent_threads_per_session",
    "max_threads",
    "default_subagent_model",
    "default_subagent_reasoning_effort",
}
ROLE_NAME_RE = re.compile(r"^[a-z][a-z0-9_-]{0,47}$")
PROFILE_NAME_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
MODEL_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


class ConfigError(ValueError):
    """An invalid or unsafe configuration request."""


def codex_home() -> Path:
    configured = os.environ.get("CODEX_HOME")
    base = Path(configured).expanduser() if configured else Path.home() / ".codex"
    return base.resolve()


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def detect_project_root(candidate: str | None = None) -> Path | None:
    """Return an explicit project path, or discover a marked root from cwd."""
    requested = normalize_project_root(candidate) or normalize_project_root(
        os.environ.get("AGENT_SWITCHBOARD_PROJECT_ROOT")
    )
    if requested:
        path = Path(requested).expanduser()
        if not path.is_absolute():
            raise ConfigError("projectRoot must be an absolute path.")
        resolved = path.resolve()
        if not resolved.is_dir():
            raise ConfigError("projectRoot must point to an existing directory.")
        return resolved

    current = Path.cwd().resolve()
    for directory in (current, *current.parents):
        if (
            (directory / ".git").exists()
            or (directory / "AGENTS.md").is_file()
            or (directory / ".codex" / "config.toml").is_file()
        ):
            return directory
    return None


def normalize_project_root(candidate: str | None) -> str | None:
    """Trim copied paths, including one matching pair of surrounding quotes."""
    if not isinstance(candidate, str):
        return None
    requested = candidate.strip()
    if len(requested) >= 2 and requested[0] == requested[-1] and requested[0] in {"\"", "'"}:
        requested = requested[1:-1].strip()
    return requested or None


def config_path(scope: str, project_root: str | None = None) -> Path:
    if scope == "global":
        return codex_home() / "config.toml"
    if scope != "project":
        raise ConfigError("Persistent config scope must be global or project.")
    root = detect_project_root(project_root)
    if root is None:
        raise ConfigError("Provide the absolute projectRoot for project-scoped configuration.")
    target = (root / ".codex" / "config.toml").resolve()
    if not _is_relative_to(target, root):
        raise ConfigError("Project config path resolves outside projectRoot.")
    return target


def role_config_path(parent_config: Path, role_name: str, declared_path: str | None = None) -> Path:
    validate_role_name(role_name)
    base = parent_config.parent.resolve()
    relative = declared_path or f"agents/roles/{role_name}.toml"
    candidate = Path(relative)
    if candidate.is_absolute():
        raise ConfigError("Agent role config_file must be relative to its declaring config.toml.")
    unresolved = base / candidate
    cursor = base
    for part in candidate.parts:
        if part in {"", "."}:
            continue
        cursor = cursor.parent if part == ".." else cursor / part
        if cursor.is_symlink():
            raise ConfigError("Refusing to edit a symlinked role configuration path.")
    target = unresolved.resolve()
    if not _is_relative_to(target, base):
        raise ConfigError("Agent role config_file resolves outside its config directory.")
    return target


def validate_role_name(role_name: str) -> str:
    if not isinstance(role_name, str) or not ROLE_NAME_RE.fullmatch(role_name):
        raise ConfigError("Role names must start with a lowercase letter and use only letters, digits, _ or -.")
    if role_name in RESERVED_AGENT_NAMES:
        raise ConfigError(f"{role_name!r} is a reserved Codex agents setting, not a role name.")
    return role_name


def _read_document(path: Path) -> tuple[Any, str]:
    if path.exists():
        if path.is_symlink():
            raise ConfigError(f"Refusing to edit a symlinked configuration file: {path}")
        if not path.is_file():
            raise ConfigError(f"Configuration path is not a regular file: {path}")
        raw = path.read_text(encoding="utf-8")
        try:
            return tomlkit.parse(raw), raw
        except Exception as exc:
            raise ConfigError(f"Invalid TOML in {path}; the file was left unchanged.") from exc
    return tomlkit.document(), ""


def _to_plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _to_plain(child) for key, child in value.items()}
    if isinstance(value, list):
        return [_to_plain(child) for child in value]
    return value


def _read_plain(path: Path) -> dict[str, Any]:
    document, _ = _read_document(path)
    return _to_plain(document)


def _deep_merge(base: dict[str, Any], overlay: Mapping[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(base)
    for key, value in overlay.items():
        if isinstance(value, Mapping) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        elif isinstance(value, Mapping):
            result[key] = _deep_merge({}, value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def _selected_values(config: Mapping[str, Any], target: str) -> dict[str, Any]:
    values: dict[str, Any] = {}
    fields = SHARED_FIELDS | ({"model", "model_reasoning_effort"} if target == "main" else set())
    for field in fields:
        if field in config:
            values[field] = config[field]
    if target == "subagents":
        agents = config.get("agents", {})
        if isinstance(agents, Mapping):
            if "default_subagent_model" in agents:
                values["agents.default_subagent_model"] = agents["default_subagent_model"]
            if "default_subagent_reasoning_effort" in agents:
                values["agents.default_subagent_reasoning_effort"] = agents[
                    "default_subagent_reasoning_effort"
                ]
    return values


def _settings_before_removal(config: Mapping[str, Any], target: str, fields: list[str]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    agents = config.get("agents", {})
    for field in fields:
        source = field
        if target == "subagents" and field in {"model", "model_reasoning_effort"}:
            source = {
                "model": "default_subagent_model",
                "model_reasoning_effort": "default_subagent_reasoning_effort",
            }[field]
            value = agents.get(source) if isinstance(agents, Mapping) else None
        else:
            value = config.get(source)
        if isinstance(value, (str, int, float, bool)):
            values[field] = value
    return values


def _agent_names(config: Mapping[str, Any]) -> set[str]:
    agents = config.get("agents", {})
    if not isinstance(agents, Mapping):
        return set()
    return {
        str(name)
        for name, value in agents.items()
        if name not in RESERVED_AGENT_NAMES and isinstance(value, Mapping)
    }


def _role_layers(
    layers: list[tuple[str, Path, dict[str, Any]]],
    roles: set[str],
) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    for role in sorted(roles):
        try:
            validate_role_name(role)
        except ConfigError:
            continue
        effective: dict[str, Any] = {}
        sources: dict[str, str] = {}
        file_paths: list[str] = []
        for layer_name, parent_path, config in layers:
            agents = config.get("agents", {})
            agent = agents.get(role, {}) if isinstance(agents, Mapping) else {}
            pointer = agent.get("config_file") if isinstance(agent, Mapping) else None
            if not isinstance(pointer, str):
                continue
            role_path = role_config_path(parent_path, role, pointer)
            role_config = _read_plain(role_path)
            for key, value in role_config.items():
                if key in TOML_FIELDS:
                    effective[key] = value
                    sources[key] = layer_name
            file_paths.append(str(role_path))
        output[role] = {
            "settings": effective,
            "sources": sources,
            "configFiles": file_paths,
        }
    return output


def get_resolved_config(
    project_root: str | None = None,
    profile: str | None = None,
    include_project: bool = True,
    include_roles: bool = True,
) -> dict[str, Any]:
    global_path = config_path("global")
    global_config = _read_plain(global_path)
    selected_profile = profile
    if selected_profile is None and isinstance(global_config.get("profile"), str):
        selected_profile = global_config["profile"]
    if selected_profile and not PROFILE_NAME_RE.fullmatch(selected_profile):
        raise ConfigError("Profile names may use only letters, digits, _ or - (up to 64 characters).")

    layers: list[tuple[str, Path, dict[str, Any]]] = [("global", global_path, global_config)]
    profile_path: Path | None = None
    profile_config: dict[str, Any] = {}
    if selected_profile:
        profile_path = codex_home() / f"{selected_profile}.config.toml"
        profile_config = _read_plain(profile_path)
        layers.append(("profile", profile_path, profile_config))

    root = detect_project_root(project_root) if include_project else None
    project_path: Path | None = None
    project_config: dict[str, Any] = {}
    if root is not None:
        project_path = config_path("project", str(root))
        project_config = _read_plain(project_path)
        layers.append(("project", project_path, project_config))

    effective: dict[str, Any] = {}
    source_map: dict[str, str] = {}
    for layer_name, _, config in layers:
        effective = _deep_merge(effective, config)
        for key in TOML_FIELDS:
            if key in config:
                source_map[key] = layer_name
        for agent_field in ("default_subagent_model", "default_subagent_reasoning_effort"):
            if isinstance(config.get("agents"), Mapping) and agent_field in config["agents"]:
                source_map[f"agents.{agent_field}"] = layer_name

    role_layers: dict[str, dict[str, Any]] = {layer_name: {} for layer_name, _, _ in layers}
    roles: dict[str, dict[str, Any]] = {}
    if include_roles:
        # Read each role file once. The UI skips this work on startup and asks for
        # role data only when the role manager or a named role is opened.
        for layer_name, layer_path, config in layers:
            layer_roles = _role_layers(
                [(layer_name, layer_path, config)],
                _agent_names(config),
            )
            role_layers[layer_name] = layer_roles
            for role_name, role_data in layer_roles.items():
                merged = roles.setdefault(
                    role_name,
                    {"settings": {}, "sources": {}, "configFiles": []},
                )
                merged["settings"].update(role_data["settings"])
                merged["sources"].update(role_data["sources"])
                merged["configFiles"].extend(role_data["configFiles"])
    effective_agents = effective.get("agents", {})
    effective_roles: dict[str, dict[str, Any]] = {}
    for role_name, role_data in roles.items():
        role_settings = {
            field: effective[field]
            for field in SHARED_FIELDS
            if field in effective
        }
        if isinstance(effective_agents, Mapping):
            for field, inherited_field in (
                ("model", "default_subagent_model"),
                ("model_reasoning_effort", "default_subagent_reasoning_effort"),
            ):
                if inherited_field in effective_agents:
                    role_settings[field] = effective_agents[inherited_field]
        role_settings.update(role_data["settings"])
        effective_roles[role_name] = {**role_data, "settings": role_settings}

    global_view = _selected_values(global_config, "subagents")
    profile_view = _selected_values(profile_config, "subagents") if profile_path else {}
    project_view = _selected_values(project_config, "subagents") if project_path else {}
    resolved = {
        "main": _selected_values(effective, "main"),
        "subagents": _selected_values(effective, "subagents"),
        "roles": effective_roles,
    }
    warnings = [
        "Codex only loads project .codex/config.toml when the project is trusted; trust status is not queried by this plugin.",
        "Cloud-managed and system configuration are outside this local editor's read scope.",
        "CLI flags supplied to the already-running Codex process can override this resolved view.",
    ]
    if selected_profile:
        warnings.append(
            "An active profile can override user-level config.toml values; project config has higher precedence than the profile."
        )
    return {
        "ok": True,
        "configFiles": {
            "global": str(global_path),
            "profile": str(profile_path) if profile_path else None,
            "project": str(project_path) if project_path else None,
        },
        "selectedProfile": selected_profile,
        "layers": {
            "global": global_view,
            "profile": profile_view,
            "project": project_view,
        },
        "roleLayers": role_layers,
        "effective": resolved,
        "sources": source_map,
        "warnings": warnings,
    }


def load_model_catalog(refresh: bool = False) -> dict[str, Any]:
    """Return the local model catalog, reusing a short-lived in-process snapshot."""
    global _MODEL_CATALOG_CACHE
    with _MODEL_CATALOG_CACHE_LOCK:
        now = time.monotonic()
        if not refresh and _MODEL_CATALOG_CACHE is not None:
            cached_at, cached_result = _MODEL_CATALOG_CACHE
            if now - cached_at < MODEL_CATALOG_CACHE_SECONDS:
                result = copy.deepcopy(cached_result)
                result["refreshed"] = False
                result["cached"] = True
                return result

        result = _load_model_catalog_uncached(refresh)
        _MODEL_CATALOG_CACHE = (time.monotonic(), copy.deepcopy(result))
        result["cached"] = False
        return result


def _load_model_catalog_uncached(refresh: bool = False) -> dict[str, Any]:
    executable = shutil.which("codex")
    if executable:
        command = [executable, "debug", "models"]
        if not refresh:
            command.append("--bundled")
        try:
            result = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=15,
            )
            if result.returncode == 0:
                parsed = json.loads(result.stdout)
                models = []
                for item in parsed.get("models", []):
                    if not isinstance(item, dict) or not isinstance(item.get("slug"), str):
                        continue
                    model_id = item["slug"]
                    visibility = item.get("visibility")
                    if model_id in NEVER_PICK_MODEL_IDS:
                        continue
                    if visibility != "list" and not (
                        visibility is None and model_id in FALLBACK_VISIBLE_MODEL_IDS
                    ):
                        continue
                    reasoning = [
                        entry.get("effort")
                        for entry in item.get("supported_reasoning_levels", [])
                        if isinstance(entry, dict) and entry.get("effort") in REASONING_EFFORTS
                    ]
                    service_tiers = [
                        {
                            "id": entry.get("id"),
                            "name": entry.get("name"),
                        }
                        for entry in item.get("service_tiers", [])
                        if isinstance(entry, dict)
                        and isinstance(entry.get("id"), str)
                        and isinstance(entry.get("name"), str)
                    ]
                    models.append(
                        {
                            "id": model_id,
                            "label": item.get("display_name") or model_id,
                            "description": item.get("description", ""),
                            "defaultReasoningEffort": item.get("default_reasoning_level"),
                            "reasoningEfforts": reasoning,
                            "contextWindow": item.get("context_window"),
                            "maxContextWindow": item.get("max_context_window"),
                            "autoCompactPercent": DEFAULT_AUTO_COMPACT_PERCENT,
                            "speedTiers": [
                                tier
                                for tier in item.get("additional_speed_tiers", [])
                                if isinstance(tier, str) and re.fullmatch(r"[a-z][a-z0-9_-]{0,31}", tier)
                            ],
                            "serviceTiers": service_tiers,
                        }
                    )
                if models:
                    return {
                        "ok": True,
                        "source": "Codex CLI model catalog",
                        "refreshed": refresh,
                        "models": models,
                    }
        except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
            pass

    try:
        fallback = json.loads(FALLBACK_CATALOG.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigError(f"Could not read the bundled fallback model catalog: {exc}") from exc
    return {
        "ok": True,
        "source": fallback.get("source", "Bundled fallback catalog"),
        "asOf": fallback.get("asOf"),
        "refreshed": False,
        "warning": "Codex CLI model catalog was unavailable; this bundled fallback may be stale.",
        "models": fallback.get("models", []),
    }


def normalize_settings(settings: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(settings, Mapping):
        raise ConfigError("settings must be an object.")
    values: dict[str, Any] = {}
    remove: set[str] = set()
    seen: set[str] = set()
    for input_name, value in settings.items():
        if input_name not in SETTING_ALIASES:
            raise ConfigError(f"Unsupported setting: {input_name}")
        field = SETTING_ALIASES[input_name]
        if field in seen:
            raise ConfigError(f"Provide only one alias for {field}.")
        seen.add(field)
        if input_name == "speed":
            if value == "standard":
                remove.add("service_tier")
            elif value == "fast":
                values["service_tier"] = "fast"
            else:
                raise ConfigError("speed must be standard or fast.")
            continue
        if value is None:
            remove.add(field)
            continue
        if field == "model":
            if not isinstance(value, str) or not MODEL_NAME_RE.fullmatch(value):
                raise ConfigError("model must be a valid non-empty model identifier.")
        elif field == "model_reasoning_effort":
            if value not in REASONING_EFFORTS:
                raise ConfigError(f"reasoning_effort must be one of {', '.join(sorted(REASONING_EFFORTS))}.")
        elif field == "service_tier":
            if not isinstance(value, str) or not re.fullmatch(r"[a-z][a-z0-9_-]{0,31}", value):
                raise ConfigError("service_tier must be a short lowercase tier identifier.")
        elif field in {"model_context_window", "model_auto_compact_token_limit"}:
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ConfigError(f"{input_name} must be a positive integer.")
        values[field] = value
    return {"values": values, "remove": sorted(remove)}


def _current_target_values(
    scope: str,
    target: str,
    project_root: str | None,
    role_name: str | None,
) -> dict[str, Any]:
    resolved = get_resolved_config(
        project_root,
        include_project=(scope == "project"),
        include_roles=bool(role_name),
    )["effective"]
    if role_name:
        return dict(resolved.get("roles", {}).get(role_name, {}).get("settings", {}))
    return dict(resolved.get("main" if target == "main" else "subagents", {}))


def _catalog_model(model_id: str | None, catalog: Mapping[str, Any] | None = None) -> dict[str, Any] | None:
    if not model_id:
        return None
    catalog_data = dict(catalog or load_model_catalog())
    for model in catalog_data.get("models", []):
        if isinstance(model, Mapping) and model.get("id") == model_id:
            return dict(model)
    return None


def validate_settings(
    settings: Mapping[str, Any],
    target: str = "main",
    current_values: Mapping[str, Any] | None = None,
    catalog: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if target not in {"main", "subagents", "role"}:
        raise ConfigError("target must be main, subagents, or role.")
    normalized = normalize_settings(settings)
    current = dict(current_values or {})
    values = normalized["values"]
    removed = set(normalized["remove"])
    warnings: list[str] = []
    errors: list[str] = []

    model_id = values.get("model")
    if model_id is None:
        if target == "subagents":
            model_id = values.get("default_subagent_model") or current.get("agents.default_subagent_model")
        else:
            model_id = current.get("model")
    model = _catalog_model(str(model_id) if model_id else None, catalog)
    effort = values.get("model_reasoning_effort")
    if effort is None and target == "subagents":
        effort = values.get("default_subagent_reasoning_effort")
    if model and effort and effort not in model.get("reasoningEfforts", []):
        errors.append(f"{effort} reasoning effort is not listed for {model.get('label', model_id)}.")
    elif model_id and not model:
        warnings.append("The model is not in the current Codex catalog; it may be a custom-provider model.")

    context_window = values.get("model_context_window", current.get("model_context_window"))
    compact = values.get("model_auto_compact_token_limit", current.get("model_auto_compact_token_limit"))
    if "model_context_window" in removed:
        context_window = None
    if "model_auto_compact_token_limit" in removed:
        compact = None
    maximum = model.get("maxContextWindow") if model else None
    if context_window is not None:
        if isinstance(context_window, bool) or not isinstance(context_window, int) or context_window < 1:
            errors.append("model_context_window must be a positive integer.")
        elif isinstance(maximum, int) and maximum >= MIN_MODEL_CONTEXT_WINDOW and context_window < MIN_MODEL_CONTEXT_WINDOW:
            errors.append(f"model_context_window must be at least {MIN_MODEL_CONTEXT_WINDOW:,} tokens for this model.")
        elif isinstance(maximum, int) and context_window > maximum:
            errors.append(f"model_context_window exceeds this model's Codex limit of {maximum:,} tokens.")
    compact_context = context_window if isinstance(context_window, int) else (model.get("contextWindow") if model else None)
    if compact is not None:
        if isinstance(compact, bool) or not isinstance(compact, int) or compact < 1:
            errors.append("model_auto_compact_token_limit must be a positive integer.")
        if isinstance(compact_context, int) and compact > compact_context * DEFAULT_AUTO_COMPACT_PERCENT // 100:
            errors.append(
                f"model_auto_compact_token_limit cannot exceed {DEFAULT_AUTO_COMPACT_PERCENT}% of the context window."
            )

    speed_is_default = "service_tier" in removed or settings.get("speed") == "standard"
    if speed_is_default and current.get("service_tier") == "fast":
        warnings.append("Standard removes this layer's Fast override; a lower-precedence Fast setting may still apply.")
    if values.get("service_tier") == "fast" and model:
        available = set(model.get("speedTiers", []))
        if "fast" not in available:
            errors.append(f"Fast speed is not listed for {model.get('label', model_id)}.")
    if values.get("service_tier") and values.get("service_tier") != "fast" and model:
        advertised = {
            *model.get("speedTiers", []),
            *(tier.get("id") for tier in model.get("serviceTiers", []) if isinstance(tier, Mapping)),
        }
        if values["service_tier"] not in advertised:
            errors.append("service_tier is not listed in the current Codex catalog for this model.")

    return {
        "ok": not errors,
        "valid": not errors,
        "target": target,
        "normalized": normalized,
        "errors": errors,
        "warnings": warnings,
        "model": model,
        "effectiveValues": {**current, **values},
    }


def _ensure_table(parent: Any, key: str) -> Any:
    value = parent.get(key)
    if value is None:
        value = tomlkit.table()
        parent[key] = value
    if not isinstance(value, Mapping):
        raise ConfigError(f"Cannot write nested setting because {key!r} is not a TOML table.")
    return value


def _set_field(document: Any, target: str, field: str, value: Any) -> None:
    if target == "subagents" and field in {"model", "model_reasoning_effort"}:
        agents = _ensure_table(document, "agents")
        target_field = {
            "model": "default_subagent_model",
            "model_reasoning_effort": "default_subagent_reasoning_effort",
        }[field]
        agents[target_field] = value
    else:
        document[field] = value


def _delete_field(document: Any, target: str, field: str) -> None:
    if target == "subagents" and field in {"model", "model_reasoning_effort"}:
        agents = document.get("agents")
        if isinstance(agents, Mapping):
            target_field = {
                "model": "default_subagent_model",
                "model_reasoning_effort": "default_subagent_reasoning_effort",
            }[field]
            agents.pop(target_field, None)
            if not agents:
                document.pop("agents", None)
    else:
        document.pop(field, None)


def _apply_normalized(document: Any, target: str, normalized: Mapping[str, Any]) -> None:
    for field in normalized.get("remove", []):
        _delete_field(document, target, field)
    for field, value in normalized.get("values", {}).items():
        _set_field(document, target, field, value)


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.is_symlink():
        raise ConfigError(f"Refusing to edit a symlinked configuration file: {path}")
    old_mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else None
    file_descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        if old_mode is not None:
            try:
                os.chmod(temp_path, old_mode)
            except OSError:
                pass
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def _layer_warnings(
    scope: str,
    values: Mapping[str, Any],
    remove: list[str],
    target: str = "main",
) -> list[str]:
    warnings = []
    if scope == "project":
        warnings.append("Codex loads this .codex/config.toml only when the project is trusted.")
    shared = set(values) & SHARED_FIELDS | (set(remove) & SHARED_FIELDS)
    if shared:
        if target == "role":
            warnings.append("These standard config fields apply to this named role through its config_file.")
        else:
            warnings.append(
                "Context, compaction, and service tier are standard config fields at this layer; "
                "they can affect the main agent and other agents inheriting the same layer."
            )
    if "service_tier" in remove:
        warnings.append(
            "Removing service_tier uses the next applicable config layer or model default; "
            "a lower-precedence Fast setting may still apply."
        )
    return warnings


def _profile_warnings(scope: str) -> list[str]:
    if scope != "global":
        return []
    selected = _read_plain(config_path("global")).get("profile")
    if isinstance(selected, str) and selected:
        return [
            f"The selected profile {selected!r} has higher precedence than user-level config.toml and may override this value."
        ]
    return []


def apply_config(
    scope: str,
    target: str,
    settings: Mapping[str, Any],
    project_root: str | None = None,
    catalog: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if scope not in {"global", "project"}:
        raise ConfigError("apply_config accepts only global or project scope.")
    if target not in {"main", "subagents"}:
        raise ConfigError("target must be main or subagents.")
    path = config_path(scope, project_root)
    document, _ = _read_document(path)
    current = _current_target_values(scope, target, project_root, None)
    validation = validate_settings(settings, target, current, catalog)
    if not validation["valid"]:
        raise ConfigError("; ".join(validation["errors"]))
    normalized = validation["normalized"]
    if not normalized["values"] and not normalized["remove"]:
        raise ConfigError("Provide at least one setting to change.")
    _apply_normalized(document, target, normalized)
    content = tomlkit.dumps(document)
    _atomic_write(path, content)
    return {
        "ok": True,
        "scope": scope,
        "target": target,
        "filesWritten": [str(path)],
        "changedSettings": sorted(set(normalized["values"]) | set(normalized["remove"])),
        "settingsWritten": normalized["values"],
        "settingsRemoved": normalized["remove"],
        "warnings": list(dict.fromkeys(
            _layer_warnings(scope, normalized["values"], normalized["remove"], target=target)
            + validation["warnings"]
            + _profile_warnings(scope)
        )),
        "activeSessionChanged": False,
    }


def _role_config_values(
    settings: Mapping[str, Any],
    catalog: Mapping[str, Any] | None,
    current_values: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    normalized = normalize_settings(settings)
    validation = validate_settings(settings, "role", current_values, catalog)
    if not validation["valid"]:
        raise ConfigError("; ".join(validation["errors"]))
    document_values = dict(normalized["values"])
    return {"values": document_values, "remove": normalized["remove"], "warnings": validation["warnings"]}


def apply_agent_role(
    scope: str,
    role_name: str,
    settings: Mapping[str, Any],
    project_root: str | None = None,
    catalog: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if scope not in {"global", "project"}:
        raise ConfigError("Named agent roles can be written only to global or project config.")
    validate_role_name(role_name)
    parent_path = config_path(scope, project_root)
    parent, _ = _read_document(parent_path)
    agents = _ensure_table(parent, "agents")
    role = _ensure_table(agents, role_name)
    current_pointer = role.get("config_file")
    pointer = str(current_pointer) if isinstance(current_pointer, str) else None
    role_path = role_config_path(parent_path, role_name, pointer)
    role_doc, _ = _read_document(role_path)
    current_values = _current_target_values(scope, "role", project_root, role_name)
    normalized = _role_config_values(settings, catalog, current_values)
    if not normalized["values"] and not normalized["remove"]:
        raise ConfigError("Provide at least one setting to change.")
    _apply_normalized(role_doc, "role", normalized)
    relative_pointer = os.path.relpath(role_path, parent_path.parent).replace("\\", "/")
    role["config_file"] = relative_pointer
    _atomic_write(role_path, tomlkit.dumps(role_doc))
    _atomic_write(parent_path, tomlkit.dumps(parent))
    warnings = _layer_warnings(scope, normalized["values"], normalized["remove"], target="role")
    warnings.extend(normalized["warnings"])
    warnings.extend(_profile_warnings(scope))
    return {
        "ok": True,
        "scope": scope,
        "roleName": role_name,
        "filesWritten": [str(parent_path), str(role_path)],
        "changedSettings": sorted(set(normalized["values"]) | set(normalized["remove"])),
        "settingsWritten": normalized["values"],
        "settingsRemoved": normalized["remove"],
        "warnings": warnings,
        "activeSessionChanged": False,
    }


def delete_agent_role(
    scope: str,
    role_name: str,
    project_root: str | None = None,
) -> dict[str, Any]:
    """Remove a named role from one Codex config layer, preserving custom or shared files."""
    if scope not in {"global", "project"}:
        raise ConfigError("Named agent roles can be deleted only from global or project config.")
    validate_role_name(role_name)
    parent_path = config_path(scope, project_root)
    parent, _ = _read_document(parent_path)
    agents = parent.get("agents", {})
    if not isinstance(agents, Mapping):
        raise ConfigError("No named agents are defined in this configuration layer.")
    role = agents.get(role_name)
    if not isinstance(role, Mapping):
        raise ConfigError(f"The {role_name!r} role does not exist in this configuration layer.")

    pointer = role.get("config_file")
    role_path = role_config_path(parent_path, role_name, pointer if isinstance(pointer, str) else None)
    managed_default_path = role_config_path(parent_path, role_name)
    base = parent_path.parent.resolve()
    shared = False
    for other_name, other in agents.items():
        if str(other_name) == role_name or not isinstance(other, Mapping):
            continue
        other_pointer = other.get("config_file")
        if not isinstance(other_pointer, str):
            continue
        candidate = Path(other_pointer)
        if candidate.is_absolute():
            continue
        other_path = (base / candidate).resolve()
        if _is_relative_to(other_path, base) and other_path == role_path:
            shared = True
            break

    remove_file = role_path == managed_default_path and not shared and role_path.is_file()
    if role_path.exists() and role_path.is_symlink():
        raise ConfigError("Refusing to delete a symlinked role configuration file.")
    if role_path.exists() and not role_path.is_file():
        raise ConfigError("The role configuration path is not a regular file.")
    settings_before_removal: dict[str, Any] = {}
    if role_path.is_file():
        try:
            role_config = _read_plain(role_path)
            settings_before_removal = {
                key: value
                for key, value in role_config.items()
                if key in TOML_FIELDS and isinstance(value, (str, int, float, bool))
            }
        except (ConfigError, OSError, UnicodeError):
            # A malformed custom file must not prevent removing its role declaration.
            pass

    agents.pop(role_name, None)
    if not agents:
        parent.pop("agents", None)
    _atomic_write(parent_path, tomlkit.dumps(parent))

    files_deleted: list[str] = []
    warnings: list[str] = []
    preserved_file = None
    if remove_file:
        try:
            role_path.unlink()
            files_deleted.append(str(role_path))
        except OSError:
            warnings.append("The role was removed, but its default config file could not be deleted.")
            preserved_file = str(role_path)
    elif role_path.is_file():
        preserved_file = str(role_path)
        if shared:
            warnings.append("The role config file is shared by another role, so it was kept.")
        else:
            warnings.append("The role uses a custom config_file, so that file was kept.")

    return {
        "ok": True,
        "scope": scope,
        "roleName": role_name,
        "filesWritten": [str(parent_path)],
        "filesDeleted": files_deleted,
        "preservedConfigFile": preserved_file,
        "settingsBeforeRemoval": settings_before_removal,
        "warnings": warnings,
        "activeSessionChanged": False,
    }


def validate_config_request(
    scope: str,
    target: str,
    settings: Mapping[str, Any],
    project_root: str | None = None,
    role_name: str | None = None,
    catalog: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if scope not in {"global", "project"}:
        raise ConfigError("scope must be global or project.")
    if role_name:
        validate_role_name(role_name)
        target = "role"
    if target == "role" and not role_name:
        raise ConfigError("roleName is required when target is role.")
    if target not in {"main", "subagents", "role"}:
        raise ConfigError("target must be main, subagents, or role.")
    current = _current_target_values(scope, target, project_root, role_name)
    result = validate_settings(settings, target, current, catalog)
    if scope == "project":
        config_path(scope, project_root)
    result.update({"scope": scope, "roleName": role_name})
    if scope == "project":
        result["warnings"].append("Codex loads project config only when the project is trusted.")
    result["warnings"].extend(_profile_warnings(scope))
    if target == "role":
        parent_path = config_path(scope, project_root)
        agents = _read_plain(parent_path).get("agents", {})
        role_table = agents.get(role_name, {}) if isinstance(agents, Mapping) else {}
        pointer = role_table.get("config_file") if isinstance(role_table, Mapping) else None
        role_path_config = role_config_path(parent_path, role_name, pointer if isinstance(pointer, str) else None)
        result["configFile"] = str(role_path_config)
    return result


def _candidate_values(
    scope: str,
    target: str,
    normalized: Mapping[str, Any],
    project_root: str | None,
    role_name: str | None,
) -> dict[str, Any]:
    before = _current_target_values(scope, target, project_root, role_name)
    after = dict(before)
    def key_for_layer(field: str) -> str:
        if target == "subagents" and field == "model":
            return "agents.default_subagent_model"
        if target == "subagents" and field == "model_reasoning_effort":
            return "agents.default_subagent_reasoning_effort"
        return field

    for field in normalized["remove"]:
        after.pop(key_for_layer(field), None)
    for field, value in normalized["values"].items():
        after[key_for_layer(field)] = value
    return {"before": before, "after": after}


def _diff_pairs(before: Mapping[str, Any], after: Mapping[str, Any]) -> list[dict[str, Any]]:
    output = []
    for key in sorted(set(before) | set(after)):
        if before.get(key) != after.get(key):
            output.append(
                {
                    "setting": key,
                    "before": before.get(key, "(unset)"),
                    "after": after.get(key, "(unset)"),
                }
            )
    return output


def diff_config_request(
    scope: str,
    target: str,
    settings: Mapping[str, Any],
    project_root: str | None = None,
    role_name: str | None = None,
    catalog: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    validation = validate_config_request(scope, target, settings, project_root, role_name, catalog)
    if not validation["valid"]:
        return {"ok": False, "valid": False, "errors": validation["errors"], "warnings": validation["warnings"]}
    target = "role" if role_name else target
    candidate = _candidate_values(
        scope,
        target,
        validation["normalized"],
        project_root,
        role_name,
    )
    path = config_path(scope, project_root)
    files = [str(path)]
    if role_name:
        files.append(validation["configFile"])
    normalized = validation["normalized"]
    return {
        "ok": True,
        "valid": True,
        "scope": scope,
        "target": target,
        "changes": _diff_pairs(candidate["before"], candidate["after"]),
        "filesAffected": files,
        "writesConfigFiles": True,
        "warnings": list(dict.fromkeys(
            validation["warnings"]
            + _layer_warnings(scope, normalized["values"], normalized["remove"], target=target)
            + _profile_warnings(scope)
        )),
    }


def _normalize_reset_keys(keys: list[str] | None) -> list[str]:
    if not keys:
        return sorted(TOML_FIELDS)
    output = set()
    for key in keys:
        if key == "speed":
            output.add("service_tier")
        elif key in SETTING_ALIASES:
            output.add(SETTING_ALIASES[key])
        else:
            raise ConfigError(f"Unsupported reset setting: {key}")
    return sorted(output)


def reset_override(
    scope: str,
    target: str,
    project_root: str | None = None,
    role_name: str | None = None,
    keys: list[str] | None = None,
) -> dict[str, Any]:
    if scope not in {"global", "project"}:
        raise ConfigError("scope must be global or project.")
    if role_name is None and target not in {"main", "subagents"}:
        raise ConfigError("target must be main or subagents unless roleName is provided.")
    reset_keys = _normalize_reset_keys(keys)
    path = config_path(scope, project_root)
    document, _ = _read_document(path)
    if role_name:
        validate_role_name(role_name)
        agents = document.get("agents", {})
        role = agents.get(role_name, {}) if isinstance(agents, Mapping) else {}
        pointer = role.get("config_file") if isinstance(role, Mapping) else None
        role_path = role_config_path(path, role_name, pointer if isinstance(pointer, str) else None)
        role_doc, _ = _read_document(role_path)
        settings_before_removal = _settings_before_removal(role_doc, "role", reset_keys)
        for field in reset_keys:
            role_doc.pop(field, None)
        removed_reference = False
        if not role_doc:
            if isinstance(role, Mapping):
                role.pop("config_file", None)
                removed_reference = True
                if not role:
                    agents.pop(role_name, None)
                if not agents:
                    document.pop("agents", None)
        files = []
        if role_doc:
            _atomic_write(role_path, tomlkit.dumps(role_doc))
            files.append(str(role_path))
        _atomic_write(path, tomlkit.dumps(document))
        files.append(str(path))
        return {
            "ok": True,
            "scope": scope,
            "roleName": role_name,
            "filesWritten": files,
            "orphanedRoleConfig": str(role_path) if removed_reference else None,
            "removedSettings": reset_keys,
            "settingsBeforeRemoval": settings_before_removal,
            "activeSessionChanged": False,
            "warnings": _layer_warnings(scope, {}, reset_keys, target="role"),
        }

    settings_before_removal = _settings_before_removal(document, target, reset_keys)
    for field in reset_keys:
        _delete_field(document, target, field)
    _atomic_write(path, tomlkit.dumps(document))
    return {
        "ok": True,
        "scope": scope,
        "target": target,
        "filesWritten": [str(path)],
        "removedSettings": reset_keys,
        "settingsBeforeRemoval": settings_before_removal,
        "activeSessionChanged": False,
        "warnings": _layer_warnings(scope, {}, reset_keys),
    }


def render_semantic_diff(before_text: str, after_text: str) -> str:
    """Utility kept for tests; never return full config files from MCP tools."""
    return "".join(
        difflib.unified_diff(
            before_text.splitlines(keepends=True),
            after_text.splitlines(keepends=True),
            fromfile="before",
            tofile="after",
        )
    )
