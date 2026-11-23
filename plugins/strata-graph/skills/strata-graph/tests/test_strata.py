"""Tests for scripts/strata.py and assets/viewer.js (standard library only)."""

import copy
import importlib.util
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
VIEWER_JS = SKILL_DIR / "assets" / "viewer.js"

_spec = importlib.util.spec_from_file_location(
    "strata", SKILL_DIR / "scripts" / "strata.py"
)
strata = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(strata)


def _jsonl(rows):
    return "\n".join(json.dumps(r) for r in rows) + "\n"


def _transcript(output_step):
    return [
        {"type": "USER_INPUT", "content": "<USER_REQUEST>Find the docs</USER_REQUEST>"},
        {
            "type": "PLANNER_RESPONSE",
            "model": "test-model-1",
            "thinking": "Search first.",
            "tool_calls": [{"name": "search_web", "args": {"query": "release notes"}}],
        },
        output_step,
        {"type": "PLANNER_RESPONSE", "content": "Done.", "tool_calls": []},
    ]


def _mutual_cycle_dataset():
    node = {"kind": "stage", "status": "ready", "parent": "r"}
    rel = {
        "label": "next",
        "darkColor": "#60a5fa",
        "lightColor": "#2563eb",
        "dash": "none",
        "category": "flow",
    }
    return {
        "schema": "strata-graph/1",
        "id": "cycle",
        "title": "Cycle",
        "domain": "process",
        "rootId": "r",
        "relations": {"next": rel},
        "nodes": [
            {
                "id": "r",
                "title": "Root",
                "kind": "process",
                "status": "ready",
                "parent": None,
            },
            {"id": "a", "title": "Alpha", **node},
            {"id": "b", "title": "Beta", **node},
        ],
        "edges": [
            {"id": "e1", "from": "a", "to": "b", "relation": "next"},
            {"id": "e2", "from": "b", "to": "a", "relation": "next"},
        ],
        "overlays": [],
        "traces": [],
        "diagnostics": [],
    }


class CompileAtifTest(unittest.TestCase):
    def _compile(self, rows):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "session-abc.jsonl"
            path.write_text(_jsonl(rows), encoding="utf-8")
            return strata.compile_atif_decision([path])

    def test_clean_search_web_is_not_a_blind_alley(self):
        ds = self._compile(
            _transcript({"type": "GENERIC", "status": "DONE", "content": "3 results"})
        )
        self.assertEqual(ds["traces"][0]["blindAlleyCount"], 0)
        self.assertFalse([n for n in ds["nodes"] if n["status"] == "blind-alley"])
        self.assertFalse([s for s in ds["traces"][0]["steps"] if s.get("isError")])

    def test_title_and_model_come_from_input(self):
        ds = self._compile(
            _transcript({"type": "GENERIC", "status": "DONE", "content": "ok"})
        )
        text = json.dumps(ds)
        self.assertIn("session-abc", ds["title"])
        self.assertNotIn("Forensic", text)
        self.assertEqual(ds["traces"][0]["model"], "test-model-1")

    def test_error_status_is_a_blind_alley(self):
        ds = self._compile(
            _transcript(
                {"type": "GENERIC", "status": "ERROR", "error": "boom", "content": ""}
            )
        )
        self.assertEqual(ds["traces"][0]["blindAlleyCount"], 1)

    def test_no_event_cap(self):
        rows = []
        for i in range(40):
            rows.append(
                {
                    "type": "PLANNER_RESPONSE",
                    "content": f"Update number {i} with unique text",
                    "tool_calls": [],
                }
            )
        norm = strata._normalize_jetski_jsonl(Path("t.jsonl"), rows)
        self.assertEqual(len(norm["events"]), 40)


class RenderHtmlTest(unittest.TestCase):
    def test_title_is_escaped(self):
        evil = "</title><script>alert(1)</script>"
        for html in (
            strata.render_html({"title": evil}),
            strata.render_html({"title": "x"}, title=evil),
        ):
            head = html.split("</head>", 1)[0]
            self.assertNotIn(evil, head)
            self.assertIn("&lt;/title&gt;&lt;script&gt;", head)


class ValidateDatasetTest(unittest.TestCase):
    def codes(self, ds):
        return [d["code"] for d in strata.validate_dataset(ds)]

    def test_valid_dataset_has_no_errors(self):
        self.assertEqual(self.codes(_mutual_cycle_dataset()), [])

    def test_dangling_edge(self):
        ds = _mutual_cycle_dataset()
        ds["edges"].append({"id": "e3", "from": "a", "to": "zzz", "relation": "next"})
        self.assertIn("DANGLING_EDGE", self.codes(ds))

    def test_duplicate_id(self):
        ds = _mutual_cycle_dataset()
        ds["nodes"].append(copy.deepcopy(ds["nodes"][1]))
        self.assertIn("DUPLICATE_ID", self.codes(ds))

    def test_missing_parent_and_trace_step(self):
        ds = _mutual_cycle_dataset()
        ds["nodes"][1]["parent"] = "nope"
        ds["traces"] = [{"id": "t", "steps": [{"stepIndex": 1, "nodeId": "gone"}]}]
        codes = self.codes(ds)
        self.assertIn("MISSING_PARENT", codes)
        self.assertIn("DANGLING_TRACE_STEP", codes)

    def test_repeated_runs_do_not_duplicate_diagnostics(self):
        ds = _mutual_cycle_dataset()
        ds["edges"].append({"id": "e3", "from": "a", "to": "zzz", "relation": "next"})
        first = list(strata.validate_dataset(ds))
        second = list(strata.validate_dataset(ds))
        self.assertEqual(first, second)


@unittest.skipUnless(shutil.which("node"), "node is not installed")
class ViewerTest(unittest.TestCase):
    def test_viewer_js_parses(self):
        subprocess.run(["node", "--check", str(VIEWER_JS)], check=True)

    @unittest.skipUnless(shutil.which("npx"), "npx is not installed")
    def test_viewer_js_has_no_undefined_names(self):
        proc = subprocess.run(
            [
                "npx",
                "--yes",
                "eslint@8",
                "--no-eslintrc",
                "--env",
                "browser,es2022",
                "--rule",
                '{"no-undef":"error"}',
                str(VIEWER_JS),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0 and "no-undef" not in proc.stdout:
            self.skipTest(f"eslint could not run: {proc.stderr[-200:]}")
        self.assertEqual(proc.returncode, 0, proc.stdout)


@unittest.skipUnless(
    shutil.which("google-chrome") or shutil.which("chromium"), "no headless browser"
)
class MutualCycleRenderTest(unittest.TestCase):
    def test_mutual_two_cycle_renders_without_script_errors(self):
        browser = shutil.which("google-chrome") or shutil.which("chromium")
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "cycle.html"
            page.write_text(
                strata.render_html(_mutual_cycle_dataset()), encoding="utf-8"
            )
            proc = subprocess.run(
                [
                    browser,
                    "--headless=new",
                    "--no-sandbox",
                    "--disable-gpu",
                    "--enable-logging=stderr",
                    "--v=0",
                    "--dump-dom",
                    str(page),
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=90,
            )
        self.assertNotIn("Uncaught", proc.stderr)
        self.assertIn("Alpha", proc.stdout)
        self.assertIn("Beta", proc.stdout)


if __name__ == "__main__":
    unittest.main()
