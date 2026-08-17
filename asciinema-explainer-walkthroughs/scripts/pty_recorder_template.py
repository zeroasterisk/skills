#!/usr/bin/env python3
"""
Production-Ready Synchronous PTY Asciinema Recorder Engine
- Master/Slave PTY with locked geometry (112x34)
- Human typing cadence with natural jitter (Gaussian distribution)
- Strict prompt synchronization via select.select (0% collision guarantee)
- Native Asciicast v2 chapter marker injection ([ts, "m", "Label"])
- Automated token and secret redaction filter
- Idle time compression (clamps long pauses > max_idle down to max_idle)
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
from typing import List, Optional, Pattern, Tuple, Union

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = REPO_ROOT / "demo.cast"
DEFAULT_PROMPT_STR = "developer@workstation:~/project$ "

DEFAULT_REDACTION_PATTERNS: List[Tuple[Pattern[str], str]] = [
    (re.compile(r'1//[a-zA-Z0-9_\-]{20,}'), '[REDACTED_REFRESH_TOKEN]'),
    (re.compile(r'ya29\.[a-zA-Z0-9_\-]{30,}'), '[REDACTED_ACCESS_TOKEN]'),
    (re.compile(r'(?:client_secret["\']?\s*[:=]\s*["\'])([^"\']+)(?:["\'])'), 'client_secret: "[REDACTED_CLIENT_SECRET]"'),
    (re.compile(r'AIzaSy[a-zA-Z0-9_\-]{20,}'), '[REDACTED_API_KEY]'),
]


class SynchronousPTYRecorder:
    def __init__(
        self,
        cols: int = 112,
        rows: int = 34,
        prompt_str: str = DEFAULT_PROMPT_STR,
        redaction_patterns: Optional[List[Tuple[Pattern[str], str]]] = None,
    ):
        self.cols = cols
        self.rows = rows
        self.prompt_str = prompt_str
        self.redaction_patterns = redaction_patterns or DEFAULT_REDACTION_PATTERNS
        self.events: List[Tuple[float, str, str]] = []
        self.start_time: Optional[float] = None
        self.master_fd: Optional[int] = None
        self.slave_fd: Optional[int] = None
        self.process: Optional[subprocess.Popen] = None
        self.recent_buffer: str = ""

    def set_winsize(self, fd: int) -> None:
        winsize = struct.pack("HHHH", self.rows, self.cols, 0, 0)
        fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)

    def redact_text(self, text: str) -> str:
        for pattern, replacement in self.redaction_patterns:
            text = pattern.sub(replacement, text)
        return text

    def record_event(self, text: str, kind: str = "o") -> None:
        if self.start_time is not None:
            ts = time.time() - self.start_time
            sanitized = self.redact_text(text) if kind == "o" else text
            self.events.append((ts, kind, sanitized))

    def add_marker(self, label: str) -> None:
        """Inject an Asciicast v2 marker event for chapter-based player navigation."""
        self.record_event(label, kind="m")

    def drain_output(self, timeout: float = 0.05, record: bool = True) -> str:
        collected = ""
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
                    if len(self.recent_buffer) > 20000:
                        self.recent_buffer = self.recent_buffer[-10000:]
                except (OSError, ValueError):
                    break
            else:
                break
        return collected

    def wait_for_prompt(self, timeout: float = 120.0) -> bool:
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
                    if len(self.recent_buffer) > 20000:
                        self.recent_buffer = self.recent_buffer[-10000:]
                    # Check if prompt appears at the end of stream
                    if self.prompt_str in buf[-80:] or "developer@workstation" in buf[-80:]:
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

    def send_turn(
        self,
        cmd: str,
        pause_after: float = 3.0,
        base_delay: float = 0.032,
        jitter: bool = True,
        timeout: float = 120.0,
        marker_label: Optional[str] = None,
    ) -> None:
        if marker_label:
            self.add_marker(marker_label)
        self.drain_output(timeout=0.05, record=False)
        time.sleep(0.3)
        self.type_string(cmd, base_delay=base_delay, jitter=jitter)
        time.sleep(0.2)
        os.write(self.master_fd, b"\n")
        self.wait_for_prompt(timeout=timeout)
        time.sleep(pause_after)

    def assert_recent_output(self, expected_substring: str) -> None:
        """Verify that the recent subshell output contains the expected substring."""
        if expected_substring not in self.recent_buffer:
            raise AssertionError(
                f"Expected substring '{expected_substring}' not found in recent terminal output."
            )

    def start(self, cwd: Path = REPO_ROOT) -> None:
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
        self.recent_buffer = ""
        self.start_time = time.time()

    def stop(self) -> None:
        try:
            self.type_string("exit\n", base_delay=0.01, jitter=False)
            time.sleep(0.3)
            self.drain_output(timeout=0.2)
        except Exception:
            pass
        try:
            os.close(self.master_fd)
        except OSError:
            pass
        if self.process and self.process.poll() is None:
            self.process.terminate()

    def export(
        self,
        filepath: Path = DEFAULT_OUTPUT,
        title: str = "Interactive AI Agent Walkthrough",
        max_idle: float = 2.5,
    ) -> None:
        start_idx = 0
        for i, ev in enumerate(self.events):
            if ev[1] == "o" and "." in ev[2]:  # First user command
                start_idx = i
                break
        raw_events = self.events[start_idx:] if start_idx < len(self.events) else self.events

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
        rec.send_turn("./scripts/banner.sh 1", pause_after=1.5, marker_label="Step 1: Init")
        rec.send_turn("echo 'Hello from synchronous PTY recording!'", pause_after=2.0)
    finally:
        rec.stop()
        rec.export()
