from __future__ import annotations

import json
from pathlib import Path
import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

from mcp.client import Client
from mcp.client.stdio import StdioServerParameters

from agent_switchboard import server as server_module
from agent_switchboard.server import UI_URI, server

PROJECT_DIR = Path(__file__).resolve().parents[1]


class McpServerTests(unittest.IsolatedAsyncioTestCase):
    async def test_advertises_requested_tools_and_app_resource(self) -> None:
        async with Client(server) as client:
            tool_result = await client.list_tools()
            resource_result = await client.list_resources()
            resource = await client.read_resource(UI_URI)

        names = {tool.name for tool in tool_result.tools}
        expected = {
            "get_resolved_config",
            "get_model_catalog",
            "set_global_config",
            "set_project_config",
            "set_agent_role",
            "delete_agent_role",
            "get_plugin_logs",
            "validate_config",
            "diff_config",
            "reset_override",
            "open_switchboard",
        }
        self.assertTrue(expected.issubset(names))
        self.assertNotIn("set_session_config", names)
        self.assertIn(UI_URI, {str(item.uri) for item in resource_result.resources})
        self.assertEqual(resource.contents[0].mime_type, "text/html;profile=mcp-app")
        self.assertIn("Agent Switchboard", resource.contents[0].text)
        self.assertNotIn("AGENT_SWITCHBOARD_BUNDLE", resource.contents[0].text)
        self.assertNotIn('data-scope="session"', resource.contents[0].text)
        self.assertNotIn("set_session_config", resource.contents[0].text)

    def test_plugin_log_stores_only_safe_operation_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with patch.dict(os.environ, {"CODEX_HOME": temporary}, clear=False):
                server_module._record_log("set_agent_role", "success", "project", "role")
                result = server_module.get_plugin_logs(limit=10)

        self.assertTrue(result["ok"])
        self.assertEqual(len(result["entries"]), 1)
        entry = result["entries"][0]
        self.assertEqual(entry["event"], "set_agent_role")
        self.assertEqual(entry["scope"], "project")
        self.assertEqual(set(entry), {"timestamp", "event", "result", "scope", "target"})

    def test_write_log_includes_paths_and_only_managed_setting_values(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with patch.dict(os.environ, {"CODEX_HOME": temporary}, clear=False):
                server_module._safe_call(
                    lambda: {
                        "ok": True,
                        "filesWritten": ["D:/sample/.codex/config.toml"],
                        "changedSettings": ["model", "service_tier"],
                        "settingsWritten": {"model": "gpt-6-sol", "service_tier": "fast", "api_key": "secret"},
                        "settingsBeforeRemoval": {"model": "gpt-6-luna", "api_key": "do-not-log"},
                    },
                    log_event="set_project_config",
                    log_scope="project",
                    log_target="subagents",
                )
                result = server_module.get_plugin_logs(limit=10)

        entry = result["entries"][0]
        self.assertGreaterEqual(entry["durationMs"], 0)
        self.assertEqual(entry["details"]["filesWritten"], ["D:/sample/.codex/config.toml"])
        self.assertEqual(entry["details"]["settingsWritten"], {"model": "gpt-6-sol", "service_tier": "fast"})
        self.assertEqual(entry["details"]["settingsBeforeRemoval"], {"model": "gpt-6-luna"})
        self.assertNotIn("secret", json.dumps(entry))

    async def test_mcp_tools_return_filtered_catalog_and_open_current_project(self) -> None:
        async with Client(server) as client:
            catalog_result = await client.call_tool("get_model_catalog", {"refresh": False})
            panel_result = await client.call_tool("open_switchboard", {"project_root": f'"{PROJECT_DIR}"'})
            global_panel_result = await client.call_tool("open_switchboard", {})

        catalog_text = json.dumps(catalog_result.structured_content or catalog_result.content)
        panel = panel_result.structured_content or json.loads(panel_result.content[0].text)
        global_panel = global_panel_result.structured_content or json.loads(global_panel_result.content[0].text)
        self.assertNotIn("model_messages", catalog_text)
        self.assertNotIn("base_instructions", catalog_text)
        self.assertEqual(panel["defaultScope"], "project")
        self.assertEqual(panel["defaultTarget"], "subagents")
        self.assertEqual(Path(panel["projectRoot"]), PROJECT_DIR.resolve())
        self.assertEqual(global_panel["defaultScope"], "global")

    async def test_plugin_stdio_command_starts_and_lists_tools(self) -> None:
        import json as json_module

        manifest = json_module.loads((PROJECT_DIR / ".mcp.json").read_text(encoding="utf-8"))
        config = manifest["mcpServers"]["agent-switchboard"]
        self.assertEqual(config.get("cwd"), ".")
        self.assertEqual(config.get("command"), "uv")
        command = shutil.which(config["command"])
        args = config["args"]
        if command is None:
            # The clean worker does not have uv on PATH. Exercise stdio through
            # the active project environment while retaining the manifest check.
            command = sys.executable
            args = ["-m", "agent_switchboard.server"]
        params = StdioServerParameters(
            command=command,
            args=args,
            cwd=PROJECT_DIR / config.get("cwd", "."),
        )
        async with Client(params, read_timeout_seconds=30) as client:
            result = await client.list_tools()

        self.assertNotIn("set_session_config", {tool.name for tool in result.tools})
        self.assertIn("open_switchboard", {tool.name for tool in result.tools})
        self.assertIn("delete_agent_role", {tool.name for tool in result.tools})
        self.assertIn("get_plugin_logs", {tool.name for tool in result.tools})


if __name__ == "__main__":
    unittest.main()
