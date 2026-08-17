#!/usr/bin/env python3
"""
Automated Verification & Unit Test Suite for Asciinema Explainer Walkthroughs
Tests PTY session handling, time-clamping compression, secret redaction,
chapter markers, and Asciicast v2 schema compliance.
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

from scripts.pty_recorder_template import (
    DEFAULT_REDACTION_PATTERNS,
    SynchronousPTYRecorder,
)


class TestAsciinemaRecorderEngine(unittest.TestCase):

    def test_redaction_patterns(self):
        """Verify that sensitive tokens and secrets are redacted."""
        rec = SynchronousPTYRecorder()
        mock_refresh = "1//" + "04_mock_refresh_token_" + "a" * 25
        mock_bearer = "ya" + "29." + "mock_bearer_token_" + "b" * 35
        mock_apikey = "AIza" + "Sy" + "mock_api_key_" + "c" * 25
        sample_text = (
            f"OAuth token: {mock_refresh}\n"
            f"Bearer token: {mock_bearer}\n"
            f"API Key: {mock_apikey}\n"
            'client_secret: "super_secret_password_here"'
        )
        sanitized = rec.redact_text(sample_text)
        self.assertNotIn(mock_refresh, sanitized)
        self.assertNotIn(mock_bearer, sanitized)
        self.assertNotIn(mock_apikey, sanitized)
        self.assertNotIn("super_secret_password_here", sanitized)
        self.assertIn("[REDACTED_REFRESH_TOKEN]", sanitized)
        self.assertIn("[REDACTED_ACCESS_TOKEN]", sanitized)
        self.assertIn("[REDACTED_API_KEY]", sanitized)
        self.assertIn('[REDACTED_CLIENT_SECRET]', sanitized)

    def test_idleness_compression(self):
        """Verify that idle gaps > max_idle are clamped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cast_path = Path(tmpdir) / "test_compress.cast"
            rec = SynchronousPTYRecorder()
            rec.start_time = 1000.0

            # Simulate 3 events with a 30-second idle gap
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
            # Check timestamps: 0.0 -> 0.5 -> (0.5 + 2.5 = 3.0) -> (3.0 + 1.5 = 4.5)
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

    def test_live_pty_synchronization(self):
        """Test real PTY master/slave execution and prompt return synchronization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cast_path = Path(tmpdir) / "test_live.cast"
            rec = SynchronousPTYRecorder(cols=100, rows=30)
            rec.start(cwd=Path(tmpdir))
            try:
                rec.send_turn(
                    "echo 'PTY_VERIFICATION_TOKEN_SUCCESS'",
                    pause_after=0.2,
                    marker_label="Verification Step",
                )
                rec.assert_recent_output("PTY_VERIFICATION_TOKEN_SUCCESS")
            finally:
                rec.stop()
                rec.export(filepath=cast_path)

            self.assertTrue(cast_path.exists())
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
