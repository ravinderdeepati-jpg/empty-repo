"""
Clothing-mask generation via human parsing (SegFormer).

WHY THIS IS DIFFERENT FROM THE ORIGINAL SCAFFOLD
-------------------------------------------------
The original prompted SAM with a SINGLE point at the image center and hoped it
would grab "the clothing". In practice that point lands on whatever is at the
middle of the frame — often the whole torso, the entire body, or background —
so the resulting mask is unreliable. A bad mask is catastrophic here: anything
included in the mask gets regenerated, so a sloppy mask repaints the FACE and
BACKGROUND, which is exactly what you asked to keep identical.

This script uses a *human-parsing* model, `mattmdjaga/segformer_b2_clothes`,
which semantically labels each pixel as face, hair, arm, upper-clothes, skirt,
dress, etc. We then build a mask from ONLY the garment classes. The face, hair,
skin, and background are excluded by construction, so inpainting leaves them
untouched.

It runs on CPU (slow but fine) so it does not compete with Stable Diffusion for
the M1200's 4 GB of VRAM.

SegFormer clothes label map (mattmdjaga/segformer_b2_clothes):
  0 Background        7 Dress           14 Left-arm
  1 Hat               8 Belt            15 Right-arm
  2 Hair              9 Left-shoe       16 Left-leg
  3 Sunglasses       10 Right-shoe      17 Right-leg
  4 Upper-clothes    11 Face           18 (scarf in some variants)
  5 Skirt            12 Left-leg(var)
  6 Pants            13 Right-leg(var)
"""

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

import config

# Garment classes we WANT to replace. Tune via --include.
# Defaults cover a full-outfit swap (saree/dress style): upper clothes, skirt,
# pants, dress, belt, and scarf. Face(11), hair(2), arms, legs, shoes, and
# background(0) are deliberately excluded so they are preserved.
DEFAULT_INCLUDE = [4, 5, 6, 7, 8]   # upper-clothes, skirt, pants, dress, belt

MODEL_ID = "mattmdjaga/segformer_b2_clothes"


def _lazy_imports():
    """Import torch/transformers only when actually generating a mask."""
    try:
        import torch
        from transformers import (
            AutoModelForSemanticSegmentation,
            SegformerImageProcessor,
        )
    except ImportError as e:
        raise SystemExit(
            "Missing ML deps. Install them (CPU build keeps the GPU free for SD):\n"
            "  pip install torch --index-url https://download.pytorch.org/whl/cpu\n"
            "  pip install transformers pillow numpy\n"
            f"Original import error: {e}"
        )
    return torch, AutoModelForSemanticSegmentation, SegformerImageProcessor


_processor = None
_model = None


def _load_model():
    global _processor, _model
    if _model is None:
        torch, AutoModelForSemanticSegmentation, SegformerImageProcessor = _lazy_imports()
        # Cache into the project's models/ dir so re-runs are offline-friendly.
        cache = str(config.MODELS_DIR)
        _processor = SegformerImageProcessor.from_pretrained(MODEL_ID, cache_dir=cache)
        _model = AutoModelForSemanticSegmentation.from_pretrained(
            MODEL_ID, cache_dir=cache
        )
        _model.eval()
    return _processor, _model


def generate_clothing_mask(
    image_path: str,
    output_mask_path: str,
    include_labels=None,
    dilate: int = 8,
    blur: int = 4,
) -> str:
    """
    Build a white-on-black mask covering only the garment regions of `image_path`.

    include_labels : list[int] of SegFormer classes to mask (defaults to clothes).
    dilate         : grow the mask outward (px) so garment edges are fully covered.
    blur           : feather the mask edge (px) for a smoother inpaint seam.
    """
    torch, _, _ = _lazy_imports()
    include = include_labels if include_labels else DEFAULT_INCLUDE

    src = Path(image_path)
    if not src.is_file():
        raise FileNotFoundError(f"Input image not found: {image_path}")

    image = Image.open(src).convert("RGB")
    processor, model = _load_model()

    inputs = processor(images=image, return_tensors="pt")
    with torch.no_grad():
        logits = model(**inputs).logits  # (1, num_labels, h/4, w/4)

    # Upsample logits to the original image size, then argmax to a label map.
    upsampled = torch.nn.functional.interpolate(
        logits,
        size=image.size[::-1],  # (height, width)
        mode="bilinear",
        align_corners=False,
    )
    seg = upsampled.argmax(dim=1)[0].cpu().numpy().astype(np.uint8)

    # Binary mask: 255 where the pixel belongs to a target garment class.
    mask = np.isin(seg, include).astype(np.uint8) * 255
    if mask.max() == 0:
        return (
            f"[WARNING] No garment pixels detected in {src.name}. "
            "The photo may be a close-up/headshot, or try a different --include set. "
            "No mask written."
        )

    mask_img = Image.fromarray(mask, mode="L")

    # Grow + feather: dilation via MaxFilter (odd kernel), then Gaussian blur.
    if dilate > 0:
        k = dilate * 2 + 1
        mask_img = mask_img.filter(ImageFilter.MaxFilter(size=min(k, 25)))
    if blur > 0:
        mask_img = mask_img.filter(ImageFilter.GaussianBlur(radius=blur))

    out = Path(output_mask_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    mask_img.save(out)

    coverage = float((mask > 0).mean()) * 100.0
    return f"Mask saved: {out} (garment coverage ~{coverage:.1f}% of frame)"


def _default_mask_path(image_path: str) -> str:
    name = Path(image_path).stem + "_mask.png"
    return str(config.MASKS_DIR / name)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate a clothing-only mask for outfit inpainting."
    )
    parser.add_argument("image", help="Path to the input photo.")
    parser.add_argument(
        "-o", "--output", default=None, help="Output mask path (PNG)."
    )
    parser.add_argument(
        "--include",
        default=None,
        help="Comma-separated SegFormer label ids to mask (default: 4,5,6,7,8).",
    )
    parser.add_argument("--dilate", type=int, default=8, help="Grow mask (px).")
    parser.add_argument("--blur", type=int, default=4, help="Feather mask edge (px).")
    args = parser.parse_args(argv)

    config.ensure_dirs()
    output = args.output or _default_mask_path(args.image)
    include = (
        [int(x) for x in args.include.split(",") if x.strip() != ""]
        if args.include
        else None
    )

    result = generate_clothing_mask(
        args.image, output, include_labels=include, dilate=args.dilate, blur=args.blur
    )
    print(result)


if __name__ == "__main__":
    main()
