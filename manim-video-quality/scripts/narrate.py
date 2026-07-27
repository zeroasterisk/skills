#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = ["google-cloud-texttospeech>=2.31.0"]
# ///
"""Generate narration audio and emit a timing manifest for the animation.

This is the first half of an audio-first pipeline. Beat duration must come
from the REAL audio, not a predicted words-per-minute, because observed TTS
rate varies between identical calls. So: synthesize each line, measure what
came back, and hand those measured durations to the scene.

    narrate.py  ->  beats/*.wav + narration.json + narration.wav
    scene reads narration.json and times each beat to its measured line
    ffmpeg muxes narration.wav onto the render

Input script JSON:

    {
      "voice": "Charon",
      "pace": "fast",
      "beats": [
        {"id": "start",  "line": "An agent process starts up..."},
        {"id": "issuer", "line": "The platform runs a workload CA..."}
      ]
    }

Pace note: measured against a reference corpus at ~205 wpm, gemini-3.1
lands on ~204 wpm with pace "fast", and ~159 wpm with "normal". The 2.5
models ignore (or invert) inline pace markup — prefer 3.1.

Usage:
    GOOGLE_CLOUD_PROJECT=... python3 narrate.py --script script.json --out ./narration
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
import wave
from pathlib import Path

MODEL = "gemini-3.1-flash-tts-preview"

# Verified rates on a 20-word line, voice Charon, via Cloud TTS API.
PACE_PROMPT = {
    "normal":  ("Say the following.", "", 159),
    "fast":    ("Say the following briskly and energetically, at a fast pace.",
                "", 204),
    "faster":  ("Say the following.", "[extremely fast] ", 233),
}

# ~10% of runtime is silence in the reference style; this is the inter-beat
# breath that produces roughly that.
BREATH_S = 0.35


def synth(client, tts, text: str, prompt: str, voice: str) -> bytes:
    r = client.synthesize_speech(
        input=tts.SynthesisInput(text=text, prompt=prompt),
        voice=tts.VoiceSelectionParams(
            language_code="en-US", name=voice, model_name=MODEL),
        audio_config=tts.AudioConfig(
            audio_encoding=tts.AudioEncoding.LINEAR16, sample_rate_hertz=24000),
    )
    return r.audio_content


def wav_duration(data: bytes) -> float:
    with contextlib.closing(wave.open(io.BytesIO(data))) as w:
        return w.getnframes() / float(w.getframerate())


def wav_frames(data: bytes) -> bytes:
    with contextlib.closing(wave.open(io.BytesIO(data))) as w:
        return w.readframes(w.getnframes())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--voice", default=None)
    ap.add_argument("--pace", default=None, choices=sorted(PACE_PROMPT))
    args = ap.parse_args()

    try:
        from google.cloud import texttospeech as tts
    except ImportError:
        sys.exit("pip install 'google-cloud-texttospeech>=2.31.0'")

    spec = json.loads(args.script.read_text())
    voice = args.voice or spec.get("voice", "Charon")
    pace = args.pace or spec.get("pace", "fast")
    prompt, markup, expected = PACE_PROMPT[pace]

    out = args.out
    beats_dir = out / "beats"
    beats_dir.mkdir(parents=True, exist_ok=True)

    client = tts.TextToSpeechClient()
    beats, pcm_all = [], b""
    cursor = 0.0

    print(f"model {MODEL} | voice {voice} | pace {pace} (~{expected} wpm)\n")
    for b in spec["beats"]:
        line = b["line"].strip()
        data = synth(client, tts, markup + line, prompt, voice)
        dur = wav_duration(data)
        words = len(line.split())
        (beats_dir / f"{b['id']}.wav").write_bytes(data)

        beats.append({
            "id": b["id"],
            "line": line,
            "words": words,
            "audio_s": round(dur, 3),
            "start_s": round(cursor, 3),
            "end_s": round(cursor + dur, 3),
            "wpm": round(words / dur * 60, 1),
            "file": f"beats/{b['id']}.wav",
        })
        print(f"  {b['id']:<12} {dur:5.2f}s  {words:>3}w  "
              f"{words/dur*60:5.0f} wpm")

        pcm_all += wav_frames(data)
        pcm_all += b"\x00\x00" * int(24000 * BREATH_S)   # breath
        cursor += dur + BREATH_S

    # single concatenated track, so muxing is one ffmpeg call
    track = out / "narration.wav"
    with wave.open(str(track), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(24000)
        w.writeframes(pcm_all)

    total_speech = sum(b["audio_s"] for b in beats)
    manifest = {
        "model": MODEL, "voice": voice, "pace": pace,
        "breath_s": BREATH_S,
        "total_s": round(cursor, 3),
        "speech_s": round(total_speech, 3),
        "speech_density": round(total_speech / cursor, 3) if cursor else 0,
        "wpm_overall": round(sum(b["words"] for b in beats) / total_speech * 60, 1),
        "track": "narration.wav",
        "beats": beats,
    }
    (out / "narration.json").write_text(json.dumps(manifest, indent=2))

    print(f"\n  total {manifest['total_s']}s | speech {manifest['speech_s']}s "
          f"({manifest['speech_density']:.0%}) | {manifest['wpm_overall']} wpm")
    print(f"  reference: ~205 wpm, ~90% density")
    print(f"\n  {out/'narration.json'}\n  {track}")
    print(f"\n  Next: time the scene from narration.json, render, then\n"
          f"    ffmpeg -i render.mp4 -i {track} -c:v copy -c:a aac -shortest out.mp4\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
