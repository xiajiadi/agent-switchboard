# Privacy and local data

Agent Switchboard is a local Codex plugin. It does not send configuration files or operation logs to a project-operated server, and it has no built-in telemetry.

## Files it may access

- Global Codex settings: CODEX_HOME/config.toml (or the default Codex home when CODEX_HOME is unset).
- Project settings: <project>/.codex/config.toml, when the user selects a project scope.
- Named role TOML files referenced by Codex agent configuration.
- The local model catalog exposed by the installed Codex CLI.
- Operation history: CODEX_HOME/logs/agent-switchboard.jsonl.

The operation history can contain the target file path, operation result, and before/after values for settings managed by this plugin. It does not record unrelated TOML settings.

## Sharing diagnostics

Before sharing a log or configuration excerpt, remove usernames, project paths, repository names, and any values you do not want to publish. Never share API credentials or a complete Codex configuration file in a public issue.

## Dependencies

First-time installation or development setup may download Python and JavaScript dependencies from their configured package registries. The plugin runtime itself is local.