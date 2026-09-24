---
name: agent-switchboard
description: Configure Codex main agents, default subagents, named agent roles, models, reasoning effort, speed, context windows, and compaction thresholds through official Codex configuration.
---

# Agent Switchboard

Use the Agent Switchboard MCP tools when the user asks to inspect, change, compare, or reset Codex model and agent configuration.

## Rules

- Treat Codex TOML configuration as the only persistent source of truth. Never create or use a second settings store.
- Use get_resolved_config to inspect the selected layers. Return only the fields managed by this plugin; do not expose unrelated Codex settings.
- Use get_model_catalog to populate model and capability choices. Do not infer model support when the catalog does not advertise it.
- For a requested change, call validate_config and diff_config before writing. A clear direct instruction to change settings authorizes the requested write. Do not change unrelated fields.
- Write global values with set_global_config, project values with set_project_config, and named roles with set_agent_role.
- When opening the visual panel from a project-scoped Codex task, pass the active project root as an absolute `project_root` argument to `open_switchboard`. The panel opens on that project and the default subagents. Never infer a project path from the plugin's working directory. In a projectless task, open the global scope.
- Use reset_override only for the user's selected layer. Removing a project value makes Codex inherit the next applicable layer.
- Inspect named roles under `roleLayers.global` and `roleLayers.project` in `get_resolved_config`. Use `delete_agent_role` only for the role and scope the user selected; custom or shared role config files are preserved.
- Use `get_plugin_logs` when the user asks to inspect recent Agent Switchboard operations. Logs stay under `CODEX_HOME` and may include configuration file paths plus the setting fields and values managed by this plugin. Do not claim logs omit paths or values, and do not expose unrelated Codex settings.
- The visual panel manages persistent global and project settings; it does not provide one-session CLI overrides.
- Explain that model, reasoning effort, and service tier are saved for subsequent requests. Context and compaction are read when a new agent starts.
- A project .codex/config.toml is loaded only when Codex trusts that project. Do not report project settings as active when trust has not been established.
- service_tier=fast requests the Fast tier. Standard removes the override in the selected layer; a lower-precedence Fast value may still apply.
- The Codex default-subagent settings expose dedicated model and reasoning fields. Explain when service tier, context, and compaction values are shared at the selected config layer.

## Visual workflow

When the user asks to choose settings, open the visual panel with open_switchboard. In a project-scoped task, pass the active absolute project root so the panel opens on the current project. The default target is the subagents. Let the user choose project or global scope, main agent, default subagents, or a named role. In the named-role view, use the role manager to inspect existing project and global roles; edit through the normal preview flow and confirm a deletion in the UI. For the main agent, direct model, reasoning, and speed changes to the native composer model picker; use the panel for context and compaction. Preview the semantic changes before applying them.

## Natural-language workflow

For a direct configuration request:

1. Read the current resolved settings and model catalog.
2. Resolve the exact scope, target, role, project root, and requested values from the conversation. Accept quoted absolute paths after removing one matching pair of surrounding quotes.
3. Validate the candidate settings and preview the changed fields.
4. Apply only the requested update with the scope-specific setter.
5. Report the file path, values changed, inherited values, and activation boundary.
