"""Tests for sync.py: exclusions, materialized plugins, managed-link checks, dry-run.

Hermetic: every test builds a tiny fake repo and a temporary HOME. The CLI is
exercised by running a copy of sync.py inside the fake repo (so REGISTRY_DIR is
the fake repo) with HOME pointing at the temp dir. Stdlib only, no network.
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SYNC_PY = REPO_ROOT / "sync.py"


def load_sync_module():
    spec = importlib.util.spec_from_file_location("sync_under_test", SYNC_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write(path: Path, text: str = "") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def make_skill(path: Path, name: str | None = None) -> None:
    name = name or path.name
    write(path / "SKILL.md", f"---\nname: {name}\ndescription: test skill {name}\n---\nbody\n")


def snapshot(*roots: Path) -> dict[str, tuple]:
    """Record every path (without following symlinks) with enough state to detect changes."""
    snap: dict[str, tuple] = {}
    for root in roots:
        for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
            for n in dirnames + filenames:
                p = Path(dirpath) / n
                st = p.lstat()
                target = os.readlink(p) if p.is_symlink() else None
                snap[str(p)] = (st.st_mode, st.st_ino, st.st_mtime_ns, st.st_size, target)
    return snap


class FakeEnv(unittest.TestCase):
    """Fake repo (plugins p1, p2 + plain source) and temp HOME."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name).resolve()
        self.repo = self.tmp / "repo"
        self.home = self.tmp / "home"
        self.plugins_dir = self.home / ".gemini/config/plugins"
        self.skills_dir = self.home / ".gemini/config/skills"
        self.home.mkdir()
        self.repo.mkdir()
        shutil.copy(SYNC_PY, self.repo / "sync.py")

        write(
            self.repo / "registry.toml",
            """
[targets]
cloudcode_config = ""
local_catalog_dir = "~/.config/skills-sync"

[agents.jetski]
enabled = true
kind = "jetski"
tiers = ["zeroasterisk"]
skills_dir = "~/.gemini/config/skills"
plugins_dir = "~/.gemini/config/plugins"

[agents.cloudcode]
enabled = false

[[source]]
name = "fake/plugins"
tier = "zeroasterisk"
path = "plugins"

[[source]]
name = "fake/plain"
tier = "zeroasterisk"
path = "plain"
""",
        )
        p1 = self.repo / "plugins/p1"
        write(p1 / "plugin.json", "{}")
        write(p1 / "README.md", "p1")
        write(p1 / "hooks.json", "{}")
        write(p1 / "agents/x.md", "agent")
        make_skill(p1 / "skills/a")
        make_skill(p1 / "skills/b")
        p2 = self.repo / "plugins/p2"
        write(p2 / "plugin.json", "{}")
        make_skill(p2 / "skills/c")
        # Non-plugin source: a skill whose dir is named like a plugin, and a category dir.
        make_skill(self.repo / "plain/p1")
        make_skill(self.repo / "plain/cat/other")

    def set_local(self, **jetski_cfg: list[str]) -> None:
        lines = ["[agents.jetski]"]
        for k, v in jetski_cfg.items():
            lines.append(f"{k} = {v!r}".replace("'", '"'))
        write(self.home / ".config/skills-sync/local.toml", "\n".join(lines) + "\n")

    def run_sync(self, *args: str) -> str:
        env = dict(os.environ, HOME=str(self.home))
        proc = subprocess.run(
            [sys.executable, str(self.repo / "sync.py"), *args],
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        return proc.stdout + proc.stderr


class TierReportTest(FakeEnv):
    def jetski_count(self, out: str) -> int:
        line = next(l for l in out.splitlines() if l.strip().startswith("- jetski"))
        return int(line.split("->")[1].split()[0])

    def test_list_tiers_honors_excludes(self) -> None:
        self.assertEqual(self.jetski_count(self.run_sync("--list-tiers")), 5)
        self.set_local(exclude_skills=["a"])
        self.assertEqual(self.jetski_count(self.run_sync("--list-tiers")), 4)
        self.set_local(exclude_plugins=["p1"])
        # p1/a, p1/b excluded; plain "p1" skill is not a plugin and stays.
        self.assertEqual(self.jetski_count(self.run_sync("--list-tiers")), 3)

    def test_print_tier_report_passes_agent_cfg(self) -> None:
        sync = load_sync_module()
        source = {"name": "fake/plugins", "path": str(self.repo / "plugins"), "tier": "zeroasterisk"}
        sync.VERBOSE = False
        skills = sync.discover(source, {})
        self.assertEqual(len(skills), 3)
        import contextlib
        import io

        buf = io.StringIO()
        cfg = {"jetski": {"enabled": True, "tiers": ["zeroasterisk"], "exclude_skills": ["c"]}}
        with contextlib.redirect_stdout(buf):
            sync.print_tier_report(skills, cfg)
        self.assertIn("-> 2 skill(s)", buf.getvalue())


class MaterializedPluginTest(FakeEnv):
    def test_second_sync_is_noop(self) -> None:
        self.set_local(exclude_skills=["a"])
        first = self.run_sync()
        self.assertIn("linked plugin.json", first)
        p1 = self.plugins_dir / "p1"
        self.assertTrue(p1.is_dir() and not p1.is_symlink())
        self.assertTrue((p1 / "plugin.json").is_symlink())
        self.assertTrue((p1 / "skills/b").is_symlink())
        self.assertFalse((p1 / "skills/a").exists())
        self.assertTrue((self.plugins_dir / "p2").is_symlink())

        # Catalogs under ~/.config are rewritten every run; only compare the link dirs.
        before = snapshot(self.home / ".gemini")
        second = self.run_sync()
        self.assertNotIn(": linked ", second)
        self.assertNotIn("removed", second)
        self.assertEqual(before, snapshot(self.home / ".gemini"))

    def test_all_skills_excluded_skips_plugin(self) -> None:
        self.set_local(exclude_skills=["a"])
        self.run_sync()
        self.assertTrue((self.plugins_dir / "p1").is_dir())
        self.set_local(exclude_skills=["a", "b"])
        self.run_sync()
        self.assertFalse(os.path.lexists(self.plugins_dir / "p1"))
        self.assertTrue((self.plugins_dir / "p2").is_symlink())

    def test_restores_plain_symlink_when_exclusions_removed(self) -> None:
        self.set_local(exclude_skills=["a"])
        self.run_sync()
        self.set_local(exclude_skills=[])
        self.run_sync()
        self.assertTrue((self.plugins_dir / "p1").is_symlink())


class ManagedLinkTest(FakeEnv):
    def test_prefix_boundary(self) -> None:
        sync = load_sync_module()
        root = self.tmp / "managed"
        evil = self.tmp / "managed-evil"
        (root / "x").mkdir(parents=True)
        (evil / "x").mkdir(parents=True)
        links = self.tmp / "links"
        links.mkdir()
        (links / "good").symlink_to(root / "x")
        (links / "evil").symlink_to(evil / "x")
        sync.MANAGED_WORKSPACE_ROOTS[:] = [str(root)]
        self.assertTrue(sync.is_managed_link(links / "good"))
        self.assertFalse(sync.is_managed_link(links / "evil"))
        self.assertTrue(sync.is_managed_link(links / "evil", [str(evil)]))


class ExcludePluginsScopeTest(FakeEnv):
    def test_only_real_plugins_match(self) -> None:
        sync = load_sync_module()
        skills = []
        for src in ("plugins", "plain"):
            source = {"name": src, "path": str(self.repo / src), "tier": "zeroasterisk"}
            skills += sync.discover(source, {})
        cfg = {"exclude_plugins": ["p1", "cat"]}
        kept = {s["rel"] for s in sync.filter_skills_for_agent(skills, "jetski", ["zeroasterisk"], cfg)}
        self.assertEqual(kept, {"p2/skills/c", "p1", "cat/other"})
        by_rel = {s["rel"]: s for s in skills}
        self.assertEqual(sync.plugin_name_for_skill(by_rel["p1/skills/a"]), "p1")
        self.assertIsNone(sync.plugin_name_for_skill(by_rel["p1"]))
        self.assertIsNone(sync.plugin_name_for_skill(by_rel["cat/other"]))


class DryRunTest(FakeEnv):
    def test_fresh_dry_run_changes_nothing(self) -> None:
        self.set_local(exclude_skills=["a"])
        before = snapshot(self.tmp)
        out = self.run_sync("--dry-run")
        self.assertIn("[dry-run]", out)
        self.assertEqual(before, snapshot(self.tmp))
        self.assertFalse(self.plugins_dir.exists())

    def test_dry_run_with_symlinked_plugin_reports_without_walking(self) -> None:
        self.run_sync()  # p1 is now a plain dir symlink into the repo
        self.assertTrue((self.plugins_dir / "p1").is_symlink())
        self.set_local(exclude_skills=["a"])
        before = snapshot(self.tmp)
        out = self.run_sync("--dry-run")
        self.assertEqual(before, snapshot(self.tmp))
        self.assertIn("would replace symlink", out)
        self.assertIn(f"would symlink {self.plugins_dir / 'p1' / 'plugin.json'}", out)
        self.assertIn(f"would symlink {self.plugins_dir / 'p1' / 'skills' / 'b'}", out)
        self.assertNotIn(f"{self.plugins_dir / 'p1' / 'skills' / 'a'}", out)


if __name__ == "__main__":
    unittest.main()
