"""Real media ingestion helpers: download/decoding/transcription stay separate from channel adapters."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
from typing import Any


@dataclass
class MediaResult:
    status: str
    media_type: str
    transcript: str | None = None
    extracted_audio: str | None = None
    error_class: str | None = None
    evidence: dict[str, Any] | None = None


def extract_audio(video_path: str, output_path: str | None = None) -> MediaResult:
    source = Path(video_path)
    if not source.exists():
        return MediaResult("FAILED", "video", error_class="MEDIA_INACCESSIBLE", evidence={"path": video_path})
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return MediaResult("FAILED", "video", error_class="CAPABILITY_UNAVAILABLE", evidence={"capability": "ffmpeg"})
    target = Path(output_path) if output_path else source.with_suffix(".audio.wav")
    cmd = [ffmpeg, "-y", "-i", str(source), "-vn", "-ac", "1", "-ar", "16000", str(target)]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if proc.returncode != 0 or not target.exists():
        return MediaResult("FAILED", "video", error_class="MEDIA_INACCESSIBLE", evidence={"stderr": proc.stderr[-1000:]})
    return MediaResult("SUCCESS", "video", extracted_audio=str(target), evidence={"audio": str(target), "tool": "ffmpeg"})


def transcribe(audio_path: str, *, model: str = "base") -> MediaResult:
    source = Path(audio_path)
    if not source.exists():
        return MediaResult("FAILED", "audio", error_class="MEDIA_INACCESSIBLE", evidence={"path": audio_path})
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return MediaResult("FAILED", "audio", error_class="CAPABILITY_UNAVAILABLE", evidence={"capability": "faster_whisper"})
    try:
        wm = WhisperModel(model, device="auto", compute_type="int8")
        segments, info = wm.transcribe(str(source), vad_filter=True)
        text = " ".join(seg.text.strip() for seg in segments if seg.text.strip()).strip()
        if not text:
            return MediaResult("FAILED", "audio", error_class="MEDIA_INACCESSIBLE", evidence={"language": getattr(info, "language", None)})
        return MediaResult("SUCCESS", "audio", transcript=text, evidence={"language": getattr(info, "language", None), "model": model})
    except Exception as exc:  # backend errors are classified, not hidden
        return MediaResult("FAILED", "audio", error_class="MEDIA_INACCESSIBLE", evidence={"error": str(exc)})
