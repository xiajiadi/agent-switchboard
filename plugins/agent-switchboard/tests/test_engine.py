from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import tomlkit

from agent_switchboard import engine


CATALOG = {
    "models": [
        {
            "id": "gpt-6-sol",
            "label": "GPT-6 Sol",
            "reasoningEfforts": ["low", "medium", "high"],
            "contextWindow": 256_000,
            "maxContextWindow": 500_000,
            "speedTiers": ["fast"],
            "serviceTiers": [{"id": "priority", "name": "Fast"}],
        },
        {
            "id": "gpt-6-luna",
            "label": "GPT-6 Luna",
            "reasoningEfforts": ["low", "medium"],
            "contextWindow": 128_000,
            "maxContextWindow": 300_000,
            "speedTiers": [],
            "serviceTiers": [],
        },
    ]
}


class EngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.codex_home = self.root / "user-codex"
        self.codex_home.mkdir()
        self.project = self.root / "sample-project"
        self.project.mkdir()
        self.env_patch = patch.dict(os.environ, {"CODEX_HOME": str(self.codex_home)}, clear=False)
        self.env_patch.start()
        self.catalog_patch = patch.object(engine, "load_model_catalog", return_value=CATALOG)
        self.catalog_patch.start()

    def tearDown(self) -> None:
        self.catalog_patch.stop()
        self.env_patch.stop()
        self.temp.cleanup()

    def test_global_update_preserves_comments_and_unmanaged_values(self) -> None:
        config = self.codex_home / "config.toml"
        config.write_text(
            "# keep this note\napi_key_hint = \"do-not-return\"\nmodel = \"gpt-6-luna\"\n",
            encoding="utf-8",
        )

        result = engine.apply_config(
            "global",
            "main",
            {"model": "gpt-6-sol", "reasoning_effort": "high", "speed": "fast"},
            catalog=CATALOG,
        )
        written = config.read_text(encoding="utf-8")
        parsed = tomlkit.parse(written)

        self.assertEqual(result["ok"], True)
        self.assertIn("# keep this note", written)
        self.assertEqual(parsed["model"], "gpt-6-sol")
        self.assertEqual(parsed["model_reasoning_effort"], "high")
        self.assertEqual(parsed["service_tier"], "fast")
        self.assertEqual(parsed["api_key_hint"], "do-not-return")
        self.assertNotIn("do-not-return", json.dumps(result))
        self.assertEqual(result["activeSessionChanged"], False)

    def test_project_subagent_settings_use_official_agents_fields(self) -> None:
        result = engine.apply_config(
            "project",
            "subagents",
            {
                "model": "gpt-6-luna",
                "reasoning_effort": "medium",
                "model_context_window": 300_000,
                "model_auto_compact_token_limit": 180_000,
            },
            str(self.project),
            CATALOG,
        )
        config = tomlkit.parse((self.project / ".codex" / "config.toml").read_text(encoding="utf-8"))

        self.assertEqual(config["agents"]["default_subagent_model"], "gpt-6-luna")
        self.assertEqual(config["agents"]["default_subagent_reasoning_effort"], "medium")
        self.assertEqual(config["model_context_window"], 300_000)
        self.assertEqual(config["model_auto_compact_token_limit"], 180_000)
        self.assertEqual(result["scope"], "project")
        self.assertIn("trusted", " ".join(result["warnings"]))

    def test_role_update_creates_official_config_file_reference(self) -> None:
        result = engine.apply_agent_role(
            "project",
            "reviewer",
            {
                "model": "gpt-6-sol",
                "reasoning_effort": "high",
                "model_context_window": 300_000,
                "model_auto_compact_token_limit": 250_000,
            },
            str(self.project),
            CATALOG,
        )
        parent = tomlkit.parse((self.project / ".codex" / "config.toml").read_text(encoding="utf-8"))
        role_path = self.project / ".codex" / "agents" / "roles" / "reviewer.toml"
        role = tomlkit.parse(role_path.read_text(encoding="utf-8"))

        self.assertEqual(parent["agents"]["reviewer"]["config_file"], "agents/roles/reviewer.toml")
        self.assertEqual(role["model"], "gpt-6-sol")
        self.assertEqual(role["model_reasoning_effort"], "high")
        self.assertEqual(result["filesWritten"], [str(self.project / ".codex" / "config.toml"), str(role_path)])

    def test_delete_project_role_removes_its_default_role_file(self) -> None:
        config_path = self.project / ".codex" / "config.toml"
        config_path.parent.mkdir()
        config_path.write_text(
            '[agents]\ndefault_subagent_model = "gpt-6-sol"\n'
            '[agents.reviewer]\nconfig_file = "agents/roles/reviewer.toml"\n',
            encoding="utf-8",
        )
        role_path = config_path.parent / "agents" / "roles" / "reviewer.toml"
        role_path.parent.mkdir(parents=True)
        role_path.write_text('model = "gpt-6-sol"\n', encoding="utf-8")

        result = engine.delete_agent_role("project", "reviewer", str(self.project))
        parent = tomlkit.parse(config_path.read_text(encoding="utf-8"))

        self.assertEqual(result["ok"], True)
        self.assertEqual(result["filesDeleted"], [str(role_path)])
        self.assertEqual(result["settingsBeforeRemoval"], {"model": "gpt-6-sol"})
        self.assertFalse(role_path.exists())
        self.assertNotIn("reviewer", parent["agents"])
        self.assertEqual(parent["agents"]["default_subagent_model"], "gpt-6-sol")

    def test_delete_global_role_removes_its_default_role_file(self) -> None:
        config_path = self.codex_home / "config.toml"
        config_path.write_text(
            '[agents.audit]\nconfig_file = "agents/roles/audit.toml"\n',
            encoding="utf-8",
        )
        role_path = self.codex_home / "agents" / "roles" / "audit.toml"
        role_path.parent.mkdir(parents=True)
        role_path.write_text('model_reasoning_effort = "high"\n', encoding="utf-8")

        result = engine.delete_agent_role("global", "audit")

        self.assertEqual(result["ok"], True)
        self.assertEqual(result["filesDeleted"], [str(role_path)])
        self.assertEqual(result["settingsBeforeRemoval"], {"model_reasoning_effort": "high"})
        self.assertFalse(role_path.exists())
        self.assertFalse(tomlkit.parse(config_path.read_text(encoding="utf-8")).get("agents"))

    def test_delete_role_preserves_custom_and_shared_role_files(self) -> None:
        config_path = self.project / ".codex" / "config.toml"
        config_path.parent.mkdir()
        config_path.write_text(
            '[agents.reviewer]\nconfig_file = "custom/reviewer.toml"\n'
            '[agents.worker]\nconfig_file = "agents/roles/shared.toml"\n'
            '[agents.helper]\nconfig_file = "agents/roles/shared.toml"\n',
            encoding="utf-8",
        )
        custom_path = config_path.parent / "custom" / "reviewer.toml"
        shared_path = config_path.parent / "agents" / "roles" / "shared.toml"
        custom_path.parent.mkdir(parents=True)
        shared_path.parent.mkdir(parents=True)
        custom_path.write_text('model = "gpt-6-sol"\n', encoding="utf-8")
        shared_path.write_text('model = "gpt-6-luna"\n', encoding="utf-8")

        custom_result = engine.delete_agent_role("project", "reviewer", str(self.project))
        shared_result = engine.delete_agent_role("project", "worker", str(self.project))

        self.assertEqual(custom_result["preservedConfigFile"], str(custom_path))
        self.assertTrue(custom_path.exists())
        self.assertEqual(shared_result["preservedConfigFile"], str(shared_path))
        self.assertTrue(shared_path.exists())
        self.assertTrue(any("shared" in warning for warning in shared_result["warnings"]))

    def test_delete_role_keeps_malformed_custom_file_without_blocking_declaration_removal(self) -> None:
        config_path = self.project / ".codex" / "config.toml"
        config_path.parent.mkdir()
        config_path.write_text(
            '[agents.reviewer]\nconfig_file = "custom/reviewer.toml"\n',
            encoding="utf-8",
        )
        custom_path = config_path.parent / "custom" / "reviewer.toml"
        custom_path.parent.mkdir()
        custom_path.write_text("this is not valid TOML = ]\n", encoding="utf-8")

        result = engine.delete_agent_role("project", "reviewer", str(self.project))

        self.assertEqual(result["ok"], True)
        self.assertEqual(result["preservedConfigFile"], str(custom_path))
        self.assertTrue(custom_path.exists())
        self.assertEqual(tomlkit.parse(config_path.read_text(encoding="utf-8")).get("agents"), None)

    def test_role_name_and_role_path_traversal_are_rejected(self) -> None:
        with self.assertRaises(engine.ConfigError):
            engine.apply_agent_role("project", "../escape", {"model": "gpt-6-sol"}, str(self.project), CATALOG)

        parent = self.project / ".codex" / "config.toml"
        parent.parent.mkdir()
        parent.write_text('[agents.worker]\nconfig_file = \"../../outside.toml\"\n', encoding="utf-8")
        with self.assertRaises(engine.ConfigError):
            engine.role_config_path(parent, "worker", "../../outside.toml")

    def test_role_config_path_rejects_symlink_components_before_resolving_them(self) -> None:
        parent = self.project / ".codex" / "config.toml"
        parent.parent.mkdir()
        parent.write_text("", encoding="utf-8")
        symlink_component = parent.parent / "agents"

        def reports_symlink(path: Path) -> bool:
            return path == symlink_component

        with patch.object(Path, "is_symlink", reports_symlink):
            with self.assertRaises(engine.ConfigError):
                engine.role_config_path(parent, "worker")

    def test_validation_rejects_unsupported_effort_and_invalid_compaction(self) -> None:
        effort = engine.validate_settings(
            {"model": "gpt-6-luna", "reasoning_effort": "high"},
            "main",
            catalog=CATALOG,
        )
        compact = engine.validate_settings(
            {
                "model": "gpt-6-sol",
                "model_context_window": 300_000,
                "model_auto_compact_token_limit": 280_000,
            },
            "main",
            catalog=CATALOG,
        )
        context = engine.validate_settings(
            {"model": "gpt-6-sol", "model_context_window": 600_000},
            "main",
            catalog=CATALOG,
        )

        self.assertFalse(effort["valid"])
        self.assertFalse(compact["valid"])
        self.assertFalse(context["valid"])

    def test_project_reset_removes_only_selected_override(self) -> None:
        config = self.project / ".codex" / "config.toml"
        config.parent.mkdir()
        config.write_text(
            'model = \"gpt-6-sol\"\nmodel_reasoning_effort = \"high\"\napproval_policy = \"on-request\"\n',
            encoding="utf-8",
        )
        result = engine.reset_override("project", "main", str(self.project), keys=["model"])
        parsed = tomlkit.parse(config.read_text(encoding="utf-8"))

        self.assertNotIn("model", parsed)
        self.assertEqual(parsed["model_reasoning_effort"], "high")
        self.assertEqual(parsed["approval_policy"], "on-request")
        self.assertEqual(result["removedSettings"], ["model"])
        self.assertEqual(result["settingsBeforeRemoval"], {"model": "gpt-6-sol"})

    def test_quoted_absolute_project_path_is_normalized(self) -> None:
        quoted = f'  "{self.project}"  '

        self.assertEqual(engine.detect_project_root(quoted), self.project.resolve())

    def test_context_window_minimum_and_codex_compaction_ceiling_are_enforced(self) -> None:
        too_small = engine.validate_settings(
            {"model": "gpt-6-sol", "model_context_window": 255_000},
            "main",
            catalog=CATALOG,
        )
        too_late = engine.validate_settings(
            {
                "model": "gpt-6-sol",
                "model_context_window": 300_000,
                "model_auto_compact_token_limit": 270_001,
            },
            "main",
            catalog=CATALOG,
        )

        self.assertFalse(too_small["valid"])
        self.assertFalse(too_late["valid"])

    def test_model_catalog_filters_non_ui_instructions(self) -> None:
        payload = {
            "models": [
                {
                    "slug": "gpt-6-sol",
                    "display_name": "GPT-6 Sol",
                    "description": "Test model",
                    "default_reasoning_level": "medium",
                    "supported_reasoning_levels": [{"effort": "medium"}],
                    "context_window": 256_000,
                    "max_context_window": 500_000,
                    "additional_speed_tiers": ["fast"],
                    "service_tiers": [{"id": "priority", "name": "Fast"}],
                    "model_messages": {"persistent_instructions": "PRIVATE-CATALOG-INSTRUCTION"},
                }
            ]
        }
        completed = subprocess.CompletedProcess(
            ["codex", "debug", "models", "--bundled"],
            0,
            stdout=json.dumps(payload),
            stderr="",
        )
        self.catalog_patch.stop()
        try:
            with patch("agent_switchboard.engine.shutil.which", return_value="codex"), patch(
                "agent_switchboard.engine.subprocess.run", return_value=completed
            ):
                result = engine.load_model_catalog(refresh=True)
        finally:
            self.catalog_patch.start()

        encoded = json.dumps(result)
        self.assertEqual(result["models"][0]["maxContextWindow"], 500_000)
        self.assertEqual(result["models"][0]["speedTiers"], ["fast"])
        self.assertNotIn("model_messages", encoded)
        self.assertNotIn("PRIVATE-CATALOG-INSTRUCTION", encoded)

    def test_resolved_view_omits_unmanaged_configuration(self) -> None:
        (self.codex_home / "config.toml").write_text(
            'model = \"gpt-6-sol\"\napi_key_hint = \"PRIVATE-VALUE\"\n',
            encoding="utf-8",
        )
        result = engine.get_resolved_config()
        encoded = json.dumps(result)

        self.assertEqual(result["effective"]["main"]["model"], "gpt-6-sol")
        self.assertNotIn("PRIVATE-VALUE", encoded)
        self.assertNotIn("api_key_hint", encoded)

    def test_resolved_config_can_defer_role_files_and_reads_them_once_when_requested(self) -> None:
        config = self.codex_home / "config.toml"
        config.write_text(
            '[agents.reviewer]\nconfig_file = "agents/roles/reviewer.toml"\n',
            encoding="utf-8",
        )
        role_file = self.codex_home / "agents" / "roles" / "reviewer.toml"
        role_file.parent.mkdir(parents=True)
        role_file.write_text('model = "gpt-6-sol"\n', encoding="utf-8")

        with patch.object(engine, "_role_layers", wraps=engine._role_layers) as read_roles:
            quick = engine.get_resolved_config(include_project=False, include_roles=False)
            self.assertEqual(read_roles.call_count, 0)
            full = engine.get_resolved_config(include_project=False, include_roles=True)
            self.assertEqual(read_roles.call_count, 1)

        self.assertEqual(quick["effective"]["roles"], {})
        self.assertEqual(full["effective"]["roles"]["reviewer"]["settings"]["model"], "gpt-6-sol")

    def test_resolved_precedence_includes_profile_and_project_layers(self) -> None:
        (self.codex_home / "config.toml").write_text(
            'profile = \"lean\"\n[agents]\ndefault_subagent_model = \"gpt-6-luna\"\n',
            encoding="utf-8",
        )
        (self.codex_home / "lean.config.toml").write_text(
            '[agents]\ndefault_subagent_model = \"gpt-6-sol\"\n',
            encoding="utf-8",
        )
        project_config = self.project / ".codex" / "config.toml"
        project_config.parent.mkdir()
        project_config.write_text(
            '[agents]\ndefault_subagent_model = \"gpt-6-astra\"\n',
            encoding="utf-8",
        )

        with_project = engine.get_resolved_config(str(self.project))
        global_and_profile = engine.get_resolved_config(include_project=False)

        self.assertEqual(with_project["effective"]["subagents"]["agents.default_subagent_model"], "gpt-6-astra")
        self.assertEqual(global_and_profile["effective"]["subagents"]["agents.default_subagent_model"], "gpt-6-sol")
        self.assertEqual(global_and_profile["selectedProfile"], "lean")

    def test_named_role_resolution_includes_inherited_defaults(self) -> None:
        (self.codex_home / "config.toml").write_text(
            "model_context_window = 300000\nmodel_auto_compact_token_limit = 260000\n"
            '[agents]\ndefault_subagent_model = \"gpt-6-luna\"\n'
            'default_subagent_reasoning_effort = \"medium\"\n'
            '[agents.reviewer]\nconfig_file = \"agents/roles/reviewer.toml\"\n',
            encoding="utf-8",
        )
        role_path = self.codex_home / "agents" / "roles" / "reviewer.toml"
        role_path.parent.mkdir(parents=True)
        role_path.write_text(
            'model = \"gpt-6-sol\"\nmodel_reasoning_effort = \"high\"\n',
            encoding="utf-8",
        )

        result = engine.get_resolved_config(include_project=False)
        role = result["effective"]["roles"]["reviewer"]["settings"]

        self.assertEqual(role["model"], "gpt-6-sol")
        self.assertEqual(role["model_reasoning_effort"], "high")
        self.assertEqual(role["model_context_window"], 300000)
        self.assertEqual(role["model_auto_compact_token_limit"], 260000)


class ModelCatalogCacheTests(unittest.TestCase):
    def test_regular_reads_reuse_catalog_until_explicit_refresh(self) -> None:
        payload = {
            "models": [
                {
                    "slug": "gpt-6-sol",
                    "display_name": "GPT-6 Sol",
                    "visibility": "list",
                    "supported_reasoning_levels": [{"effort": "high"}],
                }
            ]
        }
        completed = subprocess.CompletedProcess(["codex"], 0, stdout=json.dumps(payload), stderr="")
        with patch.object(engine, "_MODEL_CATALOG_CACHE", None), patch(
            "agent_switchboard.engine.shutil.which", return_value="codex"
        ), patch("agent_switchboard.engine.subprocess.run", return_value=completed) as run:
            first = engine.load_model_catalog()
            second = engine.load_model_catalog()
            refreshed = engine.load_model_catalog(refresh=True)

        self.assertEqual(run.call_count, 2)
        self.assertFalse(first["cached"])
        self.assertTrue(second["cached"])
        self.assertTrue(refreshed["refreshed"])
        self.assertFalse(refreshed["cached"])


if __name__ == "__main__":
    unittest.main()
