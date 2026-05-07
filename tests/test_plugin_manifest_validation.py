"""Tests for plugin manifest validation in ingest handlers.

Pattern: claude-plugins-official #1751 — plugin.json missing
'skills' path causes silent discovery failures.
"""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "xchange"))

from glass_adapter import PluginManifestError, validate_plugin_manifest


class TestValidatePluginManifest(unittest.TestCase):
    def test_valid_manifest_with_skills_list(self):
        manifest = {
            "name": "my-plugin",
            "version": "1.0.0",
            "skills": ["skills/math.yaml", "skills/code.yaml"],
        }
        validate_plugin_manifest(manifest)  # should not raise

    def test_valid_manifest_with_skills_string(self):
        manifest = {
            "name": "my-plugin",
            "skills": "skills/",
        }
        validate_plugin_manifest(manifest)  # should not raise

    def test_missing_name_raises(self):
        with self.assertRaises(PluginManifestError) as ctx:
            validate_plugin_manifest({"skills": []})
        self.assertEqual(ctx.exception.field, "name")

    def test_missing_skills_raises(self):
        with self.assertRaises(PluginManifestError) as ctx:
            validate_plugin_manifest({"name": "bad-plugin"})
        self.assertEqual(ctx.exception.field, "skills")
        self.assertIn("skills path", ctx.exception.reason)

    def test_skills_wrong_type_raises(self):
        with self.assertRaises(PluginManifestError) as ctx:
            validate_plugin_manifest({"name": "bad-plugin", "skills": 42})
        self.assertEqual(ctx.exception.field, "skills")

    def test_non_dict_manifest_raises(self):
        with self.assertRaises(PluginManifestError) as ctx:
            validate_plugin_manifest("not-a-dict")
        self.assertIsNone(ctx.exception.field)

    def test_version_wrong_type_raises(self):
        with self.assertRaises(PluginManifestError) as ctx:
            validate_plugin_manifest({"name": "p", "skills": [], "version": 123})
        self.assertEqual(ctx.exception.field, "version")


if __name__ == "__main__":
    unittest.main()
