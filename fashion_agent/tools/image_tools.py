"""
Image post-processing via ImageMagick.

WHY THIS IS DIFFERENT FROM THE ORIGINAL SCAFFOLD
-------------------------------------------------
The original hard-coded the v6 `convert` binary. ImageMagick 7 (the default on
modern Windows/winget and recent Linux) renamed the entry point to `magick`, and
on many systems `convert` no longer exists. This module auto-detects which is
available and builds commands accordingly, so it runs on both v6 and v7.

It also runs commands as argument lists (never shell=True) so paths with spaces
are safe, and validates inputs up front with clear errors.
"""

import shutil
import subprocess
from pathlib import Path
from typing import List

import config

_IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


# --------------------------------------------------------------------------- #
# Binary detection (v7 `magick` vs v6 `convert`)
# --------------------------------------------------------------------------- #
def _magick_prefix() -> List[str]:
    """
    Return the command prefix for an ImageMagick 'convert'-style operation.

    v7: ["magick"]            -> `magick input ... output`
    v6: ["convert"]           -> `convert input ... output`
    """
    if config.IMAGEMAGICK_BIN:
        return [config.IMAGEMAGICK_BIN]
    if shutil.which("magick"):
        return ["magick"]
    if shutil.which("convert"):
        return ["convert"]
    raise EnvironmentError(
        "ImageMagick not found. Install it:\n"
        "  Linux:   sudo apt install imagemagick\n"
        "  Windows: winget install ImageMagick.ImageMagick\n"
        "Then re-run. (v7 provides 'magick'; v6 provides 'convert'.)"
    )


def _run(cmd: List[str]) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            "ImageMagick failed:\n" + (proc.stderr.strip() or proc.stdout.strip())
        )


def _require_input(path: str) -> Path:
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Image not found: {path}")
    return p


# --------------------------------------------------------------------------- #
# Operations
# --------------------------------------------------------------------------- #
def resize_image(input_path: str, output_path: str, width: int, height: int) -> str:
    """Resize+crop to exactly width x height, centered (fills the frame)."""
    _require_input(input_path)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    cmd = _magick_prefix() + [
        input_path,
        "-resize", f"{width}x{height}^",
        "-gravity", "center",
        "-extent", f"{width}x{height}",
        output_path,
    ]
    _run(cmd)
    return f"Resized -> {output_path} ({width}x{height})"


def enhance_image(input_path: str, output_path: str) -> str:
    """Auto-level, gentle sharpen, normalize colorspace."""
    _require_input(input_path)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    cmd = _magick_prefix() + [
        input_path,
        "-auto-level",
        "-modulate", "100,110,100",   # slightly richer saturation
        "-unsharp", "0x1.0",
        "-colorspace", "sRGB",
        output_path,
    ]
    _run(cmd)
    return f"Enhanced -> {output_path}"


def add_watermark(input_path: str, output_path: str, text: str = "My Brand") -> str:
    """Add a semi-transparent text watermark in the bottom-right corner."""
    _require_input(input_path)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    cmd = _magick_prefix() + [
        input_path,
        "-gravity", "SouthEast",
        "-fill", "rgba(255,255,255,0.5)",
        "-pointsize", "24",
        "-annotate", "+12+12", text,
        output_path,
    ]
    _run(cmd)
    return f"Watermarked -> {output_path}"


def batch_process(input_folder: str, output_folder: str) -> str:
    """Enhance every image in a folder, writing processed_<name> to the output."""
    in_dir = Path(input_folder)
    if not in_dir.is_dir():
        raise FileNotFoundError(f"Input folder not found: {input_folder}")
    out_dir = Path(output_folder)
    out_dir.mkdir(parents=True, exist_ok=True)

    images = sorted(p for p in in_dir.iterdir() if p.suffix.lower() in _IMG_EXTS)
    if not images:
        return f"No images found in {input_folder}"

    count = 0
    for img in images:
        out = out_dir / f"processed_{img.name}"
        enhance_image(str(img), str(out))
        count += 1
    return f"Batch processed {count} images -> {output_folder}"
