#!/usr/bin/env python3
"""
Automated Verification & Unit Test Suite for Asciinema Explainer Walkthroughs
Tests PTY session handling, time-clamping compression, secret redaction,
chapter markers, ANSI stripping, banner generation, HTML walkthrough building,
and Asciicast v2 schema compliance.
"""

import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from scripts.banner import make_banner, strip_ansi as banner_strip_ansi, visual_len
from scripts.build_walkthrough import (
    parse_cast_file,
    render_html_walkthrough,
    validate_cast,
)
from scripts.pty_recorder_template import (
    DEFAULT_REDACTION_PATTERNS,
    SynchronousPTYRecorder,
    strip_ansi,
)


class TestAsciinemaRecorderEngine(unittest.TestCase):

    def test_comprehensive_redaction_patterns(self):
        """Verify that all sensitive tokens and secrets are securely redacted."""
        rec = SynchronousPTYRecorder()
        mock_refresh = "1//" + "04_mock_refresh_token_" + "a" * 25
        mock_bearer = "ya" + "29." + "mock_bearer_token_" + "b" * 35
        mock_apikey = "AIza" + "Sy" + "mock_api_key_" + "c" * 25
        mock_ghp = "ghp_" + "mockGitHubPatToken1234567890abcdef"
        mock_gh_pat = "github_pat_" + "mockPatToken1234567890abcdef"
        mock_ant = "sk-ant-" + "mockAnthropicKey1234567890abcdef"
        mock_oai = "sk-" + "mockOpenAIKey1234567890abcdef123456"
        mock_aws = "AKIA" + "IOSFODNN7EXAMPLE"
        mock_priv_key = "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA0mockkey...\n-----END RSA PRIVATE KEY-----"
        mock_auth_header = "Authorization: Bearer my_super_secret_access_jwt_token_123"

        sample_text = f"""
OAuth refresh: {mock_refresh}
OAuth bearer: {mock_bearer}
Google API Key: {mock_apikey}
GitHub PAT: {mock_ghp}
GitHub Fine-Grained PAT: {mock_gh_pat}
Anthropic API Key: {mock_ant}
OpenAI API Key: {mock_oai}
AWS Access Key: {mock_aws}
Private Key Block:
{mock_priv_key}
Auth Header: {mock_auth_header}
client_secret: "super_secret_password_here"
"""
        sanitized = rec.redact_text(sample_text)

        # Verify raw tokens are stripped
        for secret in [mock_refresh, mock_bearer, mock_apikey, mock_ghp, mock_gh_pat, mock_ant, mock_oai, mock_aws, mock_priv_key]:
            self.assertNotIn(secret, sanitized)

        # Verify replacement placeholders
        self.assertIn("[REDACTED_REFRESH_TOKEN]", sanitized)
        self.assertIn("[REDACTED_ACCESS_TOKEN]", sanitized)
        self.assertIn("[REDACTED_API_KEY]", sanitized)
        self.assertIn("[REDACTED_GITHUB_TOKEN]", sanitized)
        self.assertIn("[REDACTED_ANTHROPIC_KEY]", sanitized)
        self.assertIn("[REDACTED_OPENAI_KEY]", sanitized)
        self.assertIn("[REDACTED_AWS_KEY]", sanitized)
        self.assertIn("[REDACTED_PRIVATE_KEY]", sanitized)
        self.assertIn("[REDACTED_BEARER_TOKEN]", sanitized)
        self.assertIn("[REDACTED_CLIENT_SECRET]", sanitized)

    def test_ansi_stripping_and_assertions(self):
        """Verify that ANSI escape codes are stripped cleanly for assertion checking."""
        rec = SynchronousPTYRecorder()
        colored_output = "\033[1;32m✓ Step 1: Initialization Successful\033[0m\r\n\033[34m[INFO] Ready.\033[0m"
        rec.recent_buffer = colored_output

        plain = strip_ansi(colored_output)
        self.assertEqual(plain, "✓ Step 1: Initialization Successful\r\n[INFO] Ready.")

        # Test output assertion with and without formatting
        rec.assert_recent_output("Step 1: Initialization Successful")
        rec.assert_recent_output("[INFO] Ready.")
        rec.assert_no_errors()

        # Test error detection
        rec.recent_buffer += "\r\nTraceback (most recent call last):\r\n  File 'app.py', line 10"
        with self.assertRaises(AssertionError):
            rec.assert_no_errors()

    def test_banner_generator(self):
        """Verify banner generation alignment, width, and styles."""
        banner_112 = make_banner(
            title="Capability Discovery",
            subtitle="Agent queries registry",
            step=1,
            width=112,
            color="cyan",
            style="double",
        )
        lines = banner_112.split("\n")
        self.assertEqual(len(lines), 4)  # Top, Title, Subtitle, Bottom
        for line in lines:
            self.assertEqual(visual_len(line), 112)

        # Test Center Alignment
        banner_centered = make_banner(
            title="CENTERED TITLE",
            subtitle="Centered description",
            width=100,
            align="center",
            style="rounded",
        )
        c_lines = banner_centered.split("\n")
        for line in c_lines:
            self.assertEqual(visual_len(line), 100)

    def test_idleness_compression(self):
        """Verify that idle gaps > max_idle are clamped mathematically."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cast_path = Path(tmpdir) / "test_compress.cast"
            rec = SynchronousPTYRecorder()
            rec.start_time = 1000.0

            # Simulate 4 events with a 30-second idle gap
            rec.events = [
                (0.0, "o", "."),
                (0.5, "o", "ls\r\n"),
                (30.5, "o", "file1.txt  file2.txt\r\n"),
                (32.0, "o", "exit\r\n"),
            ]
            rec.export(filepath=cast_path, max_idle=2.5)

            with open(cast_path, "r", encoding="utf-8") as f:
                lines = [json.loads(line) for line in f]

            header = lines[0]
            self.assertEqual(header["version"], 2)
            self.assertEqual(header["width"], 112)
            self.assertEqual(header["height"], 34)

            events = lines[1:]
            self.assertEqual(len(events), 4)
            # Timestamps: 0.0 -> 0.5 -> (0.5 + 2.5 = 3.0) -> (3.0 + 1.5 = 4.5)
            self.assertAlmostEqual(events[0][0], 0.0, places=2)
            self.assertAlmostEqual(events[1][0], 0.5, places=2)
            self.assertAlmostEqual(events[2][0], 3.0, places=2)
            self.assertAlmostEqual(events[3][0], 4.5, places=2)

    def test_chapter_markers(self):
        """Verify that chapter markers ('m') are injected and formatted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cast_path = Path(tmpdir) / "test_markers.cast"
            rec = SynchronousPTYRecorder()
            rec.start_time = 1000.0

            rec.events = [
                (0.0, "o", "."),
                (1.0, "m", "Step 1: Initialization"),
                (2.0, "o", "init complete\r\n"),
                (5.0, "m", "Step 2: Execution"),
                (6.0, "o", "done\r\n"),
            ]
            rec.export(filepath=cast_path, max_idle=2.0)

            with open(cast_path, "r", encoding="utf-8") as f:
                lines = [json.loads(line) for line in f]

            events = lines[1:]
            marker_events = [e for e in events if e[1] == "m"]
            self.assertEqual(len(marker_events), 2)
            self.assertEqual(marker_events[0][2], "Step 1: Initialization")
            self.assertEqual(marker_events[1][2], "Step 2: Execution")

    def test_walkthrough_builder_and_html_generation(self):
        """Verify parse_cast_file, validate_cast, and HTML rendering."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cast_path = Path(tmpdir) / "sample.cast"
            html_path = Path(tmpdir) / "index.html"

            # Create sample valid cast
            header = {"version": 2, "width": 112, "height": 34, "timestamp": 1234567890}
            events = [
                [0.0, "o", "developer@workstation:~$ ./scripts/banner.sh 1\r\n"],
                [1.0, "m", "Step 1: Discover"],
                [2.0, "o", "Discovered 5 skills\r\n"],
                [5.0, "m", "Step 2: Run"],
                [6.0, "o", "Completed with success!\r\n"],
            ]
            with open(cast_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(header) + "\n")
                for ev in events:
                    f.write(json.dumps(ev) + "\n")

            # Validate cast
            self.assertTrue(validate_cast(cast_path))

            # Parse cast
            parsed = parse_cast_file(cast_path)
            self.assertEqual(len(parsed["markers"]), 2)
            self.assertEqual(parsed["markers"][0][1], "Step 1: Discover")
            self.assertIn("Completed with success!", parsed["transcript"])

            # Render HTML
            render_html_walkthrough(
                cast_path=cast_path,
                output_html_path=html_path,
                title="Custom Demo Title",
                subtitle="Custom Subtitle",
            )
            self.assertTrue(html_path.exists())

            with open(html_path, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn("Custom Demo Title", content)
            self.assertIn("Step 1: Discover", content)
            self.assertIn("Step 2: Run", content)
            self.assertIn("asciinema-player", content)
            self.assertIn("mermaid", content)

    def test_live_pty_synchronization(self):
        """Test real PTY master/slave execution and prompt return synchronization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cast_path = Path(tmpdir) / "test_live.cast"
            rec = SynchronousPTYRecorder(cols=100, rows=30)
            rec.start(cwd=Path(tmpdir))
            try:
                rec.execute_and_verify(
                    cmd="echo 'PTY_VERIFICATION_TOKEN_SUCCESS'",
                    expected_substrings=["PTY_VERIFICATION_TOKEN_SUCCESS"],
                    marker_label="Verification Step",
                    pause_after=0.2,
                )
            finally:
                rec.stop()
                rec.export(filepath=cast_path)

            self.assertTrue(cast_path.exists())
            summary = rec.generate_summary()
            self.assertEqual(summary["cols"], 100)
            self.assertEqual(summary["rows"], 30)
            self.assertGreaterEqual(summary["turns_executed"], 1)

            with open(cast_path, "r", encoding="utf-8") as f:
                lines = [json.loads(line) for line in f]

            header = lines[0]
            self.assertEqual(header["version"], 2)
            self.assertEqual(header["width"], 100)
            self.assertEqual(header["height"], 30)

            full_text = "".join(e[2] for e in lines[1:] if e[1] == "o")
            self.assertIn("PTY_VERIFICATION_TOKEN_SUCCESS", full_text)


if __name__ == "__main__":
    unittest.main()
