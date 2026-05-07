"""Tests for skill_manifest domain mapper.

Pattern: skills #1091 — coordinator.domains frontmatter maps to
x-change InsightTier and ToolScope.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "xchange"))

from domain import InsightTier, ToolProvenance
from skill_manifest import map_skill_manifest, SkillDomain


class TestSkillManifestMapper(unittest.TestCase):
    def test_empty_manifest_defaults_to_surface(self):
        mapped = map_skill_manifest("empty-skill", "# No frontmatter\n")
        self.assertEqual(mapped.insight_tier, InsightTier.SURFACE)
        self.assertIsNone(mapped.tool_scope)
        self.assertIn("No coordinator.domains", mapped.rationale)

    def test_yaml_frontmatter_domains(self):
        text = """---
coordinator:
  domains:
    - math
    - reasoning
---
# Skill Body
"""
        mapped = map_skill_manifest("math-skill", text)
        self.assertEqual(len(mapped.domains), 2)
        self.assertEqual(mapped.domains[0].name, "math")
        self.assertEqual(mapped.domains[1].name, "reasoning")
        # Highest tier weighted by confidence: math (STRUCTURAL, conf=1.0) vs reasoning (THEORETICAL, conf=0.5)
        # Score math = 2 + 1.0 = 3.0; Score reasoning = 4 + 0.5 = 4.5 → THEORETICAL wins
        self.assertEqual(mapped.insight_tier, InsightTier.THEORETICAL)
        self.assertIsNotNone(mapped.tool_scope)
        # Tool scope picks highest-confidence domain: math → CALCULATOR
        self.assertEqual(mapped.tool_scope.provenance, ToolProvenance.CALCULATOR)

    def test_inline_domains(self):
        text = """coordinator.domains:
  - coding
  - analysis
"""
        mapped = map_skill_manifest("code-skill", text)
        self.assertEqual(len(mapped.domains), 2)
        self.assertEqual(mapped.domains[0].name, "coding")
        # Highest tier: coding → CAUSAL, analysis → PATTERN → CAUSAL wins
        self.assertEqual(mapped.insight_tier, InsightTier.CAUSAL)

    def test_confidence_decay(self):
        text = """---
coordinator:
  domains:
    - document
    - knowledge
    - search
---
"""
        mapped = map_skill_manifest("doc-skill", text)
        self.assertEqual(len(mapped.domains), 3)
        # First domain confidence = 1.0, last = 0.5
        self.assertAlmostEqual(mapped.domains[0].confidence, 1.0, places=3)
        self.assertAlmostEqual(mapped.domains[-1].confidence, 0.6667, places=3)

    def test_single_domain(self):
        text = """---
coordinator:
  domains:
    - finance
---
"""
        mapped = map_skill_manifest("finance-skill", text)
        self.assertEqual(len(mapped.domains), 1)
        self.assertEqual(mapped.domains[0].confidence, 1.0)
        self.assertEqual(mapped.insight_tier, InsightTier.STRUCTURAL)
        self.assertEqual(mapped.tool_scope.provenance, ToolProvenance.CALCULATOR)

    def test_no_domains_returns_surface(self):
        text = """---
name: my-skill
---
"""
        mapped = map_skill_manifest("bare-skill", text)
        self.assertEqual(mapped.insight_tier, InsightTier.SURFACE)
        self.assertIsNone(mapped.tool_scope)


if __name__ == "__main__":
    unittest.main()
