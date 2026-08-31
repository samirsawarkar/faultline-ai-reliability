from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DAY30 = ROOT / "day30"
EVIDENCE = DAY30 / "evidence"
sys.path.insert(0, str(DAY30))

from faultline_launch.defense import render_spoken_script, render_transcript  # noqa: E402
from faultline_launch.evidence import load_json, sha256_file, write_json  # noqa: E402


def _duration(path: Path) -> float:
    completed = subprocess.run(
        ["afinfo", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    match = re.search(r"estimated duration:\s+([0-9.]+)\s+sec", completed.stdout)
    if not match:
        raise RuntimeError("afinfo did not report recording duration")
    return round(float(match.group(1)), 3)


def main() -> int:
    for command in ("say", "afconvert", "afinfo"):
        if shutil.which(command) is None:
            raise SystemExit(f"{command} is required to regenerate the recording")

    questions = load_json(DAY30 / "defense_questions.json")["questions"]
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    transcript_path = EVIDENCE / "mock-defense-transcript.md"
    transcript_path.write_text(render_transcript(questions), encoding="utf-8")
    spoken_script = render_spoken_script(questions)

    audio_path = EVIDENCE / "mock-defense.m4a"
    with tempfile.TemporaryDirectory(prefix="faultline-day30-") as temp_dir:
        temp = Path(temp_dir)
        speech_path = temp / "speech.txt"
        aiff_path = temp / "mock-defense.aiff"
        speech_path.write_text(spoken_script, encoding="utf-8")
        subprocess.run(
            ["say", "-r", "230", "-o", str(aiff_path), "-f", str(speech_path)],
            check=True,
        )
        subprocess.run(
            [
                "afconvert",
                str(aiff_path),
                "-o",
                str(audio_path),
                "-f",
                "m4af",
                "-d",
                "aac",
                "-b",
                "64000",
            ],
            check=True,
        )

    manifest = {
        "schema_version": "1.0.0",
        "format": "MPEG-4 audio / AAC mono",
        "voice": "macOS system default",
        "speech_rate_words_per_minute": 230,
        "duration_seconds": _duration(audio_path),
        "audio_bytes": audio_path.stat().st_size,
        "audio_sha256": sha256_file(audio_path),
        "transcript_sha256": sha256_file(transcript_path),
        "question_source_sha256": hashlib.sha256(
            (DAY30 / "defense_questions.json").read_bytes()
        ).hexdigest(),
        "synthetic_narration": True,
        "human_participant": False,
        "caveat": (
            "The recording proves the prepared answers can be delivered aloud; "
            "it does not prove the author's unaided oral proficiency."
        ),
    }
    write_json(EVIDENCE / "defense_recording.json", manifest)
    print(
        f"recorded {manifest['duration_seconds']:.1f}s "
        f"({manifest['audio_bytes']} bytes)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
