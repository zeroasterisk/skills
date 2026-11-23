"""Tests for the run_workflow template embedded in the council skill's harness reference."""

import ast
import importlib.util
import os
import pathlib
import re
import tempfile
import unittest

HARNESS = (
    pathlib.Path(__file__).resolve().parent.parent
    / "plugins/council/skills/council/references/jetski-harness.md"
)


def template_source() -> str:
    blocks = re.findall(
        r"```python\n(.*?)```", HARNESS.read_text(encoding="utf-8"), re.DOTALL
    )
    assert len(blocks) == 1, "expected one python block in jetski-harness.md"
    return blocks[0]


class CouncilTemplateTest(unittest.TestCase):
    def setUp(self):
        agents_tmp = tempfile.TemporaryDirectory()
        workspace_tmp = tempfile.TemporaryDirectory()
        self.addCleanup(agents_tmp.cleanup)
        self.addCleanup(workspace_tmp.cleanup)
        self.agents = pathlib.Path(agents_tmp.name)
        self.workspace = pathlib.Path(workspace_tmp.name)
        self.addCleanup(os.chdir, os.getcwd())
        os.chdir(self.workspace)
        src = template_source()
        helpers = src[src.index("READ_ONLY_TOOLS") : src.index("seats = [vet(")]
        home_agents = 'Path.home() / ".gemini" / "config" / "agents"'
        self.assertEqual(
            helpers.count(home_agents),
            1,
            "template moved; the test must not read ~/.gemini",
        )
        helpers = helpers.replace(home_agents, f"Path({str(self.agents)!r})")
        module_file = self.workspace / "council_template.py"
        module_file.write_text(
            "import re\nfrom pathlib import Path\nlogs = []\nlog = logs.append\n"
            + helpers,
            encoding="utf-8",
        )
        spec = importlib.util.spec_from_file_location("council_template", module_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.ns = vars(module)

    def agent(self, name, text, where=None):
        path = (where or self.agents) / f"{name}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def vet(self, **seat):
        return self.ns["vet"]({"label": "L", **seat})

    def test_template_compiles_with_top_level_await(self):
        compile(
            template_source(), "template", "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT
        )

    def test_read_only_seat_is_kept_with_its_tier(self):
        self.agent(
            "ro",
            "---\nname: ro\nmodel: pro  # pinned\ntools:\n  - view_file\n  - grep_search\n---\n",
        )
        seat = self.vet(type_name="ro")
        self.assertEqual((seat["type_name"], seat["tier"]), ("ro", "pro"))

    def test_workspace_agents_dir_is_checked(self):
        self.agent(
            "ws",
            "---\nname: ws\ntools: [view_file]\n---\n",
            self.workspace / ".agents/agents",
        )
        self.assertEqual(self.vet(type_name="ws")["type_name"], "ws")

    def test_dashes_inside_frontmatter_do_not_end_it(self):
        self.agent(
            "dash", "---\nname: d\ndescription: a --- b\ntools: [view_file]\n---\n"
        )
        self.assertEqual(self.vet(type_name="dash")["type_name"], "dash")

    def test_unsafe_seats_become_research(self):
        cases = {
            "rw": "---\nname: rw\ntools: [view_file, run_command]\n---\n",
            "mcp": "---\nname: m\ntools: [view_file]\nmcpServers:\n  - name: writer\n---\n",
            "skills": "---\nname: s\ntools: [view_file]\nskills:\n  - skills/x\n---\n",
            "wrapped": "---\nname: w\ntools: [view_file,\n  run_command]\n---\n",
            "notools": "---\nname: n\n---\n",
            "nofm": "no frontmatter\n",
            "comment": "---\nname: c\ntools:\n  - view_file\n# note\n  - run_command\n---\n",
            "split": "---\nname: s\ntools:\n  - view_file\n  -\n    run_command\n---\n",
        }
        for name, text in cases.items():
            self.agent(name, text)
        for name in [*cases, "missing", "self", "browser"]:
            with self.subTest(seat=name):
                seat = self.vet(type_name=name)
                self.assertEqual(seat["type_name"], "research")
                self.assertEqual(seat["label"], "L; substituted research")

    def test_unverified_seat_runs_only_when_allowed(self):
        seat = self.vet(type_name="missing", allow_unverified=True)
        self.assertEqual(seat["type_name"], "missing")
        self.assertIn("tools unverified", seat["label"])


if __name__ == "__main__":
    unittest.main()
