"""Tests for scripts/strata.py and assets/viewer.js (standard library only)."""

import contextlib
import copy
import importlib.util
import io
import json
import re
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

    @unittest.skipUnless(shutil.which("eslint"), "eslint is not installed locally")
    def test_viewer_js_has_no_undefined_names(self):
        proc = subprocess.run(
            [
                "eslint",
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


BROWSER = shutil.which("google-chrome") or shutil.which("chromium")


def _dump_dom(payload):
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "page.html"
        page.write_text(strata.render_html(payload), encoding="utf-8")
        return subprocess.run(
            [
                BROWSER,
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


@unittest.skipUnless(BROWSER, "no headless browser")
class BrowserRenderTest(unittest.TestCase):
    def test_mutual_two_cycle_renders_without_script_errors(self):
        proc = _dump_dom(_mutual_cycle_dataset())
        self.assertNotIn("Uncaught", proc.stderr)
        self.assertIn("Alpha", proc.stdout)
        self.assertIn("Beta", proc.stdout)

    def test_level_label_and_axis_notes_reach_the_dom(self):
        ds = _mutual_cycle_dataset()
        ds["edges"] = [ds["edges"][0]]
        ds["nodes"].append(
            {
                "id": "c",
                "title": "Gamma",
                "kind": "stage",
                "status": "ready",
                "parent": "r",
            }
        )
        ds["overlays"] = [
            {
                "id": "ov",
                "title": "Shared",
                "kind": "policy",
                "touches": ["a", "b", "c"],
            }
        ]
        ds["levelLabel"] = "zorp"
        # Notes only draw beside blocks that sit at x >= 220, which is where Gamma lands.
        ds["axisNotes"] = [{"nodeId": "c", "text": "MARGIN-NOTE-TEXT"}]
        proc = _dump_dom(ds)
        self.assertNotIn("Uncaught", proc.stderr)
        # The raw text is also in the embedded JSON, so match the rendered element.
        self.assertIsNotNone(
            re.search(r'class="frame-label"[^>]*>MARGIN-NOTE-TEXT<', proc.stdout),
            "axis note was not rendered",
        )
        self.assertIn("3 zorps", proc.stdout)

    def test_html_comment_text_does_not_swallow_the_page(self):
        ds = _mutual_cycle_dataset()
        ds["nodes"][1]["title"] = "<!-- <script></script> Alpha"
        proc = _dump_dom(ds)
        self.assertNotIn("Uncaught", proc.stderr)
        self.assertIn("Beta", proc.stdout)


class EmbeddedJsonTest(unittest.TestCase):
    def _embedded(self, payload):
        html = strata.render_html(payload)
        m = re.search(
            r'<script id="strata-data" type="application/json">(.*?)</script>',
            html,
            re.DOTALL,
        )
        self.assertIsNotNone(m)
        return html, m.group(1)

    def test_dangerous_strings_round_trip(self):
        for text in ("<!-- <script></script>", "<!-- STRATA:JS -->", "a\u2028b\u2029c"):
            payload = {"title": "t", "note": text}
            html, raw = self._embedded(payload)
            self.assertNotIn("<", raw)
            self.assertEqual(json.loads(raw), payload)
            self.assertEqual(html.count('id="strata-data"'), 1)

    def test_marker_in_data_does_not_inject_viewer(self):
        html, raw = self._embedded({"title": "t", "note": "<!-- STRATA:JS -->"})
        viewer = VIEWER_JS.read_text(encoding="utf-8")
        self.assertEqual(html.count(viewer), 1)
        self.assertNotIn("function prepareDataset", raw)


class SchemaDocTest(unittest.TestCase):
    def test_first_json_example_validates(self):
        text = (SKILL_DIR / "references" / "schema.md").read_text(encoding="utf-8")
        m = re.search(r"```json\n(.*?)\n```", text, re.DOTALL)
        self.assertIsNotNone(m)
        ds = json.loads(m.group(1))
        errors = [d for d in strata.validate_dataset(ds) if d["level"] == "error"]
        self.assertEqual(errors, [])


class CliTest(unittest.TestCase):
    def _run(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = strata.main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_compile_kg_rejects_database_with_wrong_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "empty.db"
            db.write_bytes(b"")
            code, _, err = self._run(
                ["compile-kg", str(db), "-o", str(Path(tmp) / "out.json")]
            )
        self.assertEqual(code, 1)
        self.assertIn("not a compatible knowledge-graph database", err)
        self.assertIn("entities(entity_id", err)

    def test_build_hub_fails_on_error_diagnostics(self):
        ds = _mutual_cycle_dataset()
        ds["edges"].append({"id": "e3", "from": "a", "to": "zzz", "relation": "next"})
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "ds.json"
            src.write_text(json.dumps(ds), encoding="utf-8")
            out = Path(tmp) / "hub.html"
            code, _, err = self._run(["build-hub", str(src), "-o", str(out)])
            self.assertEqual(code, 1)
            self.assertIn("DANGLING_EDGE", err)
            self.assertFalse(out.exists())

    def test_build_hub_succeeds_on_valid_datasets(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "ds.json"
            src.write_text(json.dumps(_mutual_cycle_dataset()), encoding="utf-8")
            out = Path(tmp) / "hub.html"
            code, _, _ = self._run(["build-hub", str(src), "-o", str(out)])
            self.assertEqual(code, 0)
            self.assertTrue(out.exists())


def _atif_doc(tool, exit_code, output):
    return {
        "schema_version": "ATIF-v1.4",
        "steps": [
            {
                "source": "agent",
                "message": "run",
                "tool_calls": [
                    {
                        "tool_call_id": "c1",
                        "function_name": tool,
                        "arguments": {"cmd": "x"},
                        "extra": {"exit_code": exit_code},
                    }
                ],
                "observation": {
                    "results": [{"source_call_id": "c1", "content": output}]
                },
            }
        ],
    }


class AtifCompareTest(unittest.TestCase):
    def _compile(self, docs, mode_compare=True):
        with tempfile.TemporaryDirectory() as tmp:
            paths = []
            for i, doc in enumerate(docs):
                p = Path(tmp) / f"run{i}.json"
                p.write_text(json.dumps(doc), encoding="utf-8")
                paths.append(p)
            if mode_compare:
                return strata.compile_atif_compare(paths)
            return strata.compile_atif_decision(paths)

    def test_output_text_alone_is_not_an_error(self):
        ds = self._compile(
            [_atif_doc("bash", 0, "permission denied and not found in text")],
            mode_compare=False,
        )
        self.assertEqual(ds["traces"][0]["blindAlleyCount"], 0)

    def test_nonzero_exit_code_is_an_error(self):
        ds = self._compile([_atif_doc("bash", 2, "")], mode_compare=False)
        self.assertEqual(ds["traces"][0]["blindAlleyCount"], 1)

    def test_goal_step_only_when_final_event_succeeds(self):
        ds = self._compile([_atif_doc("bash", 0, "ok"), _atif_doc("bash", 1, "bad")])
        ok, failed = ds["traces"]
        self.assertEqual(ok["steps"][-1]["label"], "Trajectory Goal Reached")
        self.assertNotIn(
            "Trajectory Goal Reached", [s["label"] for s in failed["steps"]]
        )
        self.assertIn("R1..R2", ds["subtitle"])

    def test_failed_run_has_no_edge_to_goal_node(self):
        ds = self._compile([_atif_doc("bash", 1, "bad")])
        self.assertFalse([e for e in ds["edges"] if e["to"] == "state:synthesis"])

    def test_unknown_tools_keep_their_real_name(self):
        ds = self._compile([_atif_doc("github_search", 0, "ok")])
        titles = [n["title"] for n in ds["nodes"]]
        self.assertIn("Tool: github_search", titles)
        self.assertNotIn("MCP Structural Code Search (github)", titles)


if __name__ == "__main__":
    unittest.main()
