"""
Local fashion AI agent — the orchestrator ("brain").

The agent reads your natural-language request, asks a local LLM (via Ollama) to
choose ONE tool and its arguments as JSON, validates that choice against the
real function signature, runs it, and reports back. Everything runs on your
machine; nothing is sent to a cloud LLM.

DESIGN NOTES / FIXES OVER THE ORIGINAL SCAFFOLD
-----------------------------------------------
* JSON parsing uses tools.llm_utils.extract_json, which survives <think> blocks,
  prose wrapping, and braces inside strings (the original silently fell back to
  raw text and ran no tool).
* Tool dispatch is SAFE: arguments coming from the LLM are filtered/validated
  against each function's signature, so a hallucinated or misspelled argument
  produces a clear message instead of a TypeError crash.
* The agent is OFFLINE-AWARE: it tells the model whether the internet is
  available so it won't promise web results it can't deliver, and search falls
  back to local documents automatically.
* A high-level `create_outfit` tool chains mask-generation + inpainting so a
  single request ("put a red saree on photo1.jpg") does the whole pipeline.
"""

import inspect
import sys
from typing import Any, Callable, Dict, Optional

import config
from tools import image_tools, memory_tools, search_tools, video_tools
from tools import llm_utils
from tools import sd_tools


# --------------------------------------------------------------------------- #
# High-level composite tool: full outfit pipeline
# --------------------------------------------------------------------------- #
def create_outfit(
    photo_path: str,
    outfit_prompt: str,
    output_path: Optional[str] = None,
    mask_path: Optional[str] = None,
) -> str:
    """
    End-to-end: generate a clothing mask (if not supplied) then inpaint the new
    outfit, preserving face / pose / background.

    photo_path    : input photo (e.g. input_photos/photo1.jpg)
    outfit_prompt : description of the desired garment
    output_path   : where to save the result (defaults to generated_outfits/)
    mask_path     : optional pre-made mask; auto-generated if omitted
    """
    from pathlib import Path

    src = Path(photo_path)
    if not src.is_file():
        return f"Input photo not found: {photo_path}"

    if output_path is None:
        output_path = str(config.GENERATED_OUTFITS_DIR / f"outfit_{src.stem}.png")

    # 1) mask
    if mask_path is None:
        mask_path = str(config.MASKS_DIR / f"{src.stem}_mask.png")
        if not Path(mask_path).is_file():
            try:
                import generate_mask

                msg = generate_mask.generate_clothing_mask(str(src), mask_path)
                if "No garment pixels" in msg:
                    return msg
            except SystemExit as e:
                return str(e)
            except Exception as e:  # pragma: no cover - surfaces model/load errors
                return f"Mask generation failed: {e}"

    # 2) inpaint
    return sd_tools.generate_outfit(str(src), mask_path, outfit_prompt, output_path)


# --------------------------------------------------------------------------- #
# Tool registry
# --------------------------------------------------------------------------- #
TOOLS: Dict[str, Callable[..., str]] = {
    # search / knowledge
    "search_web": search_tools.web_search,
    "search_local_docs": search_tools.offline_search,
    # memory
    "remember": memory_tools.save_memory,
    "recall": memory_tools.recall_memory,
    "list_memories": memory_tools.all_memories,
    # image generation
    "create_outfit": create_outfit,
    "generate_outfit": sd_tools.generate_outfit,
    # image post-processing
    "enhance_image": image_tools.enhance_image,
    "resize_image": image_tools.resize_image,
    "add_watermark": image_tools.add_watermark,
    "batch_process": image_tools.batch_process,
    # video
    "create_video": video_tools.images_to_video,
    "video_transitions": video_tools.add_crossfade_transitions,
    "add_audio": video_tools.add_audio_to_video,
    "trim_video": video_tools.trim_video,
}

# Compact, model-facing description of each tool and its parameters.
TOOL_DOCS = """\
- search_web(query, num_results=3): search the internet (needs connection); auto-falls back to local docs offline.
- search_local_docs(query, num_results=3): search ONLY your local offline_docs/ folder.
- remember(text): save a preference/fact to permanent local memory.
- recall(query, limit=5): retrieve relevant saved memories.
- list_memories(): list everything remembered.
- create_outfit(photo_path, outfit_prompt, output_path=None, mask_path=None): FULL pipeline — auto-mask the clothing then inpaint a new outfit, keeping face/pose/background. USE THIS for "put X outfit on this photo".
- generate_outfit(photo_path, mask_path, outfit_prompt, output_path): inpaint using an EXISTING mask.
- enhance_image(input_path, output_path): auto-enhance one image.
- resize_image(input_path, output_path, width, height): resize/crop one image.
- add_watermark(input_path, output_path, text='My Brand'): add a text watermark.
- batch_process(input_folder, output_folder): enhance every image in a folder.
- create_video(image_folder, output_path, fps=24, duration_per_image=3.0): slideshow video.
- video_transitions(image_folder, output_path, duration=3.0, fade=0.5): slideshow with crossfades.
- add_audio(video_path, audio_path, output_path): add music to a video.
- trim_video(input_path, output_path, start, end): cut a segment from a video.
"""

SYSTEM_PROMPT_TEMPLATE = """You are a local fashion AI agent running entirely on the user's laptop.
You control real tools by emitting JSON. Internet status right now: {net_status}.

Available tools:
{tool_docs}

When the user gives you a task, respond with ONLY a single JSON object, no prose:
{{
  "thought": "one short sentence about your plan",
  "tool": "<tool_name or null>",
  "args": {{ ... arguments matching the chosen tool ... }},
  "response": "what to tell the user"
}}

Rules:
- Choose exactly ONE tool, or null if the request is conversational.
- Use create_outfit for any "put/generate/try this outfit on this photo" request.
- Provide file paths exactly as the user gives them; do not invent files.
- If internet is offline and the user wants a web search, still call search_web (it will use local documents).
- Output JSON only. No markdown, no explanation outside the JSON.
"""


# --------------------------------------------------------------------------- #
# Safe dispatch
# --------------------------------------------------------------------------- #
def _coerce_args(func: Callable, args: Dict[str, Any]):
    """
    Keep only arguments that the target function actually accepts, and verify
    every required parameter is present. Returns (clean_args, error_or_None).
    """
    if not isinstance(args, dict):
        return {}, "Tool arguments were not a JSON object."

    sig = inspect.signature(func)
    params = sig.parameters
    accepts_kwargs = any(
        p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values()
    )

    clean = {}
    unknown = []
    for k, v in args.items():
        if k in params or accepts_kwargs:
            clean[k] = v
        else:
            unknown.append(k)

    missing = [
        name
        for name, p in params.items()
        if p.default is inspect.Parameter.empty
        and p.kind in (p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY)
        and name not in clean
    ]
    if missing:
        return clean, f"Missing required argument(s): {', '.join(missing)}"

    note = f" (ignored unknown arg(s): {', '.join(unknown)})" if unknown else ""
    return clean, None if not note else note  # note is informational, not fatal


def dispatch(tool_name: Optional[str], args: Dict[str, Any]) -> str:
    if not tool_name:
        return ""  # conversational; nothing to run
    func = TOOLS.get(tool_name)
    if func is None:
        return f"[Unknown tool '{tool_name}'. Available: {', '.join(sorted(TOOLS))}]"

    clean, problem = _coerce_args(func, args)
    # A genuinely missing required arg is fatal; an "ignored unknown" note is not.
    if problem and problem.startswith("Missing"):
        return f"[Cannot run {tool_name}: {problem}]"
    info = problem if (problem and problem.startswith(" ")) else ""

    try:
        result = func(**clean)
        return f"{result}{info}"
    except FileNotFoundError as e:
        return f"[{tool_name} error] {e}"
    except (ConnectionError, RuntimeError, EnvironmentError, ValueError) as e:
        return f"[{tool_name} error] {e}"
    except Exception as e:  # pragma: no cover - last-resort guard
        return f"[{tool_name} unexpected error] {type(e).__name__}: {e}"


# --------------------------------------------------------------------------- #
# Turn handling
# --------------------------------------------------------------------------- #
def run_agent(user_input: str) -> str:
    net_status = "ONLINE" if search_tools.is_online() else "OFFLINE"
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        net_status=net_status, tool_docs=TOOL_DOCS
    )

    # Give the model any relevant memories as lightweight context.
    memories = memory_tools.recall_memory(user_input, limit=3)
    user_prompt = f"Known preferences:\n{memories}\n\nUser request: {user_input}"

    try:
        parsed = llm_utils.chat_json(system_prompt, user_prompt)
    except RuntimeError as e:
        return f"[LLM error] {e}\nIs Ollama running?  ollama serve"
    except Exception as e:
        return f"[LLM error] {type(e).__name__}: {e}"

    if not parsed:
        return (
            "[The model did not return valid JSON. Try rephrasing, or use a more "
            "instruction-tuned model such as qwen2.5:3b-instruct.]"
        )

    tool_name = parsed.get("tool")
    args = parsed.get("args", {}) or {}
    agent_response = parsed.get("response", "")

    tool_result = dispatch(tool_name, args)

    # Persist a compact trail of what was done (cheap, no extra LLM call).
    if tool_name and tool_result and not tool_result.startswith("["):
        memory_tools.save_memory(f"Did: {user_input} -> {tool_name}")

    if tool_result:
        return f"{agent_response}\n\nResult: {tool_result}".strip()
    return agent_response or "(no action taken)"


BANNER = """\
Fashion AI Agent — fully local. Type 'quit' to exit, 'help' for examples.
Internet: {net}   |   LLM: {model}
"""

HELP = """\
Examples:
  put a red Banarasi saree with gold border on input_photos/photo1.jpg
  enhance all images in generated_outfits/ into processed_images/
  make a video with crossfades from processed_images/
  add final_videos/music.mp3 to final_videos/show.mp4
  remember that I prefer red and gold combinations
  search for trending saree colors in 2026
"""


def main():
    config.ensure_dirs()
    net = "ONLINE" if search_tools.is_online() else "OFFLINE"
    print(BANNER.format(net=net, model=config.LLM_MODEL))

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit"):
            break
        if user_input.lower() == "help":
            print(HELP)
            continue
        print()
        print(f"Agent: {run_agent(user_input)}\n")


if __name__ == "__main__":
    sys.exit(main())
