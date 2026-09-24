# Contributing

Thanks for helping improve Agent Switchboard.

## Before opening an issue

- Check existing issues for duplicates.
- Include the plugin version, Codex version, operating system, and concise reproduction steps.
- Redact local usernames, project paths, configuration values, and logs.

## Development setup

Requirements: Python 3.11+, uv, and Node.js 20+ for rebuilding the bundled UI.

From plugins/agent-switchboard:

    uv sync --locked
    uv run python -m unittest discover -s tests -v
    npm ci
    npm run build:ui

If the UI changes, include the regenerated agent_switchboard/ui_bundle.js in the same change.

## Pull requests

- Keep changes focused and explain the user-visible effect.
- Add or update tests for behavior changes.
- Run the relevant Python tests and UI build.
- Never include personal Codex settings, operation logs, virtual environments, or dependency caches.
- For UI changes, include a screenshot when it helps reviewers assess the result.