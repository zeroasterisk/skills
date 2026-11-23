"""Tests for the run_workflow template embedded in the council skill's harness reference."""

import ast
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
    blocks = re.findall(r"```python\n(.*?)```", HARNESS.read_text(encoding="utf-8"), re.DOTALL)
    assert len(blocks) == 1, "expected one python block in jetski-harness.md"
    return blocks[0]


class CouncilTemplateTest(unittest.TestCase):
    def setUp(self):
        self.agents = pathlib.Path(tempfile.mkdtemp())
        self.workspace = pathlib.Path(tempfile.mkdtemp())
        self.cwd = os.getcwd()
        os.chdir(self.workspace)
        src = template_source()
        helpers = src[src.index("READ_ONLY_TOOLS") : src.index("seats = [vet(")]
        helpers = helpers.replace(
            'Path.home() / ".gemini" / "config" / "agents"', f"Path({str(self.agents)!r})"
        )
        self.logs = []
        self.ns = {"Path": pathlib.Path, "re": re, "log": self.logs.append}
        exec(helpers, self.ns)

    def tearDown(self):
        os.chdir(self.cwd)

    def agent(self, name, text, where=None):
        path = (where or self.agents) / f"{name}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def vet(self, **seat):
        return self.ns["vet"]({"label": "L", **seat}, 0)

    def test_template_compiles_with_top_level_await(self):
        compile(template_source(), "template", "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)

    def test_read_only_seat_is_kept_with_its_tier(self):
        self.agent("ro", "---\nname: ro\nmodel: pro  # pinned\ntools:\n  - view_file\n  - grep_search\n---\n")
        seat = self.vet(type_name="ro")
        self.assertEqual((seat["type_name"], seat["tier"]), ("ro", "pro"))

    def test_workspace_agents_dir_is_checked(self):
        self.agent("ws", "---\nname: ws\ntools: [view_file]\n---\n", self.workspace / ".agents/agents")
        self.assertEqual(self.vet(type_name="ws")["type_name"], "ws")

    def test_dashes_inside_frontmatter_do_not_end_it(self):
        self.agent("dash", "---\nname: d\ndescription: a --- b\ntools: [view_file]\n---\n")
        self.assertEqual(self.vet(type_name="dash")["type_name"], "dash")

    def test_unsafe_seats_become_research(self):
        cases = {
            "rw": "---\nname: rw\ntools: [view_file, run_command]\n---\n",
            "mcp": "---\nname: m\ntools: [view_file]\nmcpServers:\n  - name: writer\n---\n",
            "skills": "---\nname: s\ntools: [view_file]\nskills:\n  - skills/x\n---\n",
            "wrapped": "---\nname: w\ntools: [view_file,\n  run_command]\n---\n",
            "notools": "---\nname: n\n---\n",
            "nofm": "no frontmatter\n",
        }
        for name, text in cases.items():
            self.agent(name, text)
        for name in [*cases, "missing", "self", "browser"]:
            with self.subTest(seat=name):
                self.assertEqual(self.vet(type_name=name)["type_name"], "research")

    def test_unverified_seat_runs_only_when_allowed(self):
        seat = self.vet(type_name="missing", allow_unverified=True)
        self.assertEqual(seat["type_name"], "missing")
        self.assertIn("tools unverified", seat["label"])


if __name__ == "__main__":
    unittest.main()
