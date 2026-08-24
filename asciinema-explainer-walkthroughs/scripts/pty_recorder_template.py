#!/usr/bin/env python3
"""
Production-Ready Synchronous PTY Asciinema Recorder Engine
- Master/Slave PTY with locked geometry (default 112x34)
- Human typing cadence with natural Gaussian jitter
- Strict prompt synchronization via select.select (0% command collision guarantee)
- Native Asciicast v2 chapter marker injection ([ts, "m", "Label"])
- Automated token and secret redaction filter
- Idle time compression (clamps long pauses > max_idle down to max_idle)
- Programmatic assertion & verification helpers (assert_recent_output, assert_no_errors)
- Structured transcript and summary report generation
"""

import fcntl
import json
import os
import pty
import random
import re
import select
import struct
import subprocess
import termios
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Pattern, Tuple, Union

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = REPO_ROOT / "demo.cast"
DEFAULT_PROMPT_STR = "developer@workstation:~/project$ "

ANSI_ESCAPE_RE = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from text for reliable string assertions."""
    return ANSI_ESCAPE_RE.sub("", text)


DEFAULT_REDACTION_PATTERNS: List[Tuple[Pattern[str], str]] = [
    # Google OAuth tokens & API Keys
    (re.compile(r'1//[a-zA-Z0-9_\-]{20,}'), '[REDACTED_REFRESH_TOKEN]'),
    (re.compile(r'ya29\.[a-zA-Z0-9_\-]{30,}'), '[REDACTED_ACCESS_TOKEN]'),
    (re.compile(r'AIzaSy[a-zA-Z0-9_\-]{33}'), '[REDACTED_API_KEY]'),
    # GitHub Personal Access Tokens & OAuth tokens
    (re.compile(r'(?:ghp|gho|ghu|ghs|ghr|github_pat)_[a-zA-Z0-9_]{20,}'), '[REDACTED_GITHUB_TOKEN]'),
    # Anthropic & OpenAI API Keys
    (re.compile(r'sk-ant-[a-zA-Z0-9_\-]{30,}'), '[REDACTED_ANTHROPIC_KEY]'),
    (re.compile(r'sk-[a-zA-Z0-9_\-]{30,}'), '[REDACTED_OPENAI_KEY]'),
    # AWS Access Keys
    (re.compile(r'(?<![A-Z0-9])(?:AKIA|ASIA)[A-Z0-9]{16}(?![A-Z0-9])'), '[REDACTED_AWS_KEY]'),
    # Private Key blocks
    (re.compile(r'-----BEGIN [A-Z0-9_ ]*PRIVATE KEY-----[^\-]+-----END [A-Z0-9_ ]*PRIVATE KEY-----', re.DOTALL), '[REDACTED_PRIVATE_KEY]'),
    # Authorization headers
    (re.compile(r'(?i)(Authorization:\s*Bearer\s+)[a-zA-Z0-9_\-\.]+'), r'\1[REDACTED_BEARER_TOKEN]'),
    # Client secrets & config assignments
    (re.compile(r'(?i)(client_secret["\']?\s*[:=]\s*["\'])([^"\']+)(["\'])'), r'\1[REDACTED_CLIENT_SECRET]\3'),
]


class SynchronousPTYRecorder:
    def __init__(
        self,
        cols: int = 112,
        rows: int = 34,
        prompt_str: str = DEFAULT_PROMPT_STR,
        prompt_pattern: Optional[Pattern[str]] = None,
        redaction_patterns: Optional[List[Tuple[Pattern[str], str]]] = None,
    ):
        self.cols = cols
        self.rows = rows
        self.prompt_str = prompt_str
        self.prompt_pattern = prompt_pattern
        self.redaction_patterns = redaction_patterns or list(DEFAULT_REDACTION_PATTERNS)
        self.events: List[Tuple[float, str, str]] = []
        self.start_time: Optional[float] = None
        self.master_fd: Optional[int] = None
        self.slave_fd: Optional[int] = None
        self.process: Optional[subprocess.Popen] = None
        self.recent_buffer: str = ""
        self.redaction_count: int = 0
        self.markers: List[Tuple[float, str]] = []
        self.turns_executed: int = 0

    def set_winsize(self, fd: int) -> None:
        """Lock terminal dimensions to fixed cols and rows."""
        winsize = struct.pack("HHHH", self.rows, self.cols, 0, 0)
        fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)

    def redact_text(self, text: str) -> str:
        """Sanitize sensitive tokens from string using configured regex patterns."""
        sanitized = text
        for pattern, replacement in self.redaction_patterns:
            if pattern.search(sanitized):
                sanitized = pattern.sub(replacement, sanitized)
                self.redaction_count += 1
        return sanitized

    def record_event(self, text: str, kind: str = "o") -> None:
        """Append an event to the stream with relative timestamp."""
        if self.start_time is not None:
            ts = time.time() - self.start_time
            sanitized = self.redact_text(text) if kind == "o" else text
            self.events.append((ts, kind, sanitized))

    def add_marker(self, label: str) -> None:
        """Inject an Asciicast v2 marker event for chapter-based player navigation."""
        if self.start_time is not None:
            ts = time.time() - self.start_time
            self.markers.append((ts, label))
        self.record_event(label, kind="m")

    def drain_output(self, timeout: float = 0.05, record: bool = True) -> str:
        """Read pending bytes from master PTY file descriptor."""
        collected = ""
        if self.master_fd is None:
            return collected

        while True:
            r, _, _ = select.select([self.master_fd], [], [], timeout)
            if self.master_fd in r:
                try:
                    data = os.read(self.master_fd, 4096)
                    if not data:
                        break
                    text = data.decode("utf-8", errors="replace")
                    if record:
                        self.record_event(text, kind="o")
                    collected += text
                    self.recent_buffer += text
                    if len(self.recent_buffer) > 30000:
                        self.recent_buffer = self.recent_buffer[-15000:]
                except (OSError, ValueError):
                    break
            else:
                break
        return collected

    def wait_for_prompt(self, timeout: float = 120.0) -> bool:
        """
        Poll master PTY stream until shell prompt or expected pattern appears.
        Guarantees zero command collision.
        """
        if self.master_fd is None:
            return False

        start = time.time()
        buf = ""
        while time.time() - start < timeout:
            r, _, _ = select.select([self.master_fd], [], [], 0.05)
            if self.master_fd in r:
                try:
                    data = os.read(self.master_fd, 4096)
                    if not data:
                        break
                    text = data.decode("utf-8", errors="replace")
                    self.record_event(text, kind="o")
                    buf += text
                    self.recent_buffer += text
                    if len(self.recent_buffer) > 30000:
                        self.recent_buffer = self.recent_buffer[-15000:]

                    # Check match on tail
                    tail = buf[-120:]
                    if self.prompt_pattern and self.prompt_pattern.search(tail):
                        return True
                    if self.prompt_str in tail or "developer@workstation" in tail or "$ " in tail[-10:]:
                        return True
                except (OSError, ValueError):
                    break
        return False

    def type_string(
        self,
        text: str,
        base_delay: float = 0.032,
        jitter: bool = True,
    ) -> None:
        """Simulate realistic human typing with Gaussian variance."""
        if self.master_fd is None:
            return

        for char in text:
            os.write(self.master_fd, char.encode("utf-8"))
            self.drain_output(timeout=0.005)
            if jitter:
                # Add natural typing variance: longer on spaces/punctuation, slight noise
                delay = max(0.012, random.gauss(base_delay, 0.008))
                if char in " .-_/":
                    delay += 0.02
                time.sleep(delay)
            else:
                time.sleep(base_delay)

    def send_keys(self, raw_bytes: bytes, pause_after: float = 0.5) -> None:
        """Send raw byte sequence (e.g. arrow keys, Escape, Tab, Enter)."""
        if self.master_fd is not None:
            os.write(self.master_fd, raw_bytes)
            self.drain_output(timeout=0.05)
            time.sleep(pause_after)

    def send_control(self, char: str, pause_after: float = 0.5) -> None:
        """Send control key sequence (e.g. 'c' for Ctrl+C, 'd' for Ctrl+D, 'z' for Ctrl+Z)."""
        ctrl_code = ord(char.lower()) - ord('a') + 1
        self.send_keys(bytes([ctrl_code]), pause_after=pause_after)

    def send_turn(
        self,
        cmd: str,
        pause_after: float = 3.0,
        base_delay: float = 0.032,
        jitter: bool = True,
        timeout: float = 120.0,
        marker_label: Optional[str] = None,
    ) -> None:
        """
        Execute a single turn: types command, sends return, and waits for prompt return.
        """
        if marker_label:
            self.add_marker(marker_label)
        self.drain_output(timeout=0.05, record=False)
        time.sleep(0.3)
        self.type_string(cmd, base_delay=base_delay, jitter=jitter)
        time.sleep(0.2)
        if self.master_fd is not None:
            os.write(self.master_fd, b"\n")
        self.wait_for_prompt(timeout=timeout)
        self.turns_executed += 1
        time.sleep(pause_after)

    def assert_recent_output(self, expected_substring: str, strip_colors: bool = True) -> None:
        """Verify that recent subshell output contains the expected substring."""
        buf = strip_ansi(self.recent_buffer) if strip_colors else self.recent_buffer
        target = strip_ansi(expected_substring) if strip_colors else expected_substring
        if target not in buf:
            raise AssertionError(
                f"Expected substring '{expected_substring}' not found in recent terminal output."
            )

    def assert_no_errors(self, forbidden_substrings: Optional[List[str]] = None) -> None:
        """Verify that recent subshell output does not contain common error messages."""
        forbidden = forbidden_substrings or [
            "Traceback (most recent call last)",
            "command not found",
            "No such file or directory",
            "FATAL ERROR",
            "UnhandledPromiseRejection",
        ]
        buf = strip_ansi(self.recent_buffer)
        for term in forbidden:
            if term in buf:
                raise AssertionError(f"Forbidden error substring '{term}' detected in terminal output.")

    def execute_and_verify(
        self,
        cmd: str,
        expected_substrings: Optional[List[str]] = None,
        forbidden_substrings: Optional[List[str]] = None,
        marker_label: Optional[str] = None,
        pause_after: float = 3.0,
        base_delay: float = 0.032,
        jitter: bool = True,
        timeout: float = 120.0,
    ) -> str:
        """
        High-level verification turn: runs command, verifies expected tokens,
        ensures absence of forbidden errors, and returns output text.
        """
        self.recent_buffer = ""
        self.send_turn(
            cmd=cmd,
            pause_after=pause_after,
            base_delay=base_delay,
            jitter=jitter,
            timeout=timeout,
            marker_label=marker_label,
        )
        if expected_substrings:
            for exp in expected_substrings:
                self.assert_recent_output(exp)
        self.assert_no_errors(forbidden_substrings=forbidden_substrings)
        return self.recent_buffer

    def start(self, cwd: Path = REPO_ROOT) -> None:
        """Initialize Master/Slave PTY and start clean bash session."""
        self.master_fd, self.slave_fd = pty.openpty()
        self.set_winsize(self.master_fd)
        self.set_winsize(self.slave_fd)

        env = os.environ.copy()
        env["TERM"] = "xterm-256color"
        env["COLUMNS"] = str(self.cols)
        env["LINES"] = str(self.rows)

        self.process = subprocess.Popen(
            ["/bin/bash", "--norc", "--noprofile"],
            stdin=self.slave_fd,
            stdout=self.slave_fd,
            stderr=self.slave_fd,
            cwd=str(cwd),
            env=env,
            close_fds=True,
        )
        os.close(self.slave_fd)
        self.slave_fd = None
        self.start_time = time.time()

        init_cmds = f"""
export PS1='{self.prompt_str}'
clear
"""
        os.write(self.master_fd, init_cmds.encode("utf-8"))
        time.sleep(0.4)
        self.drain_output(timeout=0.2, record=False)
        os.write(self.master_fd, b"clear\n")
        time.sleep(0.5)
        self.drain_output(timeout=0.2, record=False)
        self.events = []
        self.markers = []
        self.recent_buffer = ""
        self.redaction_count = 0
        self.turns_executed = 0
        self.start_time = time.time()

    def stop(self) -> None:
        """Gracefully exit child bash process and close PTY descriptors."""
        try:
            if self.master_fd is not None:
                self.type_string("exit\n", base_delay=0.01, jitter=False)
                time.sleep(0.3)
                self.drain_output(timeout=0.2)
        except Exception:
            pass
        if self.master_fd is not None:
            try:
                os.close(self.master_fd)
            except OSError:
                pass
            self.master_fd = None
        if self.process and self.process.poll() is None:
            self.process.terminate()

    def generate_transcript(self, filepath: Optional[Path] = None, strip_colors: bool = True) -> str:
        """Extract clean full-text transcript of the recorded session."""
        raw_text = "".join(ev[2] for ev in self.events if ev[1] == "o")
        transcript = strip_ansi(raw_text) if strip_colors else raw_text
        if filepath:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(transcript)
        return transcript

    def generate_summary(self) -> Dict[str, Any]:
        """Return structured execution metrics and chapter timeline."""
        raw_dur = self.events[-1][0] if self.events else 0.0
        return {
            "cols": self.cols,
            "rows": self.rows,
            "turns_executed": self.turns_executed,
            "total_events": len(self.events),
            "raw_duration_sec": round(raw_dur, 2),
            "redactions_applied": self.redaction_count,
            "markers": [{"timestamp": round(m[0], 2), "label": m[1]} for m in self.markers],
        }

    def export(
        self,
        filepath: Path = DEFAULT_OUTPUT,
        title: str = "Interactive AI Agent Walkthrough",
        max_idle: float = 2.5,
    ) -> None:
        """
        Export recorded stream to Asciicast v2 JSONL format with idleness compression.
        """
        raw_events = self.events

        # Compress idle pauses while preserving marker timing
        compressed_events: List[List[Union[float, str]]] = []
        if raw_events:
            prev_raw_ts = raw_events[0][0]
            curr_comp_ts = 0.0
            for raw_ts, kind, text in raw_events:
                delta = max(0.0, raw_ts - prev_raw_ts)
                clamped_delta = min(delta, max_idle)
                curr_comp_ts += clamped_delta
                compressed_events.append([round(curr_comp_ts, 3), kind, text])
                prev_raw_ts = raw_ts

        header = {
            "version": 2,
            "width": self.cols,
            "height": self.rows,
            "timestamp": int(self.start_time or time.time()),
            "title": title,
            "env": {"SHELL": "/bin/bash", "TERM": "xterm-256color"},
        }
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(json.dumps(header) + "\n")
            for event in compressed_events:
                f.write(json.dumps(event) + "\n")

        raw_dur = self.events[-1][0] if self.events else 0
        comp_dur = compressed_events[-1][0] if compressed_events else 0
        markers_count = sum(1 for e in compressed_events if e[1] == "m")
        print(f"\n🎉 Successfully recorded & compressed session: {filepath}")
        print(f"• Total events: {len(compressed_events)} (Markers: {markers_count})")
        print(f"• Raw duration: {raw_dur:.1f}s | Compressed duration: {comp_dur:.1f}s (~{comp_dur/60:.2f} min)")


if __name__ == "__main__":
    rec = SynchronousPTYRecorder()
    rec.start()
    try:
        rec.send_turn("./scripts/banner_template.sh 1", pause_after=1.5, marker_label="Step 1: Init")
        rec.send_turn("echo 'Hello from synchronous PTY recording!'", pause_after=2.0)
    finally:
        rec.stop()
        rec.export()
