"""Tests for scripts/strata.py and assets/viewer.js (standard library only)."""

import contextlib
import copy
import html as html_module
import importlib.util
import io
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SKILL_DIR = Path(__file__).resolve().parent.parent
VIEWER_JS = SKILL_DIR / "assets" / "viewer.js"
OKF_BUNDLE = (
    SKILL_DIR.parents[2]
    / "okf-authoring"
    / "skills"
    / "okf-author"
    / "assets"
    / "example-bundle"
)

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
        # The agent recovers on the next turn, so exactly one return arc exists.
        backtracks = [e for e in ds["edges"] if e["flowRole"] == "backtrack"]
        self.assertEqual(len(backtracks), 1)
        self.assertIn("1 ↺ backtrack", ds["subtitle"])

    def test_identical_consecutive_steps_merge_into_one_counted_event(self):
        rows = []
        for _ in range(3):
            rows.append(
                {
                    "type": "PLANNER_RESPONSE",
                    "tool_calls": [{"name": "read_file", "args": {"Path": "/x"}}],
                }
            )
            rows.append({"type": "GENERIC", "status": "DONE", "content": "ok"})
        events = strata._normalize_jetski_jsonl(Path("t.jsonl"), rows)["events"]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["count"], 3)
        self.assertIn("×3", events[0]["label"])

    def test_short_labels_are_not_marked_truncated(self):
        rows = [
            {"type": "USER_INPUT", "content": "Fix the build."},
            {"type": "PLANNER_RESPONSE", "content": "Done.", "tool_calls": []},
        ]
        labels = [
            e["label"]
            for e in strata._normalize_jetski_jsonl(Path("t.jsonl"), rows)["events"]
        ]
        self.assertTrue(labels)
        self.assertFalse(any("…" in label for label in labels), labels)

    def test_failed_calls_to_one_tool_in_a_turn_stay_separate(self):
        rows = [
            {
                "type": "PLANNER_RESPONSE",
                "tool_calls": [
                    {"name": "run_command", "args": {"CommandLine": "a"}},
                    {"name": "run_command", "args": {"CommandLine": "b"}},
                ],
            },
            {"type": "GENERIC", "status": "ERROR", "content": "first failed"},
            {"type": "GENERIC", "status": "ERROR", "content": "second failed"},
        ]
        events = strata._normalize_jetski_jsonl(Path("t.jsonl"), rows)["events"]
        errors = [e for e in events if e["is_error"]]
        self.assertEqual(len(errors), 2)
        self.assertEqual(
            [e["observation"] for e in errors], ["first failed", "second failed"]
        )

    def test_step_indexes_count_from_one_without_gaps(self):
        clean = self._compile(
            _transcript({"type": "GENERIC", "status": "DONE", "content": "ok"})
        )
        recovered = self._compile(
            _transcript(
                {"type": "GENERIC", "status": "ERROR", "error": "boom", "content": ""}
            )
        )
        for name, ds in (("clean", clean), ("recovered", recovered)):
            with self.subTest(run=name):
                steps = ds["traces"][0]["steps"]
                self.assertGreaterEqual(len(steps), 2)
                self.assertEqual(
                    [st["stepIndex"] for st in steps], list(range(1, len(steps) + 1))
                )
        self.assertIn(
            "backtrack", [st["role"] for st in recovered["traces"][0]["steps"]]
        )

    def test_retry_after_failure_uses_neutral_wording(self):
        call = {"name": "read_file", "args": {"Path": "/x"}}
        rows = [
            {"type": "USER_INPUT", "content": "Read it"},
            {"type": "PLANNER_RESPONSE", "tool_calls": [call]},
            {"type": "GENERIC", "status": "ERROR", "error": "denied", "content": ""},
            {"type": "PLANNER_RESPONSE", "tool_calls": [call]},
            {"type": "GENERIC", "status": "DONE", "content": "ok"},
        ]
        ds = self._compile(rows)
        self.assertTrue([e for e in ds["edges"] if e["flowRole"] == "backtrack"])
        texts = []
        for edge in ds["edges"]:
            texts += [edge.get("summary", ""), edge.get("contextSnippet", "")]
        for step in ds["traces"][0]["steps"]:
            texts += [step.get("label", ""), step.get("thought", "")]
        joined = " ".join(texts).lower()
        for word in ("abandoned", "pivot", "winning", "hypothesis"):
            self.assertNotIn(word, joined)
        phases = [n["id"] for n in ds["nodes"] if n["kind"] == "phase"]
        self.assertEqual(phases, ["phase:1", "phase:2", "phase:3"])

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

    def test_non_list_collections_are_reported(self):
        cases = {
            "nodes": "MALFORMED_NODE",
            "edges": "MALFORMED_EDGE",
            "traces": "MALFORMED_STEP",
        }
        for key, code in cases.items():
            with self.subTest(key=key):
                ds = _mutual_cycle_dataset()
                ds[key] = {"e1": {"id": "e1"}}
                self.assertIn(code, self.codes(ds))
        ds = _mutual_cycle_dataset()
        ds["traces"] = [{"id": "t", "steps": {"0": {"nodeId": "a"}}}]
        self.assertIn("MALFORMED_STEP", self.codes(ds))

    def test_non_object_and_idless_nodes_are_reported(self):
        ds = _mutual_cycle_dataset()
        ds["nodes"] += ["junk", {"title": "no id"}, {"id": "", "title": "empty"}]
        codes = self.codes(ds)
        self.assertIn("MALFORMED_NODE", codes)
        self.assertEqual(codes.count("BAD_ID"), 2)

    def test_empty_trace_object_is_not_malformed(self):
        ds = _mutual_cycle_dataset()
        ds["traces"] = [{}]
        self.assertEqual(self.codes(ds), [])

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


def _dump_dom(payload, extra_script=""):
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "page.html"
        html = strata.render_html(payload).replace("</body>", f"{extra_script}</body>")
        page.write_text(html, encoding="utf-8")
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

    def test_status_with_whitespace_still_renders(self):
        ds = _mutual_cycle_dataset()
        ds["nodes"][1]["status"] = "in progress"
        proc = _dump_dom(ds)
        self.assertNotIn("Uncaught", proc.stderr)
        self.assertIn("Alpha", proc.stdout)
        self.assertIn("Beta", proc.stdout)
        self.assertIn("st-in-progress", proc.stdout)

    def test_selecting_a_block_clears_a_picked_wire_bundle(self):
        ds = _mutual_cycle_dataset()
        ds["edges"] = [ds["edges"][0]]
        ds["traces"] = [
            {
                "id": "t",
                "title": "T",
                "steps": [
                    {"stepIndex": 1, "nodeId": "a", "label": "s1"},
                    {"stepIndex": 2, "nodeId": "b", "label": "s2"},
                ],
            }
        ]
        script = """<script>(function () {
          const title = () => {
            const t = document.querySelector("#panel-body .d-title");
            return t ? t.textContent : "";
          };
          const pickBundle = () => {
            document.querySelector("[data-bundle-key] .hit").dispatchEvent(
              new MouseEvent("click", { bubbles: true }));
            return title();
          };
          const out = { picked: pickBundle() };
          document.querySelectorAll(".step-pip")[1].click();
          out.afterPip = title();
          out.pickedAgain = pickBundle();
          window.dispatchEvent(new KeyboardEvent("keydown", { key: "]" }));
          out.afterStep = title();
          document.body.setAttribute("data-result", JSON.stringify(out));
        })();</script>"""
        proc = _dump_dom(ds, script)
        self.assertNotIn("Uncaught", proc.stderr)
        m = re.search(r'data-result="([^"]*)"', proc.stdout)
        self.assertIsNotNone(m, "page script did not run")
        out = json.loads(html_module.unescape(m.group(1)))
        self.assertEqual(out["picked"], "Alpha → Beta")
        self.assertEqual(out["pickedAgain"], "Alpha → Beta")
        self.assertNotIn("→", out["afterPip"])
        self.assertNotIn("→", out["afterStep"])

    def _run_page_script(self, body, dataset=None):
        script = f"<script>(function () {{ const out = {{}}; {body}\n"
        script += 'document.body.setAttribute("data-result", JSON.stringify(out)); })();</script>'
        proc = _dump_dom(dataset or _mutual_cycle_dataset(), script)
        self.assertNotIn("Uncaught", proc.stderr)
        m = re.search(r'data-result="([^"]*)"', proc.stdout)
        self.assertIsNotNone(m, "page script did not run")
        return json.loads(html_module.unescape(m.group(1)))

    def test_dragging_the_viewport_keeps_the_selection(self):
        out = self._run_page_script("""
          const viewport = document.getElementById("viewport");
          const selected = () => !!document.querySelector(".block.selected");
          const mouse = (target, type, x) =>
            target.dispatchEvent(new MouseEvent(type, { bubbles: true, clientX: x, clientY: 10 }));
          const pick = () => document.querySelector('.block[data-box-id="a"]')
            .dispatchEvent(new MouseEvent("click", { bubbles: true }));
          pick();
          out.picked = selected();
          mouse(viewport, "mousedown", 100);
          mouse(window, "mousemove", 150);
          mouse(window, "mouseup", 150);
          mouse(viewport, "click", 150);
          out.afterDrag = selected();
          mouse(viewport, "mousedown", 100);
          mouse(window, "mouseup", 101);
          mouse(viewport, "click", 101);
          out.afterPlainClick = selected();
        """)
        self.assertTrue(out["picked"])
        self.assertTrue(out["afterDrag"])
        self.assertFalse(out["afterPlainClick"])

    def test_zoom_out_starts_from_the_fitted_scale(self):
        ds = _mutual_cycle_dataset()
        ds["edges"] = []
        for i in range(14):
            ds["nodes"].append(
                {
                    "id": f"n{i}",
                    "title": f"N{i}",
                    "kind": "stage",
                    "status": "ready",
                    "parent": "r",
                }
            )
        out = self._run_page_script(
            """
          const readout = document.getElementById("zoom-fit");
          const pct = () => parseInt(readout.textContent.match(/(\\d+)%/)[1], 10);
          out.fit = pct();
          document.getElementById("zoom-out").click();
          out.after = pct();
        """,
            ds,
        )
        self.assertLess(out["fit"], 75)
        self.assertLess(out["after"], out["fit"])

    def test_search_can_select_a_slice_beyond_the_visible_cap(self):
        ds = _mutual_cycle_dataset()
        ds["overlays"] = [
            {
                "id": f"ov{i}",
                "title": f"Overlay {i}",
                "kind": "policy",
                "touches": ["a", "b"],
            }
            for i in range(1, 22)
        ]
        ds["overlays"].append(
            {"id": "ov22", "title": "Overlay 22", "kind": "policy", "touches": ["a"]}
        )
        out = self._run_page_script(
            """
          const input = document.getElementById("search-input");
          input.value = "overlay 22";
          input.dispatchEvent(new Event("input", { bubbles: true }));
          const item = document.querySelector("#search-results .r-item");
          out.hit = item ? item.textContent : "";
          item.click();
          const title = document.querySelector("#panel-body .d-title");
          out.title = title ? title.textContent : "";
        """,
            ds,
        )
        self.assertIn("Overlay 22", out["hit"])
        self.assertEqual(out["title"], "Overlay 22")

    def test_escape_closes_diagnostics_drawer_and_resets_aria(self):
        out = self._run_page_script("""
          const toggle = document.getElementById("diag-toggle");
          const drawer = document.getElementById("drawer");
          toggle.click();
          out.open = [drawer.hidden, toggle.getAttribute("aria-expanded")];
          window.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape" }));
          out.closed = [drawer.hidden, toggle.getAttribute("aria-expanded")];
        """)
        self.assertEqual(out["open"], [False, "true"])
        self.assertEqual(out["closed"], [True, "false"])

    def test_search_results_close_on_escape_and_outside_click(self):
        out = self._run_page_script("""
          const input = document.getElementById("search-input");
          const results = document.getElementById("search-results");
          const state = () => [results.hidden, input.getAttribute("aria-expanded")];
          const search = () => {
            input.value = "alpha";
            input.dispatchEvent(new Event("input", { bubbles: true }));
            return state();
          };
          out.opened = search();
          document.body.dispatchEvent(
            new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
          out.afterEscape = state();
          search();
          input.dispatchEvent(new MouseEvent("click", { bubbles: true }));
          out.afterInputClick = state();
          document.body.dispatchEvent(new MouseEvent("click", { bubbles: true }));
          out.afterOutsideClick = state();
        """)
        self.assertEqual(out["opened"], [False, "true"])
        self.assertEqual(out["afterEscape"], [True, "false"])
        self.assertEqual(out["afterInputClick"], [False, "true"])
        self.assertEqual(out["afterOutsideClick"], [True, "false"])

    def test_untitled_nodes_and_junk_entries_render(self):
        ds = _mutual_cycle_dataset()
        for node in ds["nodes"][1:]:
            del node["title"]
        ds["nodes"].append("junk")
        ds["edges"].append(None)
        ds["domain"] = 5
        proc = _dump_dom(ds)
        self.assertNotIn("Uncaught", proc.stderr)
        for node_id in ("a", "b"):
            self.assertRegex(proc.stdout, rf'class="b-title"[^>]*>{node_id}<')

    def test_real_ids_that_look_like_synthetic_box_ids_stay_distinct(self):
        def node(node_id, title, parent):
            return {
                "id": node_id,
                "title": title,
                "kind": "stage",
                "status": "ready",
                "parent": parent,
            }

        ds = _mutual_cycle_dataset()
        ds["nodes"] = [
            node("r", "Root", None),
            node("c1", "Group One", "r"),
            node("slice:auth", "Auth Node", "c1"),
            node("bot:x", "Bot X Node", "c1"),
            node("x", "Outside X", "r"),
            node("xk", "Outside Kid", "x"),
        ]
        # The outside end of the edge is lifted to its container "x", which gets the
        # ghost box that must not collide with the real node "bot:x".
        ds["edges"] = [{"id": "e1", "from": "bot:x", "to": "xk", "relation": "next"}]
        ds["overlays"] = [
            {
                "id": "auth",
                "title": "Auth Overlay",
                "kind": "policy",
                "touches": ["slice:auth", "bot:x"],
            }
        ]
        out = self._run_page_script(
            """
          document.querySelector('.block[data-box-id="c1"]')
            .dispatchEvent(new MouseEvent("dblclick", { bubbles: true }));
          const count = (id) =>
            Array.from(document.querySelectorAll(".block[data-box-id]"))
              .filter((el) => el.dataset.boxId === id).length;
          out.counts = {
            realSlice: count("slice:auth"),
            realBot: count("bot:x"),
            overlay: count("~slice:auth"),
            ghost: count("~bot:x"),
          };
          const title = () => {
            const t = document.querySelector("#panel-body .d-title");
            return t ? t.textContent : "";
          };
          const pick = (id) => {
            Array.from(document.querySelectorAll(".block[data-box-id]"))
              .find((el) => el.dataset.boxId === id)
              .dispatchEvent(new MouseEvent("click", { bubbles: true }));
            return title();
          };
          out.pickedSlice = pick("slice:auth");
          out.pickedBot = pick("bot:x");
        """,
            ds,
        )
        self.assertEqual(
            out["counts"], {"realSlice": 1, "realBot": 1, "overlay": 1, "ghost": 1}
        )
        self.assertEqual(out["pickedSlice"], "Auth Node")
        self.assertEqual(out["pickedBot"], "Bot X Node")

    def test_expanded_mode_marks_leaves_beyond_the_cap(self):
        ds = _mutual_cycle_dataset()
        ds["edges"] = []
        ds["nodes"] = [
            {
                "id": "r",
                "title": "Root",
                "kind": "process",
                "status": "ready",
                "parent": None,
            },
            {
                "id": "g",
                "title": "Group",
                "kind": "stage",
                "status": "ready",
                "parent": "r",
            },
        ] + [
            {
                "id": f"leaf{i}",
                "title": f"Leaf {i}",
                "kind": "step",
                "status": "ready",
                "parent": "g",
            }
            for i in range(120)
        ]
        out = self._run_page_script(
            """
          document.getElementById("mode-toggle").click();
          out.stats = document.querySelector(".lh-stats").textContent;
        """,
            ds,
        )
        self.assertIn("110 spine blocks", out["stats"])
        self.assertIn("+10 more blocks not shown", out["stats"])

    def test_compare_all_marks_only_the_failing_block(self):
        def doc(steps):
            return {"schema_version": "ATIF-v1.4", "steps": steps}

        def step(tool, code):
            return _atif_doc(tool, code, "x")["steps"][0]

        with tempfile.TemporaryDirectory() as tmp:
            paths = []
            for i, steps in enumerate(
                (
                    [step("read_file", 0)],
                    [step("github_search", 1), step("read_file", 0)],
                )
            ):
                path = Path(tmp) / f"run{i}.json"
                path.write_text(json.dumps(doc(steps)), encoding="utf-8")
                paths.append(path)
            ds = strata.compile_atif_compare(paths)
        out = self._run_page_script(
            """
          const pill = Array.from(document.querySelectorAll(".trace-pill"))
            .find((b) => b.textContent.includes("Compare All"));
          pill.click();
          out.chips = {};
          for (const box of document.querySelectorAll(".block[data-box-id]")) {
            out.chips[box.dataset.boxId] = Array.from(box.querySelectorAll(".visit-chip"))
              .map((c) => ({
                text: c.textContent,
                blind: c.classList.contains("chip-blind"),
                colored: c.style.borderColor !== "",
              }));
          }
        """,
            ds,
        )
        chips = out["chips"]
        for node_id in ("state:intake", "state:synthesis", "state:planner"):
            with self.subTest(node=node_id):
                self.assertTrue(chips[node_id])
                for chip in chips[node_id]:
                    self.assertFalse(chip["blind"], chips[node_id])
                    self.assertTrue(chip["colored"], chips[node_id])
        blind_nodes = {
            node_id
            for node_id, items in chips.items()
            if any(c["blind"] for c in items)
        }
        self.assertEqual(blind_nodes, {"err:obstacle"})
        self.assertEqual([c["text"] for c in chips["err:obstacle"]], ["R2"])

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
    def test_every_trajectory_input_format_has_a_heading(self):
        help_text = " ".join(strata._build_parser().format_help().split())
        m = re.search(r"Compile 1\.\.N (.+?) trajectories", help_text)
        self.assertIsNotNone(m, help_text)
        formats = re.split(r",\s*|\s+or\s+", m.group(1))
        self.assertGreaterEqual(len(formats), 2)
        headings = [
            line.lstrip("#").strip().lower()
            for line in (SKILL_DIR / "references" / "schema.md")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.startswith("#")
        ]
        for name in formats:
            with self.subTest(format=name):
                self.assertTrue(
                    any(
                        h.startswith(name.lower()) and h.endswith("input")
                        for h in headings
                    ),
                    f"no '{name} input' heading in schema.md",
                )

    def test_first_json_example_validates(self):
        text = (SKILL_DIR / "references" / "schema.md").read_text(encoding="utf-8")
        m = re.search(r"```json\n(.*?)\n```", text, re.DOTALL)
        self.assertIsNotNone(m)
        ds = json.loads(m.group(1))
        errors = [d for d in strata.validate_dataset(ds) if d["level"] == "error"]
        self.assertEqual(errors, [])


@unittest.skipUnless(OKF_BUNDLE.is_dir(), "example OKF bundle not found")
class CompileOkfTest(unittest.TestCase):
    def parsers(self):
        yield "fallback", None
        if importlib.util.find_spec("yaml"):
            yield "pyyaml", importlib.import_module("yaml")

    def compile(self, yaml_module):
        with mock.patch.object(strata, "_pyyaml", yaml_module):
            return strata.compile_okf(OKF_BUNDLE)

    def test_example_bundle_has_no_diagnostics_and_no_reserved_nodes(self):
        for name, mod in self.parsers():
            with self.subTest(parser=name):
                ds = self.compile(mod)
                codes = [d["code"] for d in ds["diagnostics"]]
                self.assertNotIn("OKF_MISSING_TYPE", codes)
                ids = {n["id"] for n in ds["nodes"]}
                self.assertNotIn("tables:index", ids)
                self.assertNotIn("index", ids)
                self.assertNotIn("log", ids)
                self.assertIn("tables:orders", ids)

    def test_trust_tiers_follow_the_actor_convention(self):
        for name, mod in self.parsers():
            with self.subTest(parser=name):
                by_id = {n["id"]: n for n in self.compile(mod)["nodes"]}
                self.assertEqual(
                    by_id["computations:revenue"]["trust"]["tier"], "machine-confirmed"
                )
                self.assertEqual(
                    by_id["metrics:revenue"]["trust"]["tier"], "human-reviewed"
                )
                self.assertEqual(
                    by_id["references:skills:run-on-bq"]["trust"]["tier"], "unverified"
                )
                # No `status` key means stable, which is ready, not draft.
                self.assertEqual(by_id["tables:customers"]["status"], "ready")

    def test_tags_are_whole_words_and_dates_are_strings(self):
        for name, mod in self.parsers():
            with self.subTest(parser=name):
                by_id = {n["id"]: n for n in self.compile(mod)["nodes"]}
                self.assertEqual(
                    by_id["metrics:revenue"]["tags"], ["finance", "revenue"]
                )
                self.assertEqual(
                    by_id["metrics:revenue"]["trust"]["staleAfter"], "2026-12-31"
                )

    def test_compiles_to_json_and_html_with_each_parser(self):
        for name, mod in self.parsers():
            for suffix in (".json", ".html"):
                with (
                    self.subTest(parser=name, output=suffix),
                    tempfile.TemporaryDirectory() as tmp,
                    mock.patch.object(strata, "_pyyaml", mod),
                ):
                    out = Path(tmp) / f"bundle{suffix}"
                    code, _, err = run_main(
                        ["compile-okf", str(OKF_BUNDLE), "-o", str(out)]
                    )
                    self.assertEqual(code, 0, err)
                    self.assertTrue(out.exists())

    def test_parse_yaml_safe_converts_dates_and_flow_lists(self):
        text = (
            "stale_after: 2026-12-31\nat: 2026-06-20T22:53:05Z\ntags: [a, bc]  # note\n"
        )
        for name, mod in self.parsers():
            with self.subTest(parser=name):
                with mock.patch.object(strata, "_pyyaml", mod):
                    fm = strata.parse_yaml_safe(text)
                self.assertEqual(fm["stale_after"], "2026-12-31")
                self.assertEqual(fm["at"], "2026-06-20T22:53:05Z")
                self.assertEqual(fm["tags"], ["a", "bc"])
                json.dumps(fm)

    def test_block_mapping_trust_fields_match_across_parsers(self):
        concept = (
            "---\ntype: Metric\n"
            "generated:\n  by: producer/1.0\n  at: 2026-01-01T00:00:00Z\n"
            "verified:\n  by: human:alice\n  at: 2026-01-02\n---\nBody.\n"
        )
        for name, mod in self.parsers():
            with (
                self.subTest(parser=name),
                tempfile.TemporaryDirectory() as tmp,
                mock.patch.object(strata, "_pyyaml", mod),
            ):
                (Path(tmp) / "m.md").write_text(concept, encoding="utf-8")
                node = next(
                    n for n in strata.compile_okf(Path(tmp))["nodes"] if n["id"] == "m"
                )
                self.assertEqual(node["trust"]["tier"], "human-reviewed")
                self.assertEqual(node["trust"]["generatedBy"], "producer/1.0")

    def _compile_text(self, files):
        with tempfile.TemporaryDirectory() as tmp:
            for name, text in files.items():
                (Path(tmp) / name).write_text(text, encoding="utf-8")
            return strata.compile_okf(Path(tmp))

    def test_wrapped_anchor_text_still_links(self):
        for name, mod in self.parsers():
            with self.subTest(parser=name):
                ds = self.compile(mod)
                pairs = {(e["from"], e["to"]) for e in ds["edges"]}
                self.assertIn(("metrics:revenue", "computations:revenue"), pairs)

    def test_links_inside_fenced_code_are_ignored(self):
        body = (
            "---\ntype: T\n---\n"
            "Real [b](b.md) link.\n\n"
            "```md\n[fake](missing.md)\n# not a heading\n[c](c.md)\n```\n\n"
            "~~~\n[tilde](missing2.md)\n~~~\n"
        )
        plain = "---\ntype: T\n---\nText.\n"
        ds = self._compile_text({"a.md": body, "b.md": plain, "c.md": plain})
        self.assertEqual([(e["from"], e["to"]) for e in ds["edges"]], [("a", "b")])
        self.assertNotIn("BROKEN_MD_LINK", [d["code"] for d in ds["diagnostics"]])

    def test_concept_ids_never_collide_with_containers(self):
        plain = "---\ntype: T\n---\nText.\n"
        with tempfile.TemporaryDirectory() as tmp:
            for rel in ("auth/overview.md", "sec/auth.md", "sec/sec.md", "okf/root.md"):
                (Path(tmp) / rel).parent.mkdir(parents=True, exist_ok=True)
                (Path(tmp) / rel).write_text(plain, encoding="utf-8")
            ds = strata.compile_okf(Path(tmp))
        codes = [d["code"] for d in strata.validate_dataset(ds)]
        self.assertNotIn("DUPLICATE_ID", codes)
        self.assertNotIn("PARENT_CYCLE", codes)
        ids = {n["id"] for n in ds["nodes"]}
        self.assertTrue({"sec:auth", "sec/auth", "okf:root", "okf/root"} <= ids)

    def test_all_theme_slices_are_kept(self):
        files = {}
        for i in range(90):
            files[f"c{i:02d}.md"] = (
                f"---\ntype: T\ntags: [theme{i // 3}]\n---\nBody {i}.\n"
            )
        ds = self._compile_text(files)
        themes = [o for o in ds["overlays"] if o["kind"] == "theme"]
        self.assertEqual(len(themes), 30)

    def test_scalar_tags_become_one_tag(self):
        for name, mod in self.parsers():
            with self.subTest(parser=name), mock.patch.object(strata, "_pyyaml", mod):
                ds = self._compile_text(
                    {"a.md": "---\ntype: T\ntags: alpha\n---\nText.\n"}
                )
                node = next(n for n in ds["nodes"] if n["id"] == "a")
                self.assertEqual(node["tags"], ["alpha"])

    def test_symlinked_files_outside_the_bundle_are_skipped(self):
        for name, mod in self.parsers():
            with (
                self.subTest(parser=name),
                tempfile.TemporaryDirectory() as tmp,
                mock.patch.object(strata, "_pyyaml", mod),
            ):
                root = Path(tmp)
                bundle = root / "bundle"
                bundle.mkdir()
                (root / "secret.md").write_text(
                    "---\ntype: T\ntitle: TOP-SECRET-TITLE\n---\nTOP-SECRET-TEXT\n",
                    encoding="utf-8",
                )
                (root / "secret-index.md").write_text(
                    "---\ntitle: SECRET-INDEX-TITLE\n---\n", encoding="utf-8"
                )
                try:
                    (bundle / "leak.md").symlink_to(root / "secret.md")
                    (bundle / "index.md").symlink_to(root / "secret-index.md")
                except OSError:
                    self.skipTest("symlinks are not available")
                (bundle / "ok.md").write_text(
                    "---\ntype: T\n---\nFine.\n", encoding="utf-8"
                )
                ds = strata.compile_okf(bundle)
                text = json.dumps(ds)
                self.assertNotIn("TOP-SECRET", text)
                self.assertNotIn("SECRET-INDEX-TITLE", text)
                found = [
                    d for d in ds["diagnostics"] if d["code"] == "PATH_OUTSIDE_BUNDLE"
                ]
                self.assertEqual(sorted(d["level"] for d in found), ["warn", "warn"])
                self.assertIn("ok", {n["id"] for n in ds["nodes"]})

    def test_link_outside_the_bundle_is_a_warning(self):
        ds = self._compile_text(
            {"a.md": "---\ntype: T\n---\nSee [readme](../README.md).\n"}
        )
        found = [d for d in ds["diagnostics"] if d["code"] == "PATH_OUTSIDE_BUNDLE"]
        self.assertEqual([d["level"] for d in found], ["warn"])

    def test_link_outside_the_bundle_does_not_fail_the_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp) / "b"
            bundle.mkdir()
            (bundle / "a.md").write_text(
                "---\ntype: T\n---\nSee [readme](../README.md).\n", encoding="utf-8"
            )
            code, _, err = run_main(
                ["compile-okf", str(bundle), "-o", str(Path(tmp) / "o.json")]
            )
        self.assertEqual(code, 0, err)

    def test_relation_heading_uses_whole_words(self):
        classify = strata.classify_okf_relation
        self.assertEqual(classify("a", "b", "Research notes"), "references")
        self.assertEqual(classify("a", "b", "March plan, Search"), "references")
        self.assertEqual(classify("a", "b", "Architecture"), "composes-pattern")
        self.assertEqual(classify("a", "b", "Design patterns"), "composes-pattern")


BLOCK_YAML = """title: Doc
description: >-
  folded line one
  continues here
notes: |
  line a
  line b
events:
  - date: 2026-01-01
    actors:
      - acme
      - beta corp
    title: X
tags:
  - a
  - bc
"""


class FallbackYamlTest(unittest.TestCase):
    def test_block_scalars_and_nested_sequences_match_pyyaml(self):
        expected = {
            "title": "Doc",
            "description": "folded line one continues here",
            "notes": "line a\nline b\n",
            "events": [
                {"date": "2026-01-01", "actors": ["acme", "beta corp"], "title": "X"}
            ],
            "tags": ["a", "bc"],
        }
        modules = [None]
        if importlib.util.find_spec("yaml"):
            modules.append(importlib.import_module("yaml"))
        for mod in modules:
            with (
                self.subTest(parser="pyyaml" if mod else "fallback"),
                mock.patch.object(strata, "_pyyaml", mod),
            ):
                self.assertEqual(strata.parse_yaml_safe(BLOCK_YAML), expected)

    def test_quotes_match_pyyaml(self):
        text = (
            "a: \"say 'hi'\"\n"
            "b: 'say \"hi\"'\n"
            "c: \"'quoted'\"\n"
            "d: it's fine\n"
            'e: say "hi"\n'
            "f: don't\n"
            "g: '\"mixed\"'\n"
            "h: 'x'\n"
        )
        with mock.patch.object(strata, "_pyyaml", None):
            fallback = strata.parse_yaml_safe(text)
        self.assertEqual(fallback["a"], "say 'hi'")
        self.assertEqual(fallback["c"], "'quoted'")
        self.assertEqual(fallback["g"], '"mixed"')
        if importlib.util.find_spec("yaml"):
            with mock.patch.object(strata, "_pyyaml", importlib.import_module("yaml")):
                self.assertEqual(strata.parse_yaml_safe(text), fallback)

    def test_comments_after_quoted_values_are_dropped(self):
        with mock.patch.object(strata, "_pyyaml", None):
            fm = strata.parse_yaml_safe('a: "x # y"  # note\nb: https://h/p#frag\n')
        self.assertEqual(fm, {"a": "x # y", "b": "https://h/p#frag"})


class CompileKgYamlTest(unittest.TestCase):
    TIMELINE = (
        "events:\n"
        "  - date: 2026-01-01\n"
        "    title: Launch\n"
        "    description: >-\n"
        "      Acme ships.\n"
        "    actors:\n"
        "      - acme\n"
        "      - other-co\n"
    )

    def test_timeline_only_directory_resolves_actors(self):
        modules = [None]
        if importlib.util.find_spec("yaml"):
            modules.append(importlib.import_module("yaml"))
        for mod in modules:
            with (
                self.subTest(parser="pyyaml" if mod else "fallback"),
                tempfile.TemporaryDirectory() as tmp,
                mock.patch.object(strata, "_pyyaml", mod),
            ):
                root = Path(tmp)
                (root / "timeline.yaml").write_text(self.TIMELINE, encoding="utf-8")
                (root / "entities").mkdir()
                (root / "entities" / "acme.yaml").write_text(
                    "name: Acme Corp\ntype: company\n", encoding="utf-8"
                )
                ds = strata.compile_kg(root)
                titles = {n["title"] for n in ds["nodes"]}
                self.assertIn("Acme Corp", titles)
                self.assertIn("Other Co", titles)
                steps = ds["traces"][0]["steps"]
                self.assertEqual(len(steps), 2)
                self.assertIn("Acme ships.", steps[0]["observation"])

    def test_entity_type_falls_back_to_a_singular_directory_name(self):
        timeline = (
            "events:\n  - date: 2026-01-01\n    title: T\n    actors: [plain, firm]\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "timeline.yaml").write_text(timeline, encoding="utf-8")
            (root / "entities" / "companies").mkdir(parents=True)
            (root / "entities" / "plain.yaml").write_text(
                "name: Plain\n", encoding="utf-8"
            )
            (root / "entities" / "companies" / "firm.yaml").write_text(
                "name: Firm\n", encoding="utf-8"
            )
            ids = {n["id"] for n in strata.compile_kg(root)["nodes"]}
        self.assertIn("entity:plain", ids)
        self.assertIn("company:firm", ids)
        self.assertNotIn("entitie:plain", ids)

    def test_actor_slugs_cannot_read_files_outside_entities(self):
        timeline = (
            "events:\n  - date: 2026-01-01\n    title: T\n"
            '    actors: ["../secret", "..\\\\secret", "ok"]\n'
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "timeline.yaml").write_text(timeline, encoding="utf-8")
            (root / "secret.yaml").write_text("name: LEAKED\n", encoding="utf-8")
            (root / "entities").mkdir()
            (root / "entities" / "ok.yaml").write_text("name: Fine\n", encoding="utf-8")
            titles = {n["title"] for n in strata.compile_kg(root)["nodes"]}
        self.assertIn("Fine", titles)
        self.assertNotIn("LEAKED", titles)

    def test_all_source_slices_are_kept(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "pipeline.db"
            conn = sqlite3.connect(db)
            conn.executescript(
                "CREATE TABLE sources(id INTEGER, uri TEXT, title TEXT);"
                "CREATE TABLE entities(entity_id TEXT, name TEXT, kind TEXT, type TEXT,"
                " description TEXT, status TEXT, source_id INTEGER, merged_into TEXT);"
                "CREATE TABLE edges(source_entity_id TEXT, target_entity_id TEXT,"
                " edge_type TEXT, confidence REAL);"
            )
            for k in range(22):
                conn.execute(
                    "INSERT INTO sources VALUES (?, ?, ?)",
                    (k, f"https://example.test/{k}", f"Doc {k}"),
                )
                for j in range(2):
                    conn.execute(
                        "INSERT INTO entities VALUES (?, ?, 'org', 'organization',"
                        " 'd', 'approved', ?, NULL)",
                        (f"org:e{k}-{j}", f"E{k}-{j}", k),
                    )
            conn.commit()
            conn.close()
            ds = strata.compile_kg(db)
        self.assertEqual(len(ds["overlays"]), 22)

    def test_scalar_actors_are_one_entity(self):
        timeline = "events:\n  - date: 2026-01-01\n    title: T\n    actors: acme\n"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "timeline.yaml").write_text(timeline, encoding="utf-8")
            (root / "entities").mkdir()
            (root / "entities" / "acme.yaml").write_text(
                "name: Acme Corp\n", encoding="utf-8"
            )
            ds = strata.compile_kg(root)
        titles = {n["title"] for n in ds["nodes"] if n["id"].startswith("entity:")}
        self.assertEqual(titles, {"Acme Corp"})
        self.assertEqual(len(ds["traces"][0]["steps"]), 1)

    def test_graph_with_no_entities_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "timeline.yaml").write_text(
                "events:\n  - date: 2026-01-01\n    title: Nothing\n",
                encoding="utf-8",
            )
            with self.assertRaises(strata.KGSchemaError):
                strata.compile_kg(Path(tmp))

    def test_database_path_with_uri_characters(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "a#b?c"
            folder.mkdir()
            db = folder / "pipeline.db"
            conn = sqlite3.connect(db)
            conn.executescript(
                "CREATE TABLE sources(id INTEGER, uri TEXT, title TEXT);"
                "CREATE TABLE entities(entity_id TEXT, name TEXT, kind TEXT, type TEXT,"
                " description TEXT, status TEXT, source_id INTEGER, merged_into TEXT);"
                "CREATE TABLE edges(source_entity_id TEXT, target_entity_id TEXT,"
                " edge_type TEXT, confidence REAL);"
                "INSERT INTO entities VALUES('org:acme','Acme','org','organization',"
                "'d','approved',NULL,NULL);"
            )
            conn.commit()
            conn.close()
            ds = strata.compile_kg(db)
        self.assertIn("org:acme", {n["id"] for n in ds["nodes"]})

    @unittest.skipIf(
        hasattr(os, "geteuid") and os.geteuid() == 0, "root can read 0o000 files"
    )
    def test_unreadable_database_is_a_json_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "pipeline.db"
            sqlite3.connect(db).close()
            db.chmod(0)
            try:
                proc = run_cli("compile-kg", db, "-o", Path(tmp) / "out.json")
            finally:
                db.chmod(0o600)
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(json.loads(proc.stderr)["status"], "error")

    def test_text_and_null_source_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "pipeline.db"
            conn = sqlite3.connect(db)
            conn.executescript(
                "CREATE TABLE sources(id TEXT, uri TEXT, title TEXT);"
                "CREATE TABLE entities(entity_id TEXT, name TEXT, kind TEXT, type TEXT,"
                " description TEXT, status TEXT, source_id TEXT, merged_into TEXT);"
                "CREATE TABLE edges(source_entity_id TEXT, target_entity_id TEXT,"
                " edge_type TEXT, confidence REAL);"
                "INSERT INTO sources VALUES('src-a','https://example.com/a','A');"
                "INSERT INTO sources VALUES(NULL,'https://example.com/n','N');"
                "INSERT INTO entities VALUES('org:acme','Acme','org','organization',"
                "'d','approved','src-a',NULL);"
            )
            conn.commit()
            conn.close()
            ds = strata.compile_kg(db)
        acme = next(n for n in ds["nodes"] if n["id"] == "org:acme")
        self.assertEqual([s["url"] for s in acme["sources"]], ["https://example.com/a"])


class CommentStyleTest(unittest.TestCase):
    FILES = (
        ("assets/viewer.js", ("//", "/*", "*")),
        ("assets/viewer.css", ("/*", "*")),
        ("scripts/strata.py", ("#",)),
    )

    def test_no_exclamation_or_hype_in_comment_lines(self):
        for name, starts in self.FILES:
            text = (SKILL_DIR / name).read_text(encoding="utf-8")
            for number, line in enumerate(text.splitlines(), 1):
                stripped = line.strip()
                if not stripped.startswith(starts):
                    continue
                with self.subTest(file=name, line=number):
                    self.assertFalse(
                        stripped.rstrip("*/ ").endswith("!"), f"{name}:{number}"
                    )
                    self.assertNotIn("crisp", stripped.lower(), f"{name}:{number}")


class WordingTest(unittest.TestCase):
    FILES = (
        "scripts/strata.py",
        "assets/viewer.js",
        "assets/viewer.css",
        "SKILL.md",
        "references/schema.md",
        "../../README.md",
    )
    BANNED = ("never lie", "real blind alleys", "side-by-side", "beautiful", "seamless")

    def test_no_sales_style_phrases(self):
        for name in self.FILES:
            text = (SKILL_DIR / name).read_text(encoding="utf-8").lower()
            for phrase in self.BANNED:
                with self.subTest(file=name, phrase=phrase):
                    self.assertNotIn(phrase, text)


class StatusDocTest(unittest.TestCase):
    def test_every_styled_status_class_is_documented(self):
        css = (SKILL_DIR / "assets" / "viewer.css").read_text(encoding="utf-8")
        schema = (SKILL_DIR / "references" / "schema.md").read_text(encoding="utf-8")
        section = schema.split("## 2.", 1)[1].split("## 3.", 1)[0]
        documented = set(re.findall(r'"([a-z-]+)"', section))
        styled = set(re.findall(r"\.st-([a-z][a-z-]*)", css))
        self.assertIn("blind-alley", styled)
        self.assertEqual(sorted(styled - documented), [])

    def test_docs_do_not_claim_a_right_only_return_rail(self):
        for name in ("SKILL.md", "references/schema.md"):
            text = (SKILL_DIR / name).read_text(encoding="utf-8")
            self.assertNotIn("right-hand", text, name)
            self.assertNotIn("right-margin", text, name)


class ShortcutDocTest(unittest.TestCase):
    def test_every_advertised_shortcut_has_a_key_handler(self):
        template = (SKILL_DIR / "assets" / "template.html").read_text(encoding="utf-8")
        viewer = VIEWER_JS.read_text(encoding="utf-8")
        keys = re.findall(r'(?:title|placeholder)="[^"]*\((\S)\)"', template)
        self.assertGreaterEqual(len(keys), 3)
        for key in keys:
            with self.subTest(key=key):
                self.assertIn(f'ev.key === "{key}"', viewer)


class ReproducibleOutputTest(unittest.TestCase):
    @unittest.skipUnless(OKF_BUNDLE.is_dir(), "example OKF bundle not found")
    def test_source_date_epoch_makes_output_byte_identical(self):
        with (
            tempfile.TemporaryDirectory() as tmp,
            mock.patch.dict("os.environ", {"SOURCE_DATE_EPOCH": "1700000000"}),
        ):
            for suffix in (".json", ".html"):
                outs = []
                for n in (1, 2):
                    out = Path(tmp) / f"run{n}{suffix}"
                    code, _, err = run_main(
                        ["compile-okf", str(OKF_BUNDLE), "-o", str(out)]
                    )
                    self.assertEqual(code, 0, err)
                    outs.append(out.read_bytes())
                self.assertEqual(outs[0], outs[1])
            data = json.loads((Path(tmp) / "run1.json").read_text(encoding="utf-8"))
        self.assertEqual(data["generatedAt"], "2023-11-14T22:13:20Z")


MALFORMED_DATASETS = {
    "non-dict edge": ("MALFORMED_EDGE", {"edges": ["x"]}),
    "non-dict trace step": (
        "MALFORMED_STEP",
        {"traces": [{"id": "t", "steps": ["x", 3]}]},
    ),
    "list-valued node id": ("BAD_ID", {"nodes": [{"id": ["a"], "title": "t"}]}),
    "parent cycle": (
        "PARENT_CYCLE",
        {"parentCycle": True},
    ),
}


def _malformed(extra):
    ds = _mutual_cycle_dataset()
    if extra.get("parentCycle"):
        ds["nodes"][1]["parent"] = "b"
        ds["nodes"][2]["parent"] = "a"
        return ds
    for key, value in extra.items():
        ds[key] = ds[key] + value if isinstance(ds[key], list) else value
    return ds


def run_cli(*argv):
    proc = subprocess.run(
        [sys.executable, str(SKILL_DIR / "scripts" / "strata.py"), *map(str, argv)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert "Traceback" not in proc.stdout + proc.stderr, proc.stderr
    return proc


class MalformedInputTest(unittest.TestCase):
    def test_validate_reports_malformed_structures(self):
        for name, (code, extra) in MALFORMED_DATASETS.items():
            with self.subTest(case=name), tempfile.TemporaryDirectory() as tmp:
                src = Path(tmp) / "ds.json"
                src.write_text(json.dumps(_malformed(extra)), encoding="utf-8")
                proc = run_cli("validate", src)
                self.assertEqual(proc.returncode, 1)
                codes = [d["code"] for d in json.loads(proc.stdout)["diagnostics"]]
                self.assertIn(code, codes)

    def test_compile_json_and_build_hub_exit_1_with_json_on_stderr(self):
        for name, (code, extra) in MALFORMED_DATASETS.items():
            for argv in (("compile-json",), ("build-hub",)):
                with self.subTest(case=name, cmd=argv[0]):
                    with tempfile.TemporaryDirectory() as tmp:
                        src = Path(tmp) / "ds.json"
                        src.write_text(json.dumps(_malformed(extra)), encoding="utf-8")
                        proc = run_cli(*argv, src, "-o", Path(tmp) / "out.json")
                    self.assertEqual(proc.returncode, 1)
                    err = json.loads(proc.stderr)
                    self.assertEqual(err["status"], "error")
                    self.assertIn(code, [e["code"] for e in err["errors"]])

    def test_parent_cycle_is_reported_once_and_stays_stable(self):
        ds = _malformed({"parentCycle": True})
        first = strata.validate_dataset(ds)
        self.assertEqual([d["code"] for d in first].count("PARENT_CYCLE"), 1)
        self.assertEqual(strata.validate_dataset(ds), first)

    def test_non_dict_diagnostics_do_not_crash_the_cli(self):
        ds = _mutual_cycle_dataset()
        ds["diagnostics"] = ["x", 3]
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "ds.json"
            src.write_text(json.dumps(ds), encoding="utf-8")
            proc = run_cli("compile-json", src, "-o", Path(tmp) / "out.json")
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_atif_accepts_string_agent_and_json_string_arguments(self):
        doc = _atif_doc("bash", 0, "ok")
        doc["agent"] = "plain-agent"
        doc["steps"][0]["tool_calls"][0]["arguments"] = '{"cmd": "ls -la"}'
        doc["steps"].append("not a step")
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "run.json"
            src.write_text(json.dumps(doc), encoding="utf-8")
            out = Path(tmp) / "out.json"
            proc = run_cli("compile-atif", src, "-o", out)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            text = out.read_text(encoding="utf-8")
        self.assertIn("plain-agent", text)
        self.assertIn("cmd=ls -la", text)

    def test_wrong_yaml_shapes_never_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            kg = Path(tmp) / "kg"
            kg.mkdir()
            (kg / "relations.yaml").write_text("relations: 1\n", encoding="utf-8")
            (kg / "timeline.yaml").write_text("events: true\n", encoding="utf-8")
            proc = run_cli("compile-kg", kg, "-o", Path(tmp) / "kg.json")
            self.assertEqual(proc.returncode, 1)
            self.assertEqual(json.loads(proc.stderr)["status"], "error")

            bundle = Path(tmp) / "b"
            bundle.mkdir()
            (bundle / "a.md").write_text(
                "---\ntype: T\nsources: true\ntags: 3\n---\nBody.\n", encoding="utf-8"
            )
            proc = run_cli("compile-okf", bundle, "-o", Path(tmp) / "b.json")
            self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_atif_non_json_arguments_are_kept_as_raw_text(self):
        self.assertEqual(strata._tool_args("not json"), {"raw": "not json"})
        self.assertEqual(strata._tool_args("[1, 2]"), {"raw": "[1, 2]"})
        self.assertEqual(strata._tool_args(None), {})

    @unittest.skipUnless(importlib.util.find_spec("yaml"), "PyYAML not installed")
    def test_bad_frontmatter_is_a_warning_not_a_crash(self):
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp) / "b"
            bundle.mkdir()
            (bundle / "bad.md").write_text(
                "---\ntitle: [unclosed\ntype: T\n---\nBody.\n", encoding="utf-8"
            )
            (bundle / "good.md").write_text(
                "---\ntype: T\n---\nOK.\n", encoding="utf-8"
            )
            out = Path(tmp) / "out.json"
            proc = run_cli("compile-okf", bundle, "-o", out)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            data = json.loads(out.read_text(encoding="utf-8"))
        diags = [d for d in data["diagnostics"] if d["code"] == "OKF_BAD_FRONTMATTER"]
        self.assertEqual([d["level"] for d in diags], ["warn"])
        self.assertIn("bad.md", diags[0]["message"])
        self.assertEqual(
            {"bad", "good"}, {n["id"] for n in data["nodes"]} & {"bad", "good"}
        )

    def test_bad_yaml_in_kg_files_is_a_json_error(self):
        if not importlib.util.find_spec("yaml"):
            self.skipTest("PyYAML not installed")
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "timeline.yaml").write_text(
                "events: [unclosed\n", encoding="utf-8"
            )
            proc = run_cli("compile-kg", tmp, "-o", Path(tmp) / "out.json")
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(json.loads(proc.stderr)["status"], "error")


def run_main(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = strata.main(argv)
    return code, out.getvalue(), err.getvalue()


class CliTest(unittest.TestCase):
    _run = staticmethod(run_main)

    def _bad_dataset(self):
        ds = _mutual_cycle_dataset()
        ds["edges"].append({"id": "e3", "from": "a", "to": "zzz", "relation": "next"})
        return ds

    def test_compile_commands_exit_1_on_error_diagnostics(self):
        cases = {
            "compile-okf": ("compile_okf", "bundle_dir"),
            "compile-kg": ("compile_kg", "kg.db"),
            "compile-atif": ("compile_atif_decision", "run.json"),
        }
        for cmd, (func, arg) in cases.items():
            with (
                self.subTest(cmd=cmd),
                tempfile.TemporaryDirectory() as tmp,
                mock.patch.object(strata, func, return_value=self._bad_dataset()),
            ):
                out = Path(tmp) / "out.json"
                code, stdout, err = self._run(
                    [cmd, str(Path(tmp) / arg), "-o", str(out)]
                )
                self.assertEqual(code, 1)
                self.assertIn("DANGLING_EDGE", err)
                self.assertNotIn('"status": "ok"', stdout)
                self.assertFalse(out.exists())

    def test_compile_okf_exits_1_for_duplicate_concept_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp) / "bundle"
            (bundle / "a").mkdir(parents=True)
            (bundle / "a" / "b.md").write_text("---\ntype: T\n---\n", encoding="utf-8")
            (bundle / "a:b.md").write_text("---\ntype: T\n---\n", encoding="utf-8")
            code, _, err = self._run(
                ["compile-okf", str(bundle), "-o", str(Path(tmp) / "o.json")]
            )
        self.assertEqual(code, 1)
        self.assertIn("DUPLICATE_ID", err)

    def test_every_subcommand_reports_bad_input_as_json_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = str(Path(tmp) / "missing")
            bad = Path(tmp) / "bad.json"
            bad.write_text("{not json", encoding="utf-8")
            out = str(Path(tmp) / "out.json")
            cases = []
            for path in (missing, str(bad)):
                cases += [
                    ["compile-okf", path, "-o", out],
                    ["compile-kg", path, "-o", out],
                    ["compile-atif", path, "-o", out],
                    ["compile-json", path, "-o", out],
                    ["validate", path],
                    ["build-hub", path, "-o", out],
                ]
            cases.append(["validate", str(Path(tmp))])
            for argv in cases:
                with self.subTest(argv=argv[:2]):
                    code, stdout, err = self._run(argv)
                    self.assertEqual(code, 1)
                    self.assertEqual(json.loads(err)["status"], "error")
                    self.assertNotIn('"status": "ok"', stdout)

    def test_non_object_json_is_a_json_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "list.json"
            src.write_text("[1, 2]", encoding="utf-8")
            code, _, err = self._run(["validate", str(src)])
        self.assertEqual(code, 1)
        self.assertIn("not a JSON object", json.loads(err)["error"])

    def test_unknown_output_suffix_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "ds.json"
            src.write_text(json.dumps(_mutual_cycle_dataset()), encoding="utf-8")
            for suffix, expected in (
                (".hmtl", 1),
                (".txt", 1),
                (".htm", 0),
                (".json", 0),
            ):
                with self.subTest(suffix=suffix):
                    out = Path(tmp) / f"map{suffix}"
                    code, _, err = self._run(["compile-json", str(src), "-o", str(out)])
                    self.assertEqual(code, expected, err)
                    self.assertEqual(out.exists(), expected == 0)
                    if expected:
                        self.assertIn(".html", json.loads(err)["error"])

    def test_compile_atif_reports_the_effective_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / "a.json", Path(tmp) / "b.json"
            a.write_text(json.dumps(_atif_doc("bash", 0, "ok")), encoding="utf-8")
            b.write_text(json.dumps(_atif_doc("bash", 0, "ok")), encoding="utf-8")
            out = Path(tmp) / "o.json"
            code, stdout, _ = self._run(
                ["compile-atif", str(a), str(b), "--mode", "decision", "-o", str(out)]
            )
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(stdout)["mode"], "compare")
            code, stdout, _ = self._run(["compile-atif", str(a), "-o", str(out)])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(stdout)["mode"], "decision")

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

    def test_compile_kg_rejects_missing_empty_and_non_sqlite_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            empty_dir = Path(tmp) / "empty"
            empty_dir.mkdir()
            text_file = Path(tmp) / "notes.txt"
            text_file.write_text("not a database", encoding="utf-8")
            for target in (Path(tmp) / "missing", empty_dir, text_file):
                with self.subTest(target=target.name):
                    out = Path(tmp) / f"{target.name}.json"
                    code, stdout, err = self._run(
                        ["compile-kg", str(target), "-o", str(out)]
                    )
                    self.assertEqual(code, 1)
                    self.assertEqual(stdout, "")
                    self.assertIn('"status": "error"', err)
                    self.assertFalse(out.exists())

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


class AtifTokenTest(unittest.TestCase):
    def test_step_tokens_are_counted_once_across_tool_calls(self):
        call = {"function_name": "bash", "arguments": {}}
        doc = {
            "steps": [
                {
                    "source": "agent",
                    "message": "run three",
                    "metrics": {"prompt_tokens": 10, "completion_tokens": 5},
                    "tool_calls": [
                        {**call, "tool_call_id": "a"},
                        {**call, "tool_call_id": "b"},
                        {**call, "tool_call_id": "c"},
                    ],
                }
            ]
        }
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "run.json"
            src.write_text(json.dumps(doc), encoding="utf-8")
            norm = strata.normalize_trajectory_file(src)
        self.assertEqual([e["tokens"] for e in norm["events"]], [15, 0, 0])
        self.assertEqual(norm["total_tokens"], 15)


ROWS = [{"type": "USER_INPUT", "content": "Do the thing"}]


class JetskiIdTest(unittest.TestCase):
    def test_system_generated_path_uses_the_session_directory(self):
        path = Path(
            "/data/brain/abcdef123456-7890-session/.system_generated/logs/transcript.jsonl"
        )
        norm = strata._normalize_jetski_jsonl(path, ROWS)
        self.assertEqual(norm["id"], "abcdef123456")
        self.assertEqual(norm["title"], "Jetski transcript abcdef123456")

    def test_other_paths_use_the_file_stem(self):
        norm = strata._normalize_jetski_jsonl(Path("/tmp/run-7.jsonl"), ROWS)
        self.assertEqual(norm["id"], "run-7")


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
        # The run ends on the failure, so no return arc is wired or reported.
        self.assertFalse([e for e in ds["edges"] if e["flowRole"] == "backtrack"])
        self.assertIn("0 ↺ backtrack", ds["subtitle"])
        messages = " ".join(d["message"] for d in ds["diagnostics"])
        self.assertNotIn("backtrack arc", messages)

    def test_goal_step_only_when_final_event_succeeds(self):
        ds = self._compile([_atif_doc("bash", 0, "ok"), _atif_doc("bash", 1, "bad")])
        ok, failed = ds["traces"]
        self.assertEqual(ok["steps"][-1]["label"], "Trajectory Goal Reached")
        self.assertNotIn(
            "Trajectory Goal Reached", [s["label"] for s in failed["steps"]]
        )
        self.assertIn("R1..R2", ds["subtitle"])

    def test_only_the_last_step_produces_the_outcome(self):
        steps = [_atif_doc("read_file", 0, "x")["steps"][0] for _ in range(3)]
        steps.append(_atif_doc("bash", 0, "done")["steps"][0])
        doc = {"schema_version": "ATIF-v1.4", "steps": steps}
        ds = self._compile([doc])
        outcome = [e for e in ds["edges"] if e["relation"] == "produces-outcome"]
        self.assertEqual(
            [(e["from"], e["to"]) for e in outcome],
            [("cap:shell_exec", "state:synthesis")],
        )
        self.assertIn("Traversed 1×", outcome[0]["summary"])

    def test_jetski_and_atif_file_reads_share_one_node(self):
        jetski = _jsonl(
            [
                {"type": "USER_INPUT", "content": "Look"},
                {
                    "type": "PLANNER_RESPONSE",
                    "tool_calls": [{"name": "view_file", "args": {"Path": "/a"}}],
                },
                {"type": "GENERIC", "status": "DONE", "content": "ok"},
            ]
        )
        with tempfile.TemporaryDirectory() as tmp:
            a = Path(tmp) / "jetski.jsonl"
            a.write_text(jetski, encoding="utf-8")
            b = Path(tmp) / "atif.json"
            b.write_text(json.dumps(_atif_doc("read_file", 0, "ok")), encoding="utf-8")
            ds = strata.compile_atif_compare([a, b])
        ids = {n["id"] for n in ds["nodes"]}
        self.assertIn("cap:file_inspect", ids)
        self.assertNotIn("cap:view_file", ids)
        self.assertNotIn("cap:read_file", ids)
        touched = {e["from"] for e in ds["edges"] if e["to"] == "cap:file_inspect"} | {
            e["to"] for e in ds["edges"] if e["from"] == "cap:file_inspect"
        }
        self.assertTrue(touched)

    def test_tool_name_table_covers_both_vocabularies(self):
        by_name = strata.TOOL_BUCKET_BY_NAME
        for name in ("read_file", "view_file", "grep_search"):
            self.assertEqual(by_name[name], "read")
        for name in ("write_file", "edit_file", "replace_file_content"):
            self.assertEqual(by_name[name], "write")
        for name in ("bash", "run_command"):
            self.assertEqual(by_name[name], "shell")
        self.assertEqual(by_name["invoke_subagent"], "subagent")

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
