"""
Stable Diffusion control via the Forge / AUTOMATIC1111 WebUI API.

WHY THIS IS DIFFERENT FROM THE ORIGINAL SCAFFOLD
-------------------------------------------------
The original code told you to launch *Fooocus* but then called
`/sdapi/v1/img2img` with an `alwayson_scripts.controlnet` payload. That endpoint
and that payload shape belong to AUTOMATIC1111 / Forge with the sd-webui-controlnet
extension. Fooocus does not expose them, so every call would 404 / connection-fail.

This module targets **Forge** (recommended for 4 GB VRAM) or AUTOMATIC1111. It:
  * verifies the API is reachable with a clear error if not,
  * resolves ControlNet model names by prefix (the hash suffix differs per install),
  * defaults to OpenPose-only (depth is opt-in) to avoid OOM on 4 GB,
  * inpaints only the masked clothing region so face/background stay untouched,
  * raises informative exceptions instead of failing silently.
"""

import base64
from pathlib import Path
from typing import Dict, List, Optional

import requests

import config


# --------------------------------------------------------------------------- #
# Low-level helpers
# --------------------------------------------------------------------------- #
def _b64(path: str) -> str:
    """Read an image file and return base64-encoded bytes."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Image not found: {path}")
    with open(p, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _save_b64(b64_string: str, output_path: str) -> None:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "wb") as f:
        f.write(base64.b64decode(b64_string))


def check_sd_status() -> bool:
    """Return True if the Forge/A1111 API answers."""
    try:
        r = requests.get(f"{config.SD_API}/sdapi/v1/progress", timeout=5)
        return r.status_code == 200
    except requests.RequestException:
        return False


def _require_api() -> None:
    if not check_sd_status():
        raise ConnectionError(
            f"Stable Diffusion API not reachable at {config.SD_API}.\n"
            "Start Forge (or AUTOMATIC1111) with the --api flag. For the M1200:\n"
            "  ./webui.sh --api --lowvram --xformers --no-half-vae\n"
            "and confirm http://127.0.0.1:7860 loads in a browser first."
        )


# --------------------------------------------------------------------------- #
# ControlNet model-name resolution
# --------------------------------------------------------------------------- #
def _list_controlnet_models() -> List[str]:
    try:
        r = requests.get(f"{config.SD_API}/controlnet/model_list", timeout=10)
        if r.status_code == 200:
            return r.json().get("model_list", [])
    except requests.RequestException:
        pass
    return []


def _resolve_cn_model(prefix: str, available: List[str]) -> Optional[str]:
    """
    Match a configured model prefix (e.g. 'control_v11p_sd15_openpose') to the
    actual installed name (e.g. 'control_v11p_sd15_openpose [cab727d4]').
    """
    for name in available:
        if name.startswith(prefix) or prefix in name:
            return name
    return None


def _build_controlnet_args(photo_b64: str, available: List[str]) -> List[Dict]:
    """Construct the ControlNet unit list, honoring the depth opt-in flag."""
    units: List[Dict] = []

    op_model = _resolve_cn_model(config.CN_OPENPOSE_MODEL, available)
    if op_model:
        units.append(
            {
                "input_image": photo_b64,
                "module": "openpose_full",
                "model": op_model,
                "weight": 0.85,
                "guidance_start": 0.0,
                "guidance_end": 0.7,
                "control_mode": "Balanced",
                "pixel_perfect": True,
            }
        )

    if config.USE_DEPTH_CONTROLNET:
        depth_model = _resolve_cn_model(config.CN_DEPTH_MODEL, available)
        if depth_model:
            units.append(
                {
                    "input_image": photo_b64,
                    "module": "depth_midas",
                    "model": depth_model,
                    "weight": 0.6,
                    "guidance_start": 0.0,
                    "guidance_end": 0.6,
                    "control_mode": "Balanced",
                    "pixel_perfect": True,
                }
            )
    return units


# --------------------------------------------------------------------------- #
# Public: outfit generation via masked inpainting
# --------------------------------------------------------------------------- #
DEFAULT_NEGATIVE = (
    "deformed, distorted, disfigured, mutated, bad anatomy, wrong proportions, "
    "extra limbs, fused fingers, blurry, low quality, watermark, text, "
    "different face, changed face"
)


def generate_outfit(
    photo_path: str,
    mask_path: str,
    outfit_prompt: str,
    output_path: str,
    denoising_strength: Optional[float] = None,
    steps: Optional[int] = None,
) -> str:
    """
    Inpaint a new outfit into the masked clothing region of `photo_path`.

    The face, background, and everything outside the white mask area are kept
    because img2img inpainting only regenerates the masked pixels. ControlNet
    (OpenPose, optionally depth) locks the pose and body shape.

    Returns a human-readable status string.
    """
    _require_api()

    photo_b64 = _b64(photo_path)
    mask_b64 = _b64(mask_path)
    available = _list_controlnet_models()
    cn_args = _build_controlnet_args(photo_b64, available)

    if not cn_args:
        # Not fatal: inpainting still works without pose guidance, but warn loudly.
        cn_note = (
            " [WARNING: no ControlNet models found in Forge — pose may drift. "
            "Install control_v11p_sd15_openpose into models/ControlNet.]"
        )
    else:
        cn_note = f" [ControlNet units active: {len(cn_args)}]"

    payload: Dict = {
        "init_images": [photo_b64],
        "mask": mask_b64,
        "prompt": outfit_prompt,
        "negative_prompt": DEFAULT_NEGATIVE,
        # inpainting_fill: 1 = "original" (keep underlying content as the seed)
        "inpainting_fill": 1,
        "inpaint_full_res": True,
        "inpaint_full_res_padding": 32,
        # mask_blur smooths the seam between kept and regenerated regions.
        "mask_blur": 4,
        "resize_mode": 0,
        "denoising_strength": (
            denoising_strength
            if denoising_strength is not None
            else config.SD_DENOISING_STRENGTH
        ),
        "steps": steps if steps is not None else config.SD_STEPS,
        "cfg_scale": config.SD_CFG_SCALE,
        "width": config.SD_WIDTH,
        "height": config.SD_HEIGHT,
        "sampler_name": config.SD_SAMPLER,
    }

    if cn_args:
        payload["alwayson_scripts"] = {"controlnet": {"args": cn_args}}

    try:
        r = requests.post(
            f"{config.SD_API}/sdapi/v1/img2img",
            json=payload,
            timeout=600,  # CPU/lowvram inpainting can be slow
        )
    except requests.RequestException as e:
        raise ConnectionError(f"img2img request failed: {e}")

    if r.status_code != 200:
        raise RuntimeError(
            f"img2img returned HTTP {r.status_code}: {r.text[:300]}"
        )

    data = r.json()
    images = data.get("images")
    if not images:
        raise RuntimeError(f"img2img returned no images. Response: {str(data)[:300]}")

    _save_b64(images[0], output_path)
    return f"Outfit generated: {output_path}{cn_note}"
