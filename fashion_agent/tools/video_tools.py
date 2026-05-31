"""
Video assembly with FFmpeg.

This is a *slideshow* builder, not a neural video generator. That distinction is
deliberate: true AI video generation (Wan, LTX, etc.) needs roughly 8 GB+ of
VRAM, which the Quadro M1200's 4 GB cannot provide. FFmpeg, by contrast, runs
entirely on the CPU and turns your generated outfit stills into a polished,
shareable clip with transitions and music.

WHY THIS IS DIFFERENT FROM THE ORIGINAL SCAFFOLD
-------------------------------------------------
The original `add_crossfade_transitions` built filter labels like [v0],[v1] and
then did `-map [vout]` — but [vout] was never created and no `xfade`/`acrossfade`
chain was ever assembled, so FFmpeg errored every run. It also computed an
unused `inputs` variable and used a fragile `shell=True` string.

Here we build a proper `xfade` chain with correct, cumulative time offsets and
run FFmpeg as an argument list (no shell, safe with spaces in paths).
"""

import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

import config

# Common still-image extensions, matched case-insensitively.
_IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _ffmpeg() -> str:
    exe = shutil.which(config.FFMPEG_BIN) or config.FFMPEG_BIN
    return exe


def _check_ffmpeg() -> None:
    if shutil.which(config.FFMPEG_BIN) is None:
        raise EnvironmentError(
            f"'{config.FFMPEG_BIN}' not found on PATH. Install FFmpeg:\n"
            "  Linux:   sudo apt install ffmpeg\n"
            "  Windows: winget install Gyan.FFmpeg"
        )


def _collect_images(folder: str) -> List[Path]:
    d = Path(folder)
    if not d.is_dir():
        raise FileNotFoundError(f"Image folder not found: {folder}")
    imgs = sorted(p for p in d.iterdir() if p.suffix.lower() in _IMG_EXTS)
    if not imgs:
        raise FileNotFoundError(f"No images found in {folder}")
    return imgs


def _run(cmd: List[str]) -> None:
    """Run an ffmpeg command, surfacing stderr on failure."""
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        tail = proc.stderr.strip().splitlines()[-15:]
        raise RuntimeError("FFmpeg failed:\n" + "\n".join(tail))


# Scale+pad each frame to a uniform canvas so xfade (which requires matching
# dimensions) works regardless of source aspect ratios.
def _scale_pad(label_in: str, label_out: str, w: int, h: int, fps: int) -> str:
    return (
        f"[{label_in}]scale={w}:{h}:force_original_aspect_ratio=decrease,"
        f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={fps},format=yuv420p"
        f"[{label_out}]"
    )


# --------------------------------------------------------------------------- #
# Simple slideshow (no transitions)
# --------------------------------------------------------------------------- #
def images_to_video(
    image_folder: str,
    output_path: str,
    fps: int = 24,
    duration_per_image: float = 3.0,
    width: int = 1080,
    height: int = 1920,
) -> str:
    """Concatenate images into a video, each shown for `duration_per_image` s."""
    _check_ffmpeg()
    images = _collect_images(image_folder)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    cmd: List[str] = [_ffmpeg(), "-y"]
    for img in images:
        cmd += ["-loop", "1", "-t", str(duration_per_image), "-i", str(img)]

    # Normalize every input, then concat.
    filters = []
    labels = []
    for i in range(len(images)):
        filters.append(_scale_pad(f"{i}:v", f"v{i}", width, height, fps))
        labels.append(f"[v{i}]")
    concat = f"{''.join(labels)}concat=n={len(images)}:v=1:a=0[vout]"
    filter_complex = ";".join(filters + [concat])

    cmd += [
        "-filter_complex",
        filter_complex,
        "-map",
        "[vout]",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-pix_fmt",
        "yuv420p",
        output_path,
    ]
    _run(cmd)
    return f"Video created: {output_path} ({len(images)} images)"


# --------------------------------------------------------------------------- #
# Slideshow WITH crossfade transitions  (the function that was broken before)
# --------------------------------------------------------------------------- #
def add_crossfade_transitions(
    image_folder: str,
    output_path: str,
    duration: float = 3.0,
    fade: float = 0.5,
    fps: int = 24,
    width: int = 1080,
    height: int = 1920,
) -> str:
    """
    Build a video where each image is shown for `duration` seconds and
    consecutive images crossfade over `fade` seconds.

    The `xfade` filter merges two streams; chaining it across N clips requires
    each transition's `offset` to be cumulative:

        offset_k = (k+1)*duration - (k+1)*fade

    i.e. start the next fade `fade` seconds before the current segment ends,
    accounting for the time already consumed by previous fades.
    """
    _check_ffmpeg()
    images = _collect_images(image_folder)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    n = len(images)
    if n == 1:
        # Nothing to crossfade; fall back to a single-image clip.
        return images_to_video(
            image_folder, output_path, fps=fps,
            duration_per_image=duration, width=width, height=height,
        )

    if fade >= duration:
        raise ValueError(
            f"fade ({fade}s) must be shorter than per-image duration ({duration}s)."
        )

    cmd: List[str] = [_ffmpeg(), "-y"]
    for img in images:
        cmd += ["-loop", "1", "-t", str(duration), "-i", str(img)]

    # 1) normalize every input to [v0]..[v{n-1}]
    parts = [_scale_pad(f"{i}:v", f"v{i}", width, height, fps) for i in range(n)]

    # 2) chain xfade. Each step consumes `fade` seconds of overlap, so the
    #    running timeline grows by (duration - fade) per added clip.
    prev = "v0"
    timeline = duration  # length of the chain produced so far
    for k in range(1, n):
        out = f"x{k}" if k < n - 1 else "vout"
        offset = timeline - fade
        parts.append(
            f"[{prev}][v{k}]xfade=transition=fade:duration={fade}:"
            f"offset={offset:.3f}[{out}]"
        )
        timeline = offset + fade + (duration - fade)  # = timeline + duration - fade
        prev = out

    filter_complex = ";".join(parts)
    cmd += [
        "-filter_complex",
        filter_complex,
        "-map",
        "[vout]",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-pix_fmt",
        "yuv420p",
        output_path,
    ]
    _run(cmd)
    return (
        f"Video with crossfades: {output_path} "
        f"({n} images, {fade}s fades, ~{timeline:.1f}s total)"
    )


# --------------------------------------------------------------------------- #
# Audio
# --------------------------------------------------------------------------- #
def add_audio_to_video(video_path: str, audio_path: str, output_path: str) -> str:
    """Mux an audio track onto a video, trimming to the shorter of the two."""
    _check_ffmpeg()
    if not Path(video_path).is_file():
        raise FileNotFoundError(f"Video not found: {video_path}")
    if not Path(audio_path).is_file():
        raise FileNotFoundError(f"Audio not found: {audio_path}")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        _ffmpeg(), "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        output_path,
    ]
    _run(cmd)
    return f"Audio added: {output_path}"


def trim_video(
    input_path: str, output_path: str, start: float, end: float
) -> str:
    """Cut a [start, end] second segment out of a video (re-encodes for accuracy)."""
    _check_ffmpeg()
    if not Path(input_path).is_file():
        raise FileNotFoundError(f"Video not found: {input_path}")
    if end <= start:
        raise ValueError("end must be greater than start")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        _ffmpeg(), "-y",
        "-i", input_path,
        "-ss", str(start),
        "-to", str(end),
        "-c:v", "libx264",
        "-preset", "medium",
        "-pix_fmt", "yuv420p",
        output_path,
    ]
    _run(cmd)
    return f"Trimmed: {output_path} ({start}s -> {end}s)"
