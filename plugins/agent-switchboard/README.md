# Agent Switchboard: technical guide

Agent Switchboard is a local Codex plugin for configuring agent settings through an interactive panel or MCP tools. It reads and writes Codex TOML files and does not maintain a separate settings database.

For the public installation flow, use the [GitHub marketplace instructions](../../README.md#install). This guide covers configuration behavior, tools, privacy, and development.

## Requirements

- Codex CLI and plugin support
- Python 3.11 or newer
- [uv](https://docs.astral.sh/uv/)
- Node.js 20 or newer only when rebuilding the UI

The repository includes the built UI bundle. Codex starts the local MCP server from `.mcp.json`; the server communicates with Codex over standard input and output.

## Configuration scopes

| Scope | File | Notes |
| --- | --- | --- |
| Global | `$CODEX_HOME/config.toml` | User-level defaults across projects |
| Project | `<project>/.codex/config.toml` | Project overrides; Codex reads them only for trusted projects |
| Named role | The TOML file referenced by `agents.<name>.config_file` | Role-specific model and reasoning settings |

The panel can configure the default subagent and named roles. Codex provides model and reasoning settings for the default subagent. `service_tier`, `model_context_window`, and `model_auto_compact_token_limit` are broader settings at their configuration layer and can affect agents that inherit them.

Main-agent model, reasoning, and speed are selected in Codex’s model picker. Agent Switchboard can manage supported context-window and compaction settings for the main agent.

Codex determines the effective value from its configuration precedence. Command-line options and higher-precedence settings can override TOML values. Project configuration applies only to trusted projects.

## Model catalog and controls

The plugin reads model names, reasoning levels, context limits, and speed tiers from the model catalog available to the local Codex CLI. The catalog is cached in the plugin process for five minutes. Select **Refresh model catalog** to read it again immediately.

The panel can configure:

- Model and reasoning effort for the default subagent and named roles, where supported by the model catalog.
- `service_tier` for a supported speed tier such as `fast`. Removing a Fast override at one layer does not remove a value inherited from another applicable layer.
- `model_context_window` and `model_auto_compact_token_limit` at the selected configuration layer.

The suggested compaction threshold is 90% of the context window. It is a starting value; users can change it.

## Review and write behavior

Before writing, Agent Switchboard validates supported values and presents a semantic diff of managed settings. The user confirms the change before it is applied. TOML updates preserve existing comments and unrelated fields and use atomic file replacement.

When editing a named role, the plugin loads its current values and uses the same preview and confirmation flow. Deleting a role requires confirmation. Deletion also removes the role’s default TOML file; custom files and files shared by other roles are retained.

## MCP tools

| Tool | Purpose |
| --- | --- |
| `open_switchboard` | Open the configuration panel |
| `get_resolved_config` | Read managed values across applicable global, profile, project, and role layers |
| `get_model_catalog` | Read available models, reasoning levels, context limits, and speed tiers |
| `set_global_config` | Update selected settings in `$CODEX_HOME/config.toml` |
| `set_project_config` | Update selected settings in a project’s `.codex/config.toml` |
| `set_agent_role` | Update a named role reference and its role TOML file |
| `validate_config` | Check managed fields, model support, and numeric ranges |
| `diff_config` | Preview semantic changes without returning unrelated or authentication settings |
| `reset_override` | Remove selected overrides so Codex can inherit the next applicable value |
| `delete_agent_role` | Delete a named role after confirmation |
| `get_plugin_logs` | Read local Agent Switchboard operation history |

## Natural-language examples

- “Open Agent Switchboard and show the current project’s subagent settings.”
- “Set this project’s default subagent to GPT-6 Luna with high reasoning and Fast. Show a diff first.”
- “Set the global Reviewer role to GPT-6 Sol with high reasoning, keeping the other settings.”
- “Clear the Worker model override for this project.”

## Data and privacy

The plugin runs locally. It reads and writes the Codex TOML file selected for an operation. The panel reads the main configuration at startup; role files are read when the role manager is opened or a role is edited.

Operation history is stored at `$CODEX_HOME/logs/agent-switchboard.jsonl`. It can include local file paths and values for settings managed by the plugin. There is no built-in telemetry or hosted service. Read the repository’s [PRIVACY.md](../../PRIVACY.md) before sharing logs. Do not attach a complete Codex configuration or unredacted logs to a public issue.

## Advanced: local development installation

For plugin development, install the repository checkout as a Git-backed marketplace using the public commands in the [root README](../../README.md#install). Codex reads the plugin from the repository, so changes can be reviewed against the working tree. Start a new Codex task after installing or refreshing the plugin.

For a manually assembled personal marketplace, copy this plugin directory into `%USERPROFILE%\.agents\plugins\agent-switchboard`, then add an entry like this to `%USERPROFILE%\.agents\plugins\marketplace.json`. Keep the marketplace name and other entries already present in that file:

```json
{
  "name": "agent-switchboard",
  "source": {
    "source": "local",
    "path": "./agent-switchboard"
  },
  "policy": {
    "installation": "AVAILABLE",
    "authentication": "ON_INSTALL"
  },
  "category": "Developer Tools"
}
```

This path is intended for local development; use the GitHub marketplace for public installation.

## Build and verify

From this directory:

```bash
uv sync --locked
uv run python -m unittest discover -s tests -v
npm ci
npm run build:ui
```

The Node.js build regenerates `agent_switchboard/ui_bundle.js` from `ui/src/app.js`. Tests use temporary directories and do not change a real `$CODEX_HOME` or project configuration.

To run the plugin validator when installed with Codex:

```powershell
python "$env:USERPROFILE\.codex\skills\.system\plugin-creator\scripts\validate_plugin.py" .
```

## Repository layout

```text
.agents/plugins/marketplace.json       GitHub-backed marketplace definition
plugins/agent-switchboard/             Installable plugin source
.github/workflows/ci.yml               Build and test checks
```
