# =============================================================================
# EdGameClaw — AI Game-Based Learning Studio
# Created by Yuqi Hang (github.com/yh2072)
# https://github.com/yh2072/edgameclaw
# =============================================================================
"""Main orchestration pipeline for EdGameClaw game generation.

Game text language (titles, dialogue, minigame labels, etc.) is controlled by the
`locale` parameter. The studio sends the selected "Generation Language" as `locale`;
all prompts use it so that generated content is in that language consistently.
"""

import asyncio
import contextvars
import json
import os
import re
import sys
import time
from pathlib import Path

from functools import partial

from . import prompts
from .api import generate as _raw_generate
from .assembler import assemble, get_theme_css, get_audio_profile
from .sandbox import run_in_sandbox, build_repair_prompt
from .i18n import get_ui_strings, extract_locale_content, DEFAULT_LOCALE

generate = _raw_generate

# Per-task generate() so concurrent course generations don't overwrite each other's API config.
_current_generate_ctx: contextvars.ContextVar = contextvars.ContextVar("pipeline_generate", default=None)


def _get_generate():
    """Return the generate function for the current task, or module default."""
    return _current_generate_ctx.get() or generate


def _bind_api_config(api_key: str | None, base_url: str | None, model: str | None):
    """Return a generate() wrapper with API config baked in."""
    if not api_key and not model:
        return _raw_generate
    kwargs: dict = {}
    if api_key:
        kwargs["api_key"] = api_key
    if base_url:
        kwargs["base_url"] = base_url
    if model:
        kwargs["model"] = model
    return partial(_raw_generate, **kwargs)


def _extract_json(text: str) -> str:
    """Strip markdown fences and leading/trailing whitespace from LLM output.

    Handles both single and multiple fenced code blocks.
    """
    text = text.strip()
    if text.startswith("```"):
        # Extract all fenced blocks and concatenate their contents
        blocks = []
        for m in re.finditer(r'```(?:json|javascript|js)?\s*\n(.*?)```', text, re.DOTALL):
            blocks.append(m.group(1).strip())
        if blocks:
            return "\n".join(blocks)
        # Fallback: single fence without closing
        first_newline = text.index("\n")
        text = text[first_newline + 1:]
        if text.endswith("```"):
            text = text[:-3]
    return text.strip()


def _remove_trailing_commas_safe(text: str) -> str:
    """Remove trailing commas before ] or } only when outside of string values.
    LLMs often output valid JS but invalid JSON (e.g. , ] or , } )."""
    result = []
    i = 0
    in_string = False
    escape_next = False

    while i < len(text):
        ch = text[i]

        if escape_next:
            result.append(ch)
            escape_next = False
            i += 1
            continue

        if ch == '\\' and in_string:
            result.append(ch)
            escape_next = True
            i += 1
            continue

        if ch == '"':
            result.append(ch)
            in_string = not in_string
            i += 1
            continue

        if not in_string and ch == ',':
            # Look ahead: only whitespace until ] or }
            j = i + 1
            while j < len(text) and text[j] in ' \t\r\n':
                j += 1
            if j < len(text) and text[j] in '}]':
                # Trailing comma: skip the comma, keep the rest
                i += 1
                continue
        result.append(ch)
        i += 1

    return ''.join(result)


def _clean_json(text: str) -> str:
    """Fix common LLM JSON issues: trailing commas, comments, unescaped chars."""
    text = re.sub(r'//[^\n]*', '', text)
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    # Use safe trailing-comma removal (respects string boundaries)
    text = _remove_trailing_commas_safe(text)
    return text


def _fix_inner_quotes(text: str) -> str:
    """Fix unescaped double quotes inside JSON string values.

    LLMs often produce strings like: "description": "text with "inner quotes" here"
    This function walks the JSON character by character and escapes inner quotes.
    """
    result = []
    i = 0
    in_string = False
    string_start = -1

    while i < len(text):
        ch = text[i]

        if ch == '\\' and in_string:
            result.append(ch)
            i += 1
            if i < len(text):
                result.append(text[i])
            i += 1
            continue

        if ch == '"':
            if not in_string:
                in_string = True
                string_start = i
                result.append(ch)
            else:
                next_meaningful = _next_non_whitespace(text, i + 1)
                if next_meaningful in ('', ',', '}', ']', ':'):
                    in_string = False
                    result.append(ch)
                else:
                    result.append('\\"')
            i += 1
            continue

        if ch == '\n' and in_string:
            result.append('\\n')
            i += 1
            continue

        if ch == '\t' and in_string:
            result.append('\\t')
            i += 1
            continue

        result.append(ch)
        i += 1

    return ''.join(result)


def _next_non_whitespace(text: str, pos: int) -> str:
    """Return the next non-whitespace character at or after pos, or '' if end."""
    while pos < len(text):
        if text[pos] not in ' \t\r\n':
            return text[pos]
        pos += 1
    return ''


def _merge_json_fragments(text: str) -> any:
    """Handle LLM output containing multiple JSON values (arrays or objects) separated by whitespace.

    Common pattern: LLM outputs one JSON array per chapter instead of a single array.
    E.g.: [{...}]\n[{...}]\n[{...}] → merged into [{...},{...},{...}]
    Also handles: {...}\n{...} → takes just the first object.
    """
    decoder = json.JSONDecoder()
    text = text.strip()
    results = []
    pos = 0
    while pos < len(text):
        if text[pos] in ' \t\r\n':
            pos += 1
            continue
        try:
            obj, end_pos = decoder.raw_decode(text, pos)
            results.append(obj)
            pos = end_pos
        except json.JSONDecodeError:
            break

    if not results:
        raise json.JSONDecodeError("No JSON found", text, 0)

    if len(results) == 1:
        return results[0]

    if all(isinstance(r, list) for r in results):
        merged = []
        for r in results:
            merged.extend(r)
        print(f"  [PATCH] Merged {len(results)} JSON arrays into one ({len(merged)} items)", file=sys.stderr)
        return merged

    if all(isinstance(r, dict) for r in results):
        merged = {}
        for r in results:
            merged.update(r)
        print(f"  [PATCH] Merged {len(results)} JSON objects into one ({len(merged)} keys)", file=sys.stderr)
        return merged

    return results[0]


def _repair_truncated_json(text: str) -> any:
    """Attempt to repair truncated JSON by closing open braces/brackets.

    LLMs often hit max_tokens and produce truncated JSON like:
      {"a": {"b": [1, 2, 3], "c": "val
    This walks the string to find where it's valid and closes remaining brackets.
    """
    text = text.rstrip()
    # Remove trailing partial string values (unterminated strings)
    if text.count('"') % 2 != 0:
        last_quote = text.rfind('"')
        text = text[:last_quote + 1]

    # Remove trailing comma
    text = text.rstrip().rstrip(',')

    # Count unclosed braces/brackets
    stack = []
    in_str = False
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == '\\' and in_str:
            i += 2
            continue
        if ch == '"':
            in_str = not in_str
        elif not in_str:
            if ch in ('{', '['):
                stack.append('}' if ch == '{' else ']')
            elif ch in ('}', ']'):
                if stack:
                    stack.pop()
        i += 1

    if not stack:
        return json.loads(text)

    # Close remaining open structures
    closing = ''.join(reversed(stack))
    repaired = text + closing
    result = json.loads(repaired)
    print(f"  [PATCH] Repaired truncated JSON — added {len(stack)} closing bracket(s)", file=sys.stderr)
    return result


def _parse_json_robust(text: str, label: str = "output") -> any:
    """Parse JSON with automatic fixing of common LLM output issues."""
    cleaned = _extract_json(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    fixed = _clean_json(cleaned)
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass

    quote_fixed = _fix_inner_quotes(fixed)
    try:
        return json.loads(quote_fixed)
    except json.JSONDecodeError:
        pass

    # Replace Chinese-style quotes with brackets as last resort
    cn_fixed = quote_fixed.replace('\u201c', '\u300c').replace('\u201d', '\u300d')
    cn_fixed = cn_fixed.replace('\u2018', '\u300e').replace('\u2019', '\u300f')
    try:
        return json.loads(cn_fixed)
    except json.JSONDecodeError:
        pass

    # Handle "Extra data" — multiple JSON arrays/objects concatenated
    try:
        return _merge_json_fragments(cn_fixed)
    except (json.JSONDecodeError, Exception):
        pass

    # Try merging on the original cleaned text too
    try:
        return _merge_json_fragments(cleaned)
    except (json.JSONDecodeError, Exception):
        pass

    # Attempt to repair truncated JSON (LLM hit max_tokens mid-output)
    try:
        return _repair_truncated_json(cn_fixed)
    except (json.JSONDecodeError, Exception):
        pass

    try:
        return _repair_truncated_json(cleaned)
    except (json.JSONDecodeError, Exception) as e:
        pos = getattr(e, 'pos', 0) or 0
        start = max(0, pos - 80)
        end = min(len(cn_fixed), pos + 80)
        context = cn_fixed[start:end]
        print(f"  [ERROR] JSON parse failed for {label} near: ...{context}...", file=sys.stderr)
        raise


async def _step_with_retry(coro_fn, *args, retries: int = 2, label: str = "step"):
    """Retry an async step on failure."""
    for attempt in range(retries + 1):
        try:
            return await coro_fn(*args)
        except Exception as e:
            if attempt < retries:
                wait = 2 ** attempt
                print(f"  [RETRY] {label} failed (attempt {attempt+1}/{retries+1}): {e}", file=sys.stderr)
                print(f"  Waiting {wait}s before retry...", file=sys.stderr)
                await asyncio.sleep(wait)
            else:
                raise


def _validate_knowledge(data: any) -> dict:
    """Ensure the knowledge decomposition output is a well-formed dict.

    Handles the case where the LLM returns a list instead of a dict, or
    returns a dict with missing/malformed 'chunks' entries.
    """
    if isinstance(data, list):
        if len(data) == 1 and isinstance(data[0], dict):
            data = data[0]
        else:
            data = {"chunks": [c for c in data if isinstance(c, dict)]}
        print("  [PATCH] Knowledge was a list — wrapped into dict", file=sys.stderr)

    if not isinstance(data, dict):
        raise ValueError(f"Knowledge decomposition returned {type(data).__name__}, expected dict")

    chunks = data.get("chunks", [])
    if not isinstance(chunks, list):
        chunks = []
        data["chunks"] = chunks

    valid_chunks = []
    for i, c in enumerate(chunks):
        if isinstance(c, dict) and c.get("title"):
            c = dict(c)
            c["mechanic"] = "custom_simulation"
            if not c.get("simulationHint") and c.get("content"):
                c["simulationHint"] = (c.get("content", ""))[:300]
            valid_chunks.append(c)
        else:
            print(f"  [PATCH] Dropped malformed chunk at index {i}: {type(c).__name__}", file=sys.stderr)
    data["chunks"] = valid_chunks

    return data


async def _step_knowledge(
    topic: str,
    theme: str,
    exclude_mechanics: list[str] | None = None,
    game_index: int = 0,
    total_games: int = 1,
    locale: str = DEFAULT_LOCALE,
    personal_profile: dict | None = None,
) -> dict:
    """Step 1: Decompose the topic into knowledge chunks."""
    sys_p, usr_p = prompts.knowledge_decomposition_prompt(
        topic, theme=theme,
        exclude_mechanics=exclude_mechanics,
        game_index=game_index,
        total_games=total_games,
        locale=locale,
        personal_profile=personal_profile,
    )
    raw = await _get_generate()(usr_p, sys_p, max_tokens=16384, step="knowledge")
    data = _parse_json_robust(raw, "knowledge")
    data = _validate_knowledge(data)
    chunks = data.get("chunks", [])
    for i, c in enumerate(chunks):
        print(f"  [content] chunk_{i}: {c.get('title','')} | mechanic={c.get('mechanic','')} | {c.get('content','')[:80]}...", file=sys.stderr)
    return data


# -- Created by Yuqi Hang (github.com/yh2072) --
def _fix_script_sim_refs(script: list, chunks: list) -> list:
    """Correct sim_N references in the LLM-generated dialog script.

    The LLM sometimes uses wrong indices for sim_N names (e.g. 1-based
    instead of 0-based chunk indices).  This function builds the correct
    mapping from chunk data and patches any mismatched sim_N references
    so that the assembler can find the matching simulation code.
    """
    if not script or not chunks:
        return script

    correct_sim_names = [f"sim_{i}" for i in range(len(chunks))]
    if not correct_sim_names:
        return script

    script_sim_names = [
        cmd["game"]
        for cmd in script
        if isinstance(cmd, dict)
        and cmd.get("type") == "minigame"
        and isinstance(cmd.get("game", ""), str)
        and cmd["game"].startswith("sim_")
    ]

    if script_sim_names == correct_sim_names:
        return script

    if len(script_sim_names) != len(correct_sim_names):
        # Remap whichever names are wrong; leave extra/unknown references in place
        # (they will be recovered from checkpoint or fall back to generic template)
        wrong = [n for n in script_sim_names if n not in correct_sim_names]
        missing = [n for n in correct_sim_names if n not in script_sim_names]
        partial_remap = dict(zip(wrong, missing))
        if partial_remap:
            print(
                f"  [FIX] sim ref count mismatch (script={script_sim_names}, "
                f"expected={correct_sim_names}); partial remap: "
                + ", ".join(f"{k}→{v}" for k, v in partial_remap.items()),
                file=sys.stderr,
            )
            for cmd in script:
                if (
                    isinstance(cmd, dict)
                    and cmd.get("type") == "minigame"
                    and cmd.get("game") in partial_remap
                ):
                    cmd["game"] = partial_remap[cmd["game"]]
        else:
            print(
                f"  [WARN] sim ref count mismatch: script has {script_sim_names}, "
                f"expected {correct_sim_names} — no remap possible",
                file=sys.stderr,
            )
        return script

    remap = dict(zip(script_sim_names, correct_sim_names))
    if any(k != v for k, v in remap.items()):
        print(
            f"  [FIX] Correcting sim refs in dialog: "
            + ", ".join(f"{k}→{v}" for k, v in remap.items() if k != v),
            file=sys.stderr,
        )
        for cmd in script:
            if (
                isinstance(cmd, dict)
                and cmd.get("type") == "minigame"
                and cmd.get("game") in remap
            ):
                cmd["game"] = remap[cmd["game"]]

    return script


async def _step_dialog(topic: str, knowledge_json: str, theme: str, locale: str = DEFAULT_LOCALE) -> list:
    """Step 2: Generate the dialog script (with retry on parse failure)."""
    sys_p, usr_p = prompts.dialog_script_prompt(topic, knowledge_json, theme=theme, locale=locale)
    last_exc = None
    for attempt in range(3):
        try:
            raw = await _get_generate()(usr_p, sys_p, max_tokens=8192, step="dialog")
            data = _parse_json_robust(raw, "dialog")
            if isinstance(data, list):
                print(f"  [content] dialog: {len(data)} entries", file=sys.stderr)
                for entry in data[:3]:
                    if isinstance(entry, dict):
                        speaker = entry.get("speaker", "?")
                        text = entry.get("text", "")[:60]
                        print(f"    {speaker}: {text}...", file=sys.stderr)
                if len(data) > 3:
                    print(f"    ... and {len(data)-3} more lines", file=sys.stderr)
            return data
        except json.JSONDecodeError as e:
            last_exc = e
            print(f"  [RETRY] dialog parse failed (attempt {attempt+1}/3): {e}", file=sys.stderr)
            if attempt < 2:
                await asyncio.sleep(1)
    raise last_exc


async def _step_pixel_art(topic: str, knowledge_json: str, icon_names: list[str], theme: str, locale: str = DEFAULT_LOCALE) -> str:
    """Step 3 (legacy): Generate pixel art JavaScript code in one monolithic call."""
    sys_p, usr_p = prompts.pixel_art_prompt(topic, knowledge_json, icon_names, theme=theme, locale=locale)
    raw = await _get_generate()(usr_p, sys_p, max_tokens=12000, step="pixel_icons")
    text = raw.strip()
    if text.startswith("```"):
        first_newline = text.index("\n")
        text = text[first_newline + 1 :]
        if text.endswith("```"):
            text = text[: -3]
    return text.strip()


def _strip_js_fences(raw: str) -> str:
    """Strip markdown code fences from raw JS output."""
    text = raw.strip()
    if text.startswith("```"):
        first_newline = text.index("\n")
        text = text[first_newline + 1:]
        if text.endswith("```"):
            text = text[:-3]
    return text.strip()


async def _step_pixel_art_icons(
    topic: str, icon_names: list[str], theme: str, locale: str = DEFAULT_LOCALE
) -> str:
    """Focused step: generate only the ICONS object."""
    sys_p, usr_p = prompts.pixel_art_icons_prompt(topic, icon_names, theme=theme, locale=locale)
    raw = await _get_generate()(usr_p, sys_p, max_tokens=12000, step="pixel_icons")
    code = _strip_js_fences(raw)
    if _detect_truncation(code, "pixel_icons"):
        code = _repair_truncated_strings(code, "pixel_icons")
        code = _fix_unclosed_braces(code, "pixel_icons")
    return code


async def _step_minigame_icons(
    topic: str, minigame_data: dict, existing_icons: list[str],
    theme: str, locale: str = DEFAULT_LOCALE,
) -> str:
    """Generate additional pixel art icons referenced by minigame data but not yet in ICONS."""
    sys_p, usr_p = prompts.minigame_icons_prompt(
        topic, minigame_data, existing_icons, theme=theme, locale=locale
    )
    if not sys_p:
        return ""
    raw = await _get_generate()(usr_p, sys_p, max_tokens=12000, step="minigame_icons")
    code = _strip_js_fences(raw)
    if _detect_truncation(code, "minigame_icons"):
        code = _repair_truncated_strings(code, "minigame_icons")
        code = _fix_unclosed_braces(code, "minigame_icons")
    return code


async def _step_pixel_art_chars(
    topic: str, knowledge_json: str, theme: str, locale: str = DEFAULT_LOCALE
) -> str:
    """Focused step: generate only CHAR_DRAW_FNS and PORTRAITS."""
    sys_p, usr_p = prompts.pixel_art_chars_prompt(topic, knowledge_json, theme=theme, locale=locale)
    raw = await _get_generate()(usr_p, sys_p, max_tokens=12000, step="pixel_chars")
    code = _strip_js_fences(raw)
    if _detect_truncation(code, "pixel_chars"):
        code = _repair_truncated_strings(code, "pixel_chars")
        code = _fix_unclosed_braces(code, "pixel_chars")
    return code


async def _step_pixel_art_backgrounds(
    topic: str, knowledge_json: str, scene_descriptions: list[str], theme: str, locale: str = DEFAULT_LOCALE
) -> str:
    """Focused step: generate BACKGROUNDS + drawTitleLogo tied to narrative acts."""
    sys_p, usr_p = prompts.pixel_art_backgrounds_prompt(
        topic, knowledge_json, scene_descriptions, theme=theme, locale=locale
    )
    raw = await _get_generate()(usr_p, sys_p, max_tokens=12000, step="pixel_backgrounds")
    code = _strip_js_fences(raw)
    if _detect_truncation(code, "pixel_backgrounds"):
        code = _repair_truncated_strings(code, "pixel_backgrounds")
        code = _fix_unclosed_braces(code, "pixel_backgrounds")
    return code


async def _step_cover_art(
    topic: str, knowledge_json: str, theme: str, locale: str = DEFAULT_LOCALE,
    scene_descriptions: list | None = None,
) -> str:
    """Generate a stunning drawCover(g, w, h) function for the game's cover thumbnail."""
    sys_p, usr_p = prompts.cover_art_prompt(
        topic, knowledge_json, theme=theme, locale=locale, scene_descriptions=scene_descriptions
    )
    raw = await _get_generate()(usr_p, sys_p, max_tokens=12000, step="cover_art")
    code = _strip_js_fences(raw)
    if _detect_truncation(code, "cover_art"):
        code = _repair_truncated_strings(code, "cover_art")
        code = _fix_unclosed_braces(code, "cover_art")
    return code


# ---------------------------------------------------------------------------
# AI Post-processing / Quality Review steps
# ---------------------------------------------------------------------------

def _count_draw_commands(js: str) -> int:
    """Count pixel art draw calls (gpx/grect/px/rect) without double-counting.

    Matches the function names at word boundaries so 'grect(' is not also
    counted as 'rect(', and 'gpx(' is not also counted as 'px('.
    """
    return len(re.findall(r'\b(gpx|grect|px|rect)\s*\(', js))


def _needs_pixel_art_review(js: str, code_type: str) -> bool:
    """Heuristically decide if pixel art code is worth sending for AI review."""
    if not js or len(js) < 100:
        return True
    cmds = _count_draw_commands(js)
    thresholds = {"icons": 100, "chars": 80, "backgrounds": 110, "cover": 40}
    min_cmds = thresholds.get(code_type, 80)
    if cmds < min_cmds:
        return True
    # Check for stub functions (empty bodies)
    if "function(g, w, h) {}" in js or "function(g) {}" in js:
        return True
    return False



async def _step_review_pixel_art(
    js_code: str,
    code_type: str,
    requirements: str,
    theme: str,
) -> str:
    """AI review pass: check and improve pixel art JS for structure and detail.

    Only called when heuristics detect potential quality issues (too few draw
    commands, stub functions, missing globals). Skipped for already-good output
    to avoid unnecessary API calls.
    """
    if not _needs_pixel_art_review(js_code, code_type):
        print(
            f"  [REVIEW] pixel_art/{code_type}: {_count_draw_commands(js_code)} cmds — OK, skipping review",
            file=sys.stderr,
        )
        return js_code

    print(
        f"  [REVIEW] pixel_art/{code_type}: {_count_draw_commands(js_code)} cmds — sending for AI review",
        file=sys.stderr,
    )
    sys_p, usr_p = prompts.pixel_art_review_prompt(js_code, code_type, requirements, theme)
    try:
        raw = await _get_generate()(usr_p, sys_p, max_tokens=12000, step="review_batch")
        reviewed = _strip_js_fences(raw)
        if _detect_truncation(reviewed, f"review_{code_type}"):
            reviewed = _repair_truncated_strings(reviewed, f"review_{code_type}")
            reviewed = _fix_unclosed_braces(reviewed, f"review_{code_type}")
        if len(reviewed) >= len(js_code) * 0.6:
            after_cmds = _count_draw_commands(reviewed)
            print(
                f"  [REVIEW] pixel_art/{code_type}: {len(js_code)} → {len(reviewed)} chars, "
                f"{_count_draw_commands(js_code)} → {after_cmds} draw cmds",
                file=sys.stderr,
            )
            return reviewed
        print(
            f"  [REVIEW] pixel_art/{code_type}: reviewed too short, keeping original",
            file=sys.stderr,
        )
        return js_code
    except Exception as e:
        print(f"  [REVIEW WARN] pixel_art/{code_type} review failed: {e}", file=sys.stderr)
        return js_code


def _parse_pixel_art_batch(raw: str, originals: dict[str, tuple[str, str]]) -> dict[str, str]:
    """Parse batch pixel art review response into per-type JS strings."""
    results: dict[str, str] = {}
    for code_type, (orig_js, _) in originals.items():
        start_marker = f"// =={code_type.upper()}_START=="
        end_marker   = f"// =={code_type.upper()}_END=="
        s = raw.find(start_marker)
        e = raw.find(end_marker)
        if s != -1 and e != -1 and e > s:
            extracted = raw[s + len(start_marker):e].strip()
            if len(extracted) >= len(orig_js) * 0.55:
                after = _count_draw_commands(extracted)
                before = _count_draw_commands(orig_js)
                print(
                    f"  [REVIEW] pixel_art/{code_type}: {len(orig_js)} → {len(extracted)} chars, "
                    f"{before} → {after} draw cmds",
                    file=sys.stderr,
                )
                results[code_type] = extracted
                continue
        print(f"  [REVIEW] pixel_art/{code_type}: parse failed or too short, keeping original", file=sys.stderr)
        results[code_type] = orig_js
    return results


async def _step_review_pixel_art_batch(
    pieces: dict[str, tuple[str, str]],   # {code_type: (js_code, requirements)}
    theme: str,
) -> dict[str, str]:
    """Single LLM call to review all pixel art pieces that need improvement.

    Replaces 4 parallel _step_review_pixel_art calls with one batched call,
    sending only pieces that fail the quality heuristic.
    """
    to_review = {k: v for k, v in pieces.items() if _needs_pixel_art_review(v[0], k)}
    pass_through = {k: v[0] for k, v in pieces.items() if k not in to_review}

    if not to_review:
        print("  [REVIEW] all pixel art passed heuristics — skipping batch review", file=sys.stderr)
        return {k: v[0] for k, v in pieces.items()}

    print(f"  [REVIEW] batch reviewing: {list(to_review.keys())}", file=sys.stderr)
    sys_p, usr_p = prompts.pixel_art_review_batch_prompt(to_review, theme)
    try:
        raw = await _get_generate()(usr_p, sys_p, max_tokens=12000, step="review_batch")
        if _detect_truncation(raw, "review_batch"):
            raw = _repair_truncated_strings(raw, "review_batch")
            raw = _fix_unclosed_braces(raw, "review_batch")
        reviewed = _parse_pixel_art_batch(raw, to_review)
        return {**pass_through, **reviewed}
    except Exception as e:
        print(f"  [REVIEW WARN] batch review failed ({e}), keeping originals", file=sys.stderr)
        return {k: v[0] for k, v in pieces.items()}


# -- Created by Yuqi Hang (github.com/yh2072) --
def _derive_scene_descriptions(knowledge: dict) -> list[str]:
    """Derive 4 narrative-act scene descriptions from knowledge JSON.

    Maps the game's worldSetting and each chapter's narrativeHook to the
    Ki/Sho/Ten/Ketsu four-act structure, giving the background generator
    specific story context for each scene instead of generic guidance.
    """
    chunks = knowledge.get("chunks", [])
    world = knowledge.get("worldSetting", "")
    narrative = knowledge.get("narrativeTheme", "")
    n = len(chunks)

    if n == 0:
        base = f"世界：{world} | 叙事：{narrative}"
        return [base] * 4

    # Distribute chunks across 4 acts proportionally
    def _act_slice(act_idx: int) -> list[dict]:
        boundaries = [0, max(1, n // 4), max(2, n // 2), max(3, 3 * n // 4), n]
        start, end = boundaries[act_idx], boundaries[act_idx + 1]
        return chunks[start:end]

    act_labels = [
        "起（Ki）— 开场世界",
        "承（Sho）— 探索发现",
        "转（Ten）— 戏剧转折",
        "合（Ketsu）— 圆满结局",
    ]
    act_moods = [
        "氛围：温暖欢迎，充满好奇，探索的起点",
        "氛围：专注探索，充满发现，知识在积累",
        "氛围：惊奇转折，视角打开，认知突破时刻",
        "氛围：成就温暖，知识汇聚，圆满的告别",
    ]
    act_times = [
        "时段：清晨 — 天空淡蓝色带金色晨光，太阳刚升起，长影拖地",
        "时段：午间 — 明亮正午阳光，天空深蓝，色彩饱和鲜艳，阴影短",
        "时段：黄昏 — 橙红暮色，长影斜拉，天边橙紫渐变，温柔光晕",
        "时段：夜晚 — 深邃星空，月光银蓝，灯光点点，宁静而神秘",
    ]

    descs = []
    for i in range(4):
        act_chunks = _act_slice(i)
        hooks = " | ".join(
            f"{c.get('title', '')}: {c.get('narrativeHook', '')}"
            for c in act_chunks
            if c
        )
        desc = (
            f"{act_labels[i]}\n"
            f"{act_times[i]}\n"
            f"世界背景：{world}\n"
            f"章节内容：{hooks}\n"
            f"{act_moods[i]}"
        )
        descs.append(desc)

    return descs


# Template-based minigame data step disabled: custom_simulation only (no token for matching/sorting/etc).
# async def _step_minigame_data(topic: str, knowledge_json: str, icon_names: list[str], theme: str, locale: str = DEFAULT_LOCALE, used_mechanics: list[str] | None = None) -> dict:
#     """Step 4: Generate mini-game data (with retry on parse failure)."""
#     sys_p, usr_p = prompts.minigame_data_prompt(topic, knowledge_json, icon_names, theme=theme, locale=locale, used_mechanics=used_mechanics)
#     ...
#     return data


_MIN_SIM_CODE_LENGTH = 3000

def _postprocess_sim_code(text: str, chunk_index: int) -> str:
    """Clean and validate generated simulation code."""
    text = text.strip()
    if text.startswith("```"):
        first_newline = text.index("\n")
        text = text[first_newline + 1:]
        if text.endswith("```"):
            text = text[:-3]
    text = re.sub(r'^```(?:javascript|js)?\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^[^/\n]*知识点[：:].*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^[^/\n]*模拟概念[：:].*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^[^/\n]*注册名[：:].*$', '', text, flags=re.MULTILINE)
    text = text.strip()
    expected_name = f"sim_{chunk_index}"
    if "registerMinigame" not in text:
        raise ValueError(f"Generated code for {expected_name} missing registerMinigame call")
    if len(text) < _MIN_SIM_CODE_LENGTH:
        raise ValueError(
            f"Generated code for {expected_name} is too short ({len(text)} chars < {_MIN_SIM_CODE_LENGTH}). "
            "The AI likely produced a lazy/minimal simulation."
        )
    if expected_name not in text:
        text = text.replace("registerMinigame('simulation'", f"registerMinigame('{expected_name}'")
        text = text.replace('registerMinigame("simulation"', f"registerMinigame('{expected_name}'")
    text = re.sub(r'\$\{(\w+);\}', r'${\1}', text)
    text = re.sub(r'\$\{([\w.]+);"', r'${\1}"', text)
    text = re.sub(r"\$\{([\w.]+);'", r"${\1}'", text)
    text = re.sub(
        r'\$\{(makePortrait\([^)]*\))(?!\.outerHTML)\}',
        r'${\1.outerHTML}',
        text,
    )
    # Fix data.* access: for custom sims data is often {}, so data.title etc. are undefined.
    # Replace bare ${data.X} template expressions with ${data.X||''} to avoid "undefined" in UI.
    text = re.sub(r'\$\{data\.title\}', r"${data.title||''}", text)
    text = re.sub(r'\$\{data\.subtitle\}', r"${data.subtitle||''}", text)
    # data.portrait used as makePortrait arg — fall back to 'mentor'
    text = re.sub(r'makePortrait\(\s*data\.portrait\s*\)', "makePortrait(data.portrait||'mentor')", text)
    # data.title/subtitle used in JS assignments (e.g. el.textContent = data.title)
    text = re.sub(r'\bdata\.title\b(?!\s*\|)', "(data.title||'')", text)
    text = re.sub(r'\bdata\.subtitle\b(?!\s*\|)', "(data.subtitle||'')", text)
    _OUTER_PAGE_IDS = [
        'game-container', 'mini-game-overlay', 'dialog-box', 'dialog-text',
        'dialog-name', 'dialog-next', 'dialog-click-area', 'ui-overlay',
        'character-layer', 'title-screen', 'main', 'particles-canvas',
        'chapter-bar', 'audio-controls',
    ]
    for pid in _OUTER_PAGE_IDS:
        text = text.replace(
            f"document.getElementById('{pid}')", f"ct.querySelector('#{pid}')"
        )
        text = text.replace(
            f'document.getElementById("{pid}")', f"ct.querySelector('#{pid}')"
        )
        text = text.replace(f'id="{pid}"', f'id="sim-{pid}"')
        text = text.replace(f"id='{pid}'", f"id='sim-{pid}'")

    # Fix layout-breaking patterns: fullscreen sizing in a 768x576 container
    text = re.sub(r'width\s*:\s*100vw', 'width:100%', text)
    text = re.sub(r'height\s*:\s*100vh', 'height:100%', text)
    text = re.sub(r'max-width\s*:\s*960px', 'max-width:720px', text)
    text = re.sub(r'max-width\s*:\s*1200px', 'max-width:720px', text)
    # Replace window viewport sizing with container-relative sizing
    text = text.replace('window.innerWidth', 'ct.clientWidth')
    text = text.replace('window.innerHeight', 'ct.clientHeight')
    # Fix position:fixed used in tutorial overlays (should be absolute within ct)
    text = text.replace("position:fixed;inset:0", "position:absolute;inset:0")
    text = text.replace("position: fixed; inset: 0", "position:absolute;inset:0")
    text = text.replace("position:fixed;top:0;left:0;width:100%;height:100%",
                        "position:absolute;inset:0")
    text = re.sub(r"position\s*:\s*fixed", "position:absolute", text)
    # Fix document.body.appendChild for tutorial overlays
    text = text.replace("document.body.appendChild", "ct.appendChild")
    text = text.replace("document.body.removeChild", "ct.removeChild")

    # REJECT sims that read from data.X (will be undefined/empty at runtime)
    _BAD_DATA_REFS = ['data.scenarios', 'data.items', 'data.parameters', 'data.decisions',
                      'data.questions', 'data.options', 'data.categories', 'data.stimuli',
                      'data.pairs', 'data.steps', 'data.rounds', 'data.levels']
    bad_refs = [r for r in _BAD_DATA_REFS if r in text]
    if bad_refs:
        raise ValueError(
            f"sim_{chunk_index} reads {', '.join(bad_refs)} which will be undefined at runtime. "
            "Custom sims MUST hardcode all content — the `data` arg only has title/subtitle/portrait."
        )

    # REJECT quiz-like simulations: detect common quiz patterns
    _has_canvas = 'canvas' in text.lower() or 'getContext' in text
    _quiz_signals = 0
    if re.search(r"'correct'\s*:", text) and re.search(r"'incorrect'\s*:|'wrong'\s*:", text):
        _quiz_signals += 2
    if text.count("correct:true") + text.count("correct: true") + text.count("correct:false") + text.count("correct: false") > 3:
        _quiz_signals += 3
    if re.search(r'options\s*:\s*\[', text) and re.search(r'question\s*:', text):
        _quiz_signals += 2
    if text.count('.decision-card') > 2 or text.count('sim-option') > 2:
        _quiz_signals += 1
    if _quiz_signals >= 3 and not _has_canvas:
        raise ValueError(
            f"sim_{chunk_index} appears to be a QUIZ (detected {_quiz_signals} quiz signals, "
            "no canvas). Simulations MUST be canvas-based interactive experiments, not quizzes."
        )

    # Warn about emoji usage in canvas drawing code (fillText with emoji = non-professional)
    _EMOJI_PATTERN = re.compile(
        r'fillText\s*\(\s*[\'"`][^\'"` ]*'
        r'[\U0001F300-\U0001F9FF\U00002600-\U000027BF\U0001FA00-\U0001FFFF]'
        r'[^\'"` ]*[\'"`]',
        re.UNICODE,
    )
    if _EMOJI_PATTERN.search(text):
        print(
            f"  [WARN] sim_{chunk_index}: emoji detected in fillText() calls — "
            "prefer pixel art shapes (fillRect/arc)",
            file=sys.stderr,
        )

    # Fix low-contrast hardcoded dark text colors on dark backgrounds
    _DARK_TEXT_COLORS = ['color:#333', 'color:#444', 'color:#555', 'color:#666', 'color:#777', 'color:#888',
                         "color:'#333'", "color:'#444'", "color:'#555'", "color:'#666'", "color:'#777'", "color:'#888'",
                         'color: #333', 'color: #444', 'color: #555', 'color: #666', 'color: #777', 'color: #888']
    # Replace in inline styles within template literals — replace with theme.muted fallback usage
    # We don't blindly replace these since some may be used on light backgrounds,
    # but at least warn about them
    dark_count = sum(text.count(c) for c in _DARK_TEXT_COLORS)
    if dark_count > 0:
        print(
            f"  [WARN] sim_{chunk_index} contains {dark_count} potentially low-contrast dark text color(s). "
            "Consider using theme colors for better cross-theme contrast.",
            file=sys.stderr,
        )

    # Fix GAME.audio.X → Audio.X (GAME.audio is not the correct API; Audio.X is)
    if 'GAME.audio.' in text:
        n_audio = text.count('GAME.audio.')
        text = text.replace('GAME.audio.', 'Audio.')
        print(f"  [PATCH] Fixed {n_audio}× GAME.audio.X → Audio.X in sim_{chunk_index}", file=sys.stderr)

    text = _validate_js_syntax(text, f"sim_{chunk_index}")
    return text


_SIM_IMPLEMENT_MAX_TOKENS = 15000
_SIM_IMPLEMENT_CONTINUE_TOKENS = 15000
_SIM_IMPLEMENT_CONTINUE_ATTEMPTS = 2
_SIM_IMPLEMENT_REPAIR_TOKENS = 12000
_SIM_IMPLEMENT_REPAIR_ROUNDS = 3

_SIM_REFINE_MAX_TOKENS = 10000
_SIM_REFINE_CONTINUE_TOKENS = 10000
_SIM_REFINE_CONTINUE_ATTEMPTS = 1
_SIM_REFINE_REPAIR_TOKENS = 8000
_SIM_REFINE_REPAIR_ROUNDS = 2

_COVER_REPAIR_ROUNDS = 2
_COVER_REPAIR_TOKENS = 12000

_PIXEL_ART_REPAIR_ROUNDS = 3
_PIXEL_ART_REPAIR_TOKENS = 12000

_SANDBOX_REPAIR_ROUNDS = 3


def _get_sim_repair_profile(repair_mode: str) -> dict:
    repair_mode = (repair_mode or "implement").strip().lower()
    if repair_mode == "refine":
        return {
            "label": "refinement",
            "rounds": _SIM_REFINE_REPAIR_ROUNDS,
            "tokens": _SIM_REFINE_REPAIR_TOKENS,
            "step": "sim_refine",
        }
    if repair_mode == "cover":
        return {
            "label": "cover-art",
            "rounds": _SANDBOX_REPAIR_ROUNDS,
            "tokens": _SIM_IMPLEMENT_REPAIR_TOKENS,
            "step": "review_batch",
        }
    if repair_mode == "pixel_art":
        return {
            "label": "pixel-art",
            "rounds": _SANDBOX_REPAIR_ROUNDS,
            "tokens": _SIM_REFINE_REPAIR_TOKENS,
            "step": "review_batch",
        }
    return {
        "label": "implementation",
        "rounds": _SIM_IMPLEMENT_REPAIR_ROUNDS,
        "tokens": _SIM_IMPLEMENT_REPAIR_TOKENS,
        "step": "sim_implement",
    }


async def _sandbox_validate_and_repair(code: str, chunk_index: int, repair_mode: str = "implement") -> str:
    """Run code in sandbox; if it fails, ask LLM to fix and retry.

    Repair profiles are split by stage:
    - implement: allow a wider repair budget because the first draft is usually larger.
    - refine: keep the patch tighter and more conservative.
    """
    label = f"sim_{chunk_index}"
    profile = _get_sim_repair_profile(repair_mode)
    for round_idx in range(profile["rounds"]):
        result = run_in_sandbox(code, label=label)
        if result.ok:
            return code

        if result.phase in ("", "UNKNOWN") and not result.error_message:
            return code

        # Sandbox unavailable (node not found) — skip repair loop entirely,
        # there's no error info to fix and the LLM calls would be wasted.
        if result.phase == "SETUP":
            print(f"  [SANDBOX-SKIP] {label}: sandbox unavailable, skipping repair", file=sys.stderr)
            return code

        print(
            f"  [SANDBOX-FIX] {label} ({profile['label']}) round {round_idx + 1}/{profile['rounds']}: "
            f"{result.phase} — requesting LLM repair",
            file=sys.stderr,
        )

        repair_prompt = build_repair_prompt(code, result, repair_mode=repair_mode)
        system = (
            "You are a JavaScript bug-fixer. You receive code that failed in a "
            "sandbox test environment and the error message. Fix the EXACT error — "
            "do not rewrite the whole simulation. This is a "
            f"{profile['label']} repair pass. Keep the patch as small as possible. "
            "If the error is about a queried element, assign it to a variable and "
            "null-check it before addEventListener. Output ONLY the corrected "
            "complete JavaScript code. No markdown fences. No explanation."
        )
        try:
            fixed_raw = await _get_generate()(repair_prompt, system, max_tokens=profile["tokens"], step=profile["step"])
            fixed = _postprocess_sim_code(fixed_raw, chunk_index)
            code = fixed
        except Exception as e:
            print(
                f"  [SANDBOX-FIX] {label} repair attempt {round_idx + 1} failed: {e}",
                file=sys.stderr,
            )
            break

    # Final check after all repair rounds
    final = run_in_sandbox(code, label=label)
    if not final.ok:
        print(
            f"  [SANDBOX-WARN] {label} still has errors after {profile['rounds']} repairs: "
            f"{final.phase} — using best version anyway",
            file=sys.stderr,
        )
    return code


async def _sandbox_validate_cover(cover_js: str) -> str:
    """Sandbox-validate cover art (drawCover function) with LLM repair loop."""
    if not cover_js or "drawCover" not in cover_js:
        return cover_js

    for round_idx in range(_COVER_REPAIR_ROUNDS):
        sb = run_in_sandbox(cover_js, label="cover", mode="cover")
        if sb.ok:
            if round_idx > 0:
                print(f"  [SANDBOX] cover art — fixed on round {round_idx + 1} ✓", file=sys.stderr)
            return cover_js

        if sb.phase in ("", "UNKNOWN") and not sb.error_message:
            return cover_js

        if sb.phase == "SETUP":
            print(f"  [SANDBOX-SKIP] cover: sandbox unavailable, skipping repair", file=sys.stderr)
            return cover_js

        print(
            f"  [SANDBOX-FIX] cover round {round_idx + 1}/{_COVER_REPAIR_ROUNDS}: "
            f"{sb.phase} — {sb.error_message.split(chr(10))[0][:120]}",
            file=sys.stderr,
        )

        repair_prompt = build_repair_prompt(cover_js, sb, repair_mode="cover")
        system = (
            "You are a JavaScript bug-fixer specializing in pixel art cover functions. "
            "The code defines drawCover(g, w, h) using gpx() and grect() helpers. "
            "Fix the EXACT error — do not rewrite the whole function. "
            "Output ONLY the corrected complete JavaScript code. "
            "No markdown fences. No explanation."
        )
        try:
            fixed_raw = await _get_generate()(repair_prompt, system, max_tokens=_COVER_REPAIR_TOKENS, step="cover_repair")
            fixed = _strip_js_fences(fixed_raw)
            if len(fixed) >= len(cover_js) * 0.5:
                cover_js = fixed
                cover_js = _repair_truncated_strings(cover_js, "cover_repair")
                cover_js = _fix_unclosed_braces(cover_js, "cover_repair")
                cover_js = _validate_js_syntax(cover_js, "cover_repair")
            else:
                print(f"  [SANDBOX-FIX] cover repair too short, keeping current", file=sys.stderr)
                break
        except Exception as e:
            print(f"  [SANDBOX-FIX] cover repair attempt {round_idx + 1} failed: {e}", file=sys.stderr)
            break

    final = run_in_sandbox(cover_js, label="cover_final", mode="cover")
    if not final.ok:
        print(
            f"  [SANDBOX-WARN] cover art still has errors after {_COVER_REPAIR_ROUNDS} repairs: "
            f"{final.phase} — {final.error_message.split(chr(10))[0][:80]}",
            file=sys.stderr,
        )
    return cover_js


async def _step_sim_design(
    topic: str,
    chunk_info: dict,
    chunk_index: int,
    theme: str,
    locale: str = DEFAULT_LOCALE,
    all_chunks: list[dict] | None = None,
) -> str:
    """Phase 1 of simulation generation: design as plain text (no JSON).

    LLM describes mechanic, title, instruction, canvas, flow in prose.
    Implementation phase uses this text to generate code.
    """
    sys_p, usr_p = prompts.sim_design_prompt(
        topic, chunk_info, chunk_index=chunk_index, theme=theme, locale=locale,
        all_chunks=all_chunks,
    )
    raw = await _get_generate()(usr_p, sys_p, max_tokens=12000, step="sim_design")
    # Strip markdown code fences if present; return plain text
    text = re.sub(r"^```\w*\s*", "", raw.strip()).strip()
    text = re.sub(r"\s*```\s*$", "", text).strip()
    return text


async def _continue_truncated_code(partial_code: str, label: str, max_tokens: int = _SIM_IMPLEMENT_CONTINUE_TOKENS, attempts: int = 2) -> str:
    """Ask the LLM to continue a truncated JavaScript code block.

    Sends the last ~600 chars as context and asks the model to complete the code.
    Returns the fully assembled code (original + continuation).
    Retries up to 2 times if the continuation itself is also truncated.
    """
    context_tail = partial_code[-600:] if len(partial_code) > 600 else partial_code
    system = (
        "You are a JavaScript code completion assistant. "
        "You will receive the end of a truncated JavaScript code block and must continue it "
        "from EXACTLY where it was cut off. Output ONLY the continuation — no explanation, "
        "no markdown fences, no repetition of the provided code."
    )
    user = (
        f"The following JavaScript code was cut off mid-generation. "
        f"Continue it from exactly where it ends:\n\n"
        f"```\n...{context_tail}\n```\n\n"
        f"Output ONLY the continuation code. Do not repeat the code above."
    )
    for attempt in range(attempts):
        try:
            continuation = await _get_generate()(user, system, max_tokens=max_tokens, step="sim_implement")
            # Strip any accidental markdown fences
            continuation = re.sub(r'^```(?:javascript|js)?\s*', '', continuation, flags=re.MULTILINE)
            continuation = re.sub(r'\s*```\s*$', '', continuation, flags=re.MULTILINE).strip()
            # Remove overlap: if continuation starts with text already in partial_code, strip it
            overlap_check = context_tail[-100:]
            if overlap_check and continuation.startswith(overlap_check):
                continuation = continuation[len(overlap_check):]
            assembled = partial_code + "\n" + continuation
            if not _detect_truncation(assembled, f"{label}_cont{attempt+1}"):
                print(f"  [CONT] {label}: continuation successful ({len(continuation):,}ch added)", file=sys.stderr)
                return assembled
            print(f"  [CONT] {label}: continuation still truncated (attempt {attempt+1}), retrying...", file=sys.stderr)
            partial_code = assembled  # use assembled as new base for next attempt
        except Exception as e:
            print(f"  [CONT] {label}: continuation failed ({e})", file=sys.stderr)
            break
    return partial_code  # return best effort


async def _step_sim_implement(
    design_text: str,
    chunk_info: dict,
    chunk_index: int,
    theme: str,
    locale: str = DEFAULT_LOCALE,
    visual_helpers: str = "",
) -> str:
    """Phase 2: implement code from plain-text design description. Injects visual helper functions if available."""
    sys_p, usr_p = prompts.sim_implement_prompt(
        design_text, chunk_info, chunk_index=chunk_index, theme=theme, locale=locale,
    )
    if visual_helpers:
        usr_p += f"\n\n## Pre-generated Visual Helper Functions (use these in your drawCanvas)\n```javascript\n{visual_helpers}\n```"
    raw = await _get_generate()(usr_p, sys_p, max_tokens=_SIM_IMPLEMENT_MAX_TOKENS, step="sim_implement")
    if _detect_truncation(raw, f"sim_{chunk_index}_impl"):
        raw = await _continue_truncated_code(
            raw, f"sim_{chunk_index}_impl",
            max_tokens=_SIM_IMPLEMENT_CONTINUE_TOKENS,
            attempts=_SIM_IMPLEMENT_CONTINUE_ATTEMPTS,
        )
        # Final safety: patch any remaining string/brace issues after continuation
        raw = _repair_truncated_strings(raw, f"sim_{chunk_index}_impl_post")
        raw = _fix_unclosed_braces(raw, f"sim_{chunk_index}_impl_post")
    code = _postprocess_sim_code(raw, chunk_index)
    return code


_SIM_JUDGE_PASS_SCORE = 82  # minimum score to skip refine


async def _step_sim_judge(code: str, chunk_info: dict, chunk_index: int) -> dict:
    """Phase 3: LLM judge evaluates educational quality. Returns score dict."""
    sys_p, usr_p = prompts.sim_judge_prompt(code, chunk_info, chunk_index)
    try:
        raw = await _get_generate()(usr_p, sys_p, max_tokens=8192, step="sim_judge")
        result = _parse_json_robust(raw, f"sim_{chunk_index}_judge")
        total = result.get("total", 0)
        # Recompute total from sub-scores if not present
        if not total and "scores" in result:
            total = sum(result["scores"].values())
            result["total"] = total
        result.setdefault("approved", total >= _SIM_JUDGE_PASS_SCORE)
        return result
    except Exception as e:
        print(f"  [JUDGE] sim_{chunk_index}: judge failed ({e}), skipping refine", file=sys.stderr)
        return {"total": 100, "approved": True, "critical_issues": [], "visual_improvements": [], "interaction_improvements": []}


async def _step_sim_refine(
    code: str,
    judge_feedback: dict,
    chunk_info: dict,
    chunk_index: int,
    theme: str,
    locale: str = DEFAULT_LOCALE,
) -> str:
    """Phase 4: Rewrite simulation based on judge feedback with higher token budget."""
    sys_p, usr_p = prompts.sim_refine_prompt(
        code, judge_feedback, chunk_info, chunk_index, theme=theme, locale=locale,
    )
    raw = await _get_generate()(usr_p, sys_p, max_tokens=_SIM_REFINE_MAX_TOKENS, step="sim_refine")
    if _detect_truncation(raw, f"sim_{chunk_index}_refine"):
        raw = await _continue_truncated_code(
            raw, f"sim_{chunk_index}_refine",
            max_tokens=_SIM_REFINE_CONTINUE_TOKENS,
            attempts=_SIM_REFINE_CONTINUE_ATTEMPTS,
        )
        raw = _repair_truncated_strings(raw, f"sim_{chunk_index}_refine_post")
        raw = _fix_unclosed_braces(raw, f"sim_{chunk_index}_refine_post")
    return _postprocess_sim_code(raw, chunk_index)


async def _step_sim_visual_objects(chunk_info: dict, theme: str) -> str:
    """Phase 0 (optional): Generate canvas drawing helpers for key concept objects."""
    sys_p, usr_p = prompts.sim_visual_objects_prompt(chunk_info, theme=theme)
    try:
        raw = await _get_generate()(usr_p, sys_p, max_tokens=12000, step="sim_visual_objects")
        # Strip any markdown fences
        raw = re.sub(r'```(?:javascript|js)?\n?', '', raw).strip().rstrip('`').strip()
        return raw
    except Exception as e:
        print(f"  [VISUAL-OBJ] failed ({e}), skipping", file=sys.stderr)
        return ""


# -- Created by Yuqi Hang (github.com/yh2072) --
async def _step_simulation_code(topic: str, chunk_info: dict, chunk_index: int, theme: str, locale: str = DEFAULT_LOCALE, all_chunks: list[dict] | None = None) -> str:
    """Generate custom simulation JavaScript code for a specific chunk.

    Pipeline:
      Phase 0 (visual objects): Pre-generate draw helpers for key concept objects
      Phase 1 (design):         Plan mechanic, layout, data model
      Phase 2 (implement):      Write full code from blueprint (implementation budget)
      Phase 3 (judge):          LLM evaluates educational quality (score 0-100)
      Phase 4 (refine):         If score < 82, rewrite with judge feedback (refinement budget)
      Sandbox:                  Validate + auto-repair
    """
    label = f"sim_{chunk_index}"

    # ── Phase 0: Visual helper functions ──
    visual_helpers = await _step_sim_visual_objects(chunk_info, theme)
    if visual_helpers:
        print(f"  [VISUAL-OBJ] {label}: {len(visual_helpers):,}ch helpers generated", file=sys.stderr)

    repair_mode = "implement"
    for attempt in range(3):
        try:
            # ── Phase 1: Design (plain text, no JSON) ──
            design_text = await _step_sim_design(
                topic, chunk_info, chunk_index, theme, locale, all_chunks,
            )
            preview = (design_text[:80] + "…") if len(design_text) > 80 else design_text
            print(f"  [DESIGN] {label}: {len(design_text)}ch — {preview}", file=sys.stderr)

            # ── Phase 2: Implement (code from design text) ──
            code = await _step_sim_implement(
                design_text, chunk_info, chunk_index, theme, locale,
                visual_helpers=visual_helpers,
            )
            print(
                f"  [content] {label}: {len(code):,}ch, "
                f"registerMinigame={'✓' if 'registerMinigame' in code else '✗'}",
                file=sys.stderr,
            )

            # ── Phase 3: Judge ──
            judge = await _step_sim_judge(code, chunk_info, chunk_index)
            score = judge.get("total", 100)
            approved = judge.get("approved", True)
            issues = judge.get("critical_issues", [])
            print(
                f"  [JUDGE] {label}: {score}/100 {'✓ approved' if approved else '✗ needs refine'}"
                + (f" — {issues[0][:80]}" if issues else ""),
                file=sys.stderr,
            )

            # ── Phase 4: Refine if needed ──
            if not approved:
                repair_mode = "refine"
                print(f"  [REFINE] {label}: regenerating with judge feedback...", file=sys.stderr)
                try:
                    refined = await _step_sim_refine(
                        code, judge, chunk_info, chunk_index, theme, locale,
                    )
                    # Quick sandbox check before committing
                    sb = run_in_sandbox(refined, label=f"{label}_refined")
                    if sb.ok or len(refined) > len(code):
                        code = refined
                        print(f"  [REFINE] {label}: refined to {len(code):,}ch ✓", file=sys.stderr)
                    else:
                        print(f"  [REFINE] {label}: refined version worse, keeping original", file=sys.stderr)
                except Exception as re_err:
                    print(f"  [REFINE] {label}: refine failed ({re_err}), keeping original", file=sys.stderr)

            # ── Sandbox validation + repair ──
            code = await _sandbox_validate_and_repair(code, chunk_index, repair_mode=repair_mode)
            return code

        except Exception as e:
            if attempt < 2:
                wait = 2 ** attempt
                print(f"  [SIM RETRY] {label} attempt {attempt+1} failed: {e}", file=sys.stderr)
                await asyncio.sleep(wait)
            else:
                print(f"  [SIM FALLBACK] {label}: two-phase failed, trying single-pass", file=sys.stderr)
                try:
                    return await _step_simulation_code_single_pass(
                        topic, chunk_info, chunk_index, theme, locale, all_chunks,
                    )
                except Exception as e2:
                    print(f"  [SIM FAIL] {label}: all attempts failed: {e2}", file=sys.stderr)
                    raise


async def _step_simulation_code_single_pass(
    topic: str, chunk_info: dict, chunk_index: int, theme: str,
    locale: str = DEFAULT_LOCALE, all_chunks: list[dict] | None = None,
) -> str:
    """Legacy single-pass simulation generation as final fallback."""
    sys_p, usr_p = prompts.simulation_code_prompt(
        topic, chunk_info, chunk_index=chunk_index, theme=theme, locale=locale,
        all_chunks=all_chunks,
    )
    raw = await _get_generate()(usr_p, sys_p, max_tokens=_SIM_IMPLEMENT_MAX_TOKENS, step="sim_implement")
    if _detect_truncation(raw, f"sim_{chunk_index}_single"):
        raw = await _continue_truncated_code(
            raw, f"sim_{chunk_index}_single",
            max_tokens=_SIM_IMPLEMENT_CONTINUE_TOKENS,
            attempts=_SIM_IMPLEMENT_CONTINUE_ATTEMPTS,
        )
        raw = _repair_truncated_strings(raw, f"sim_{chunk_index}_single_post")
        raw = _fix_unclosed_braces(raw, f"sim_{chunk_index}_single_post")
    code = _postprocess_sim_code(raw, chunk_index)
    code = await _sandbox_validate_and_repair(code, chunk_index, repair_mode="implement")
    return code


async def regenerate_single_simulation_code(
    topic: str,
    chunk_info: dict,
    chunk_index: int,
    theme: str,
    locale: str = DEFAULT_LOCALE,
    all_chunks: list[dict] | None = None,
    custom_prompt: str = "",
    existing_code: str | None = None,
) -> str:
    """Generate simulation code for one chunk (e.g. for studio regen-sim with user prompt).

    When existing_code is provided, links to the current simulation code so the model can
    revise in place (preserve structure, apply user instructions). Otherwise runs full
    design -> implement pipeline.
    """
    custom_prompt = (custom_prompt or "").strip()
    if existing_code and existing_code.strip():
        # Regen from existing: one-shot revise so user modifications are preserved
        sys_p, usr_p = prompts.sim_regen_from_existing_prompt(
            existing_code.strip(),
            chunk_info,
            chunk_index=chunk_index,
            theme=theme,
            locale=locale,
            custom_prompt=custom_prompt,
        )
        raw = await _get_generate()(usr_p, sys_p, max_tokens=_SIM_IMPLEMENT_MAX_TOKENS, step="sim_implement")
        if _detect_truncation(raw, f"sim_{chunk_index}_regen"):
            raw = await _continue_truncated_code(
                raw, f"sim_{chunk_index}_regen",
                max_tokens=_SIM_IMPLEMENT_CONTINUE_TOKENS,
                attempts=_SIM_IMPLEMENT_CONTINUE_ATTEMPTS,
            )
            raw = _repair_truncated_strings(raw, f"sim_{chunk_index}_regen_post")
            raw = _fix_unclosed_braces(raw, f"sim_{chunk_index}_regen_post")
        code = _postprocess_sim_code(raw, chunk_index)
        code = await _sandbox_validate_and_repair(code, chunk_index, repair_mode="implement")
        return code
    info = dict(chunk_info)
    if custom_prompt:
        info["customPrompt"] = custom_prompt
    return await _step_simulation_code(
        topic, info, chunk_index, theme, locale, all_chunks,
    )


def _build_fallback_sim(chunk_index: int, chunk_info: dict, theme: str) -> str:
    """Build a working fallback simulation when AI generation fails completely.

    Generates a slider-based exploration that lets the player interact with
    the concept through parameter adjustment and visual feedback, rather than
    just reading text.
    """
    title = chunk_info.get("title", f"Exploration {chunk_index}")
    content_raw = chunk_info.get("content", "")[:250]
    content = content_raw.replace("`", "'").replace("${", "").replace("}", "")
    hint = chunk_info.get("simulationHint", "")[:100]
    hint = hint.replace("`", "'").replace("${", "").replace("}", "")
    css = prompts.THEMES.get(theme, prompts.THEMES["pink-cute"])["css"]

    acc = css.get("accent", "#ff6a9a")
    hl = css.get("highlight", "#ffd0e8")
    suc = css.get("success", "#90e0a0")
    txt = css.get("text", "#f0e0f0")
    mut = css.get("muted", "#c0a0b8")
    bg = css.get("bg", "#1a0818")
    brd = css.get("border", "#5a2848")
    cbg = css.get("cardBg", "rgba(255,255,255,0.06)")

    return f"""registerMinigame('sim_{chunk_index}', function(ct, data) {{
  var explored = 0, totalZones = 5, sliderVal = 50, history = [];
  var zones = [
    {{min:0,max:20,visited:false}}, {{min:20,max:40,visited:false}},
    {{min:40,max:60,visited:false}}, {{min:60,max:80,visited:false}},
    {{min:80,max:100,visited:false}}
  ];
  var W = 300, H = 160;

  function render() {{
    var pct = Math.round((explored / totalZones) * 100);
    var h = '<div style="max-width:700px;margin:0 auto;padding:14px 16px;font-family:inherit;color:{txt}">';
    h += '<div class="mg-header">';
    if (data.portrait) h += '<div id="fb-port"></div>';
    h += '<div class="mg-header-text"><div class="mg-title">' + (data.title || '{title}') + '</div></div></div>';
    h += '<div class="mg-instruction" style="margin-bottom:8px">' + (data.subtitle || '{hint}') + '</div>';
    h += '<div style="display:flex;gap:12px;flex-wrap:wrap">';
    h += '<div style="flex:1;min-width:260px"><canvas id="fb-cv" width="' + (W*2) + '" height="' + (H*2) + '" style="width:100%;max-width:' + W + 'px;height:auto;border:1px solid {brd};border-radius:8px;background:{bg}"></canvas></div>';
    h += '<div style="flex:1;min-width:180px;display:flex;flex-direction:column;gap:8px">';
    h += '<div style="background:{cbg};border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:12px">';
    h += '<div style="font-size:11px;color:{mut};margin-bottom:6px;text-transform:uppercase;letter-spacing:1px">Parameter</div>';
    h += '<input type="range" id="fb-sl" min="0" max="100" value="' + sliderVal + '" style="pointer-events:auto;width:100%;accent-color:{acc}">';
    h += '<div id="fb-vl" style="text-align:center;color:{acc};font-size:18px;font-weight:700;margin-top:4px">' + sliderVal + '%</div></div>';
    h += '<div style="background:{cbg};border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:10px">';
    h += '<div style="height:6px;background:rgba(255,255,255,0.06);border-radius:3px;overflow:hidden;margin-bottom:6px">';
    h += '<div id="fb-bar" style="height:100%;width:' + pct + '%;background:linear-gradient(90deg,{acc},{suc});border-radius:3px;transition:width .4s"></div></div>';
    h += '<div id="fb-st" style="font-size:12px;color:{mut}">' + explored + '/' + totalZones + '</div></div>';
    h += '<div id="fb-log" style="background:{cbg};border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:8px;max-height:80px;overflow-y:auto;font-size:11px;color:{mut}"></div>';
    h += '</div></div>';
    if (explored >= totalZones) {{
      h += '<div style="text-align:center;margin-top:12px;padding:14px;background:rgba(144,224,160,0.06);border:1px solid {suc};border-radius:10px">';
      h += '<div style="color:{suc};font-size:15px;margin-bottom:8px">✓ Exploration Complete!</div>';
      h += '<button class="mg-btn" id="fb-done" style="pointer-events:auto;padding:10px 28px">Continue →</button></div>';
    }}
    h += '</div>';
    ct.innerHTML = h;

    if (data.portrait) {{ var pe = ct.querySelector('#fb-port'); if (pe) pe.appendChild(makePortrait(data.portrait)); }}

    var canvas = ct.querySelector('#fb-cv');
    if (canvas) {{
      var g = canvas.getContext('2d');
      g.setTransform(2, 0, 0, 2, 0, 0);
      g.clearRect(0, 0, W, H);
      g.fillStyle = '{bg}'; g.fillRect(0, 0, W, H);
      var bw = (W - 30) / 10;
      for (var i = 0; i < 10; i++) {{
        var x = 15 + i * bw;
        var ctr = sliderVal / 100;
        var d = Math.abs((i / 9) - ctr);
        var bh = Math.max(6, (1 - d * 1.8) * (H - 30));
        if (bh < 0) bh = 6;
        var ratio = bh / (H - 30);
        g.fillStyle = 'rgba(255,' + Math.round(106 * ratio) + ',' + Math.round(154 * ratio) + ',' + (0.3 + 0.7 * ratio) + ')';
        g.fillRect(x + 1, H - 15 - bh, bw - 2, bh);
      }}
      var cx = 15 + (sliderVal / 100) * (W - 30);
      g.strokeStyle = '{hl}'; g.lineWidth = 1.5; g.setLineDash([3, 3]);
      g.beginPath(); g.moveTo(cx, 8); g.lineTo(cx, H - 15); g.stroke(); g.setLineDash([]);
      g.fillStyle = '{mut}'; g.font = '10px monospace'; g.textAlign = 'center';
      g.fillText(sliderVal + '%', cx, H - 3);
      history.forEach(function(hv) {{
        var hx = 15 + (hv / 100) * (W - 30);
        g.fillStyle = 'rgba(255,255,255,0.12)';
        g.beginPath(); g.arc(hx, H - 18, 2, 0, Math.PI * 2); g.fill();
      }});
    }}

    var sl = ct.querySelector('#fb-sl');
    if (sl) sl.addEventListener('input', function() {{
      sliderVal = parseInt(sl.value);
      if (history.length === 0 || Math.abs(history[history.length - 1] - sliderVal) > 10) history.push(sliderVal);
      for (var z = 0; z < zones.length; z++) {{
        if (sliderVal >= zones[z].min && sliderVal < zones[z].max && !zones[z].visited) {{
          zones[z].visited = true; explored++;
          Audio.playSFX('click');
          spawnParticles(384, 250, 'sparkle', 6);
          if (explored >= totalZones) {{ Audio.playSFX('complete'); spawnParticles(384, 250, 'confetti', 30); }}
        }}
      }}
      render();
    }});

    var db = ct.querySelector('#fb-done');
    if (db) db.addEventListener('click', function() {{
      _mgScore = Math.round((explored / totalZones) * 100);
      closeMiniGame();
    }});
  }}
  render();
}});"""


_FALLBACK_PORTRAIT = """function(g, w, h) {
  grect(g, 8, 2, 16, 18, '#f0d0b0');
  grect(g, 6, 4, 20, 14, '#f0d0b0');
  grect(g, 8, 0, 16, 6, '#c080a0');
  grect(g, 10, 8, 4, 4, '#3a1030');
  grect(g, 18, 8, 4, 4, '#3a1030');
  grect(g, 13, 16, 6, 2, '#e0a090');
  grect(g, 6, 20, 20, 10, '#5a2848');
}"""

_FALLBACK_BACKGROUND = """function() {
  rect(0, 0, 128, 96, '#1a0818');
  rect(0, 0, 128, 50, '#2a1030');
  rect(0, 50, 128, 4, '#5a2848');
  rect(0, 54, 128, 42, '#10060e');
  rect(10, 60, 40, 28, '#2a1028');
  rect(60, 62, 50, 26, '#2a1028');
}"""

_FALLBACK_TITLE_LOGO = """function drawTitleLogo(g, w, h) {
  grect(g, 10, 10, 44, 44, '#2a1028');
  grect(g, 12, 12, 40, 40, '#1a0818');
  grect(g, 20, 20, 24, 24, '#5a2848');
  grect(g, 24, 24, 16, 16, '#ff6a9a');
  grect(g, 28, 28, 8, 8, '#ffc0d0');
}"""


# -- Created by Yuqi Hang (github.com/yh2072) --
def _validate_and_repair_minigame_data(minigame_data: dict, label: str = "") -> dict:
    """Validate and repair common issues in generated minigame data.

    - Sorting: ensures all item.category values match a defined category id.
    - Deduction: ensures all answer indices are within bounds.
    - Combination: ensures at least one isTarget=True item.
    """
    if not isinstance(minigame_data, dict):
        return minigame_data

    # Fix sorting: item.category must match a category.id
    if "sorting" in minigame_data:
        s = minigame_data["sorting"]
        categories = s.get("categories", [])
        cat_ids = {c["id"] for c in categories if isinstance(c, dict) and "id" in c}
        cat_names = {c.get("name", "") for c in categories if isinstance(c, dict)}
        items = s.get("items", [])
        fixed_count = 0
        fallback_id = next(iter(cat_ids)) if cat_ids else None
        for item in items:
            if not isinstance(item, dict):
                continue
            cat = item.get("category", "")
            if cat not in cat_ids:
                # Try matching by name
                matched = next((c["id"] for c in categories if isinstance(c, dict) and c.get("name") == cat), None)
                if matched:
                    item["category"] = matched
                    fixed_count += 1
                elif fallback_id:
                    print(
                        f"  [REPAIR] sorting item '{item.get('name', '?')}' "
                        f"has unknown category '{cat}' → assigning '{fallback_id}'",
                        file=sys.stderr,
                    )
                    item["category"] = fallback_id
                    fixed_count += 1
        if fixed_count:
            print(f"  [REPAIR] Fixed {fixed_count} sorting item(s) with invalid category ids {label}", file=sys.stderr)

    # Fix deduction: answer index must be within opts bounds
    if "deduction" in minigame_data:
        d = minigame_data["deduction"]
        questions = d.get("questions", [])
        for q in questions:
            if not isinstance(q, dict):
                continue
            opts = q.get("opts", [])
            answer = q.get("answer", 0)
            if opts and (not isinstance(answer, int) or answer < 0 or answer >= len(opts)):
                q["answer"] = 0
                print(f"  [REPAIR] deduction question has invalid answer index → reset to 0 {label}", file=sys.stderr)

    # Fix matching: normalize pair field names to {term, desc, icon, sIcon}
    if "matching" in minigame_data:
        m = minigame_data["matching"]
        pairs = m.get("pairs", [])
        fixed_count = 0
        for p in pairs:
            if not isinstance(p, dict):
                continue
            if "left" in p and "term" not in p:
                p["term"] = p.pop("left")
                fixed_count += 1
            if "right" in p and "desc" not in p:
                p["desc"] = p.pop("right")
            if "iconLeft" in p and "icon" not in p:
                p["icon"] = p.pop("iconLeft")
            if "iconRight" in p and "sIcon" not in p:
                p["sIcon"] = p.pop("iconRight")
            if "concept" in p and "term" not in p:
                p["term"] = p.pop("concept")
                fixed_count += 1
            if "definition" in p and "desc" not in p:
                p["desc"] = p.pop("definition")
        if fixed_count:
            print(f"  [REPAIR] Fixed {fixed_count} matching pair(s) with non-standard field names {label}", file=sys.stderr)

    # General: check all minigame types for excessive item counts
    for mg_key, mg_val in minigame_data.items():
        if not isinstance(mg_val, dict):
            continue
        for list_key in ("items", "waves", "threats", "defenses"):
            arr = mg_val.get(list_key)
            if isinstance(arr, list) and len(arr) > 30:
                print(
                    f"  [REPAIR] {mg_key}.{list_key} has {len(arr)} entries — capping at 15 {label}",
                    file=sys.stderr,
                )
                mg_val[list_key] = arr[:15]

    # Fix word_forge: deduplicate fragments, cap count, ensure variety
    if "word_forge" in minigame_data:
        wf = minigame_data["word_forge"]
        frags = wf.get("fragments", [])
        if frags:
            texts = [f.get("text", "") for f in frags if isinstance(f, dict)]
            unique_texts = list(dict.fromkeys(texts))
            most_common = max(set(texts), key=texts.count) if texts else ""
            repeat_ratio = texts.count(most_common) / len(texts) if texts else 0
            if repeat_ratio > 0.4 or len(frags) > 20:
                print(
                    f"  [REPAIR] word_forge has {len(frags)} fragments, "
                    f"'{most_common}' repeated {texts.count(most_common)}x "
                    f"({repeat_ratio:.0%}) — deduplicating {label}",
                    file=sys.stderr,
                )
                wf["fragments"] = [{"text": t} for t in unique_texts[:15]]

    # Fix combination: ensure at least one isTarget=True
    if "combination" in minigame_data:
        c = minigame_data["combination"]
        items = c.get("items", [])
        if items and not any(item.get("isTarget") for item in items if isinstance(item, dict)):
            items[-1]["isTarget"] = True
            print(f"  [REPAIR] combination has no target item → set last item as target {label}", file=sys.stderr)

    return minigame_data


def _validate_js_syntax(js: str, label: str = "", _depth: int = 0) -> str:
    """Validate JS syntax using node --check. If error found, try to auto-fix.

    Runs up to 3 rounds so cascading fixes (e.g. truncated string → unclosed
    brace) are caught without manual intervention.
    """
    import subprocess, tempfile, os

    MAX_ROUNDS = 3
    if _depth >= MAX_ROUNDS:
        print(f"  [SYNTAX] {label}: gave up after {MAX_ROUNDS} fix rounds", file=sys.stderr)
        return js

    try:
        from .sandbox import _NODE_BIN as _node_bin
        if not _node_bin:
            return js
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False, encoding='utf-8') as f:
            f.write(js)
            tmp = f.name
        result = subprocess.run(
            [_node_bin, '--check', tmp], capture_output=True, text=True, timeout=10
        )
        os.unlink(tmp)
        if result.returncode == 0:
            return js

        err = result.stderr.strip()
        line_match = re.search(r':(\d+)', err)
        err_line = int(line_match.group(1)) if line_match else 0
        lines = js.split('\n')

        print(f"  [SYNTAX] {label}: JS error at line {err_line} (round {_depth + 1})", file=sys.stderr)

        fixed = False
        if err_line > 0 and err_line <= len(lines):
            bad_line = lines[err_line - 1]

            # Fix 1: truncated function definition — remove the incomplete line
            if re.match(r'\s*\w+\s*:\s*function\s*\([^)]*$', bad_line):
                print(f"  [SYNTAX] Removing truncated function at line {err_line}: {bad_line.strip()[:60]}", file=sys.stderr)
                lines[err_line - 1] = ''
                fixed = True

            # Fix 2: truncated string literal — complete the string instead of removing
            if not fixed:
                trunc = re.search(r"(['\"])#[0-9a-fA-F]{0,5}\s*$", bad_line)
                if trunc:
                    quote = trunc.group(1)
                    # Complete the truncated color + close the function call
                    completed = bad_line.rstrip() + 'f0e0f0' + quote + ');'
                    print(f"  [SYNTAX] Completed truncated hex color at line {err_line}: ...{bad_line.strip()[-30:]}", file=sys.stderr)
                    lines[err_line - 1] = completed
                    fixed = True

            # Fix 3: any other unterminated string on the error line
            if not fixed and re.search(r"['\"][^'\"]*$", bad_line):
                # Remove the bad line entirely
                print(f"  [SYNTAX] Removing line with unterminated string at {err_line}: {bad_line.strip()[:60]}", file=sys.stderr)
                lines[err_line - 1] = ''
                fixed = True

        if fixed:
            js = '\n'.join(lines)
            js = _fix_unclosed_braces(js, f"{label}/post-syntax-fix-r{_depth + 1}")
            return _validate_js_syntax(js, label, _depth + 1)

        print(f"  [SYNTAX] Could not auto-fix: {err[:150]}", file=sys.stderr)
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass
    return js


def _fix_unclosed_braces(js: str, label: str = "") -> str:
    """Fix mismatched `{}`in JS code — adds missing or removes extra closing braces."""
    open_count = js.count("{") - js.count("}")
    if open_count > 0:
        # More `{` than `}` — append closing braces
        js += "\n" + ("}" * open_count) + ";\n"
        print(f"  [PATCH] Fixed {open_count} unclosed braces in {label}", file=sys.stderr)
    elif open_count < 0:
        # More `}` than `{` — remove extra trailing closing braces
        extra = -open_count
        # Strip extra `}` from the end of the string
        stripped = js.rstrip()
        removed = 0
        while extra > 0 and stripped.endswith("}"):
            stripped = stripped[:-1].rstrip()
            extra -= 1
            removed += 1
        if removed:
            js = stripped + "\n"
            print(f"  [PATCH] Removed {removed} extra closing braces in {label}", file=sys.stderr)
    return js


def _repair_incomplete_draw_calls(js: str, label: str = "") -> str:
    """Remove lines that are just 'gpx' or 'grect' without the call (truncated output)."""
    lines = js.split("\n")
    out = []
    removed = 0
    for line in lines:
        stripped = line.strip()
        if re.fullmatch(r"(gpx|grect)\s*$", stripped):
            removed += 1
            continue
        out.append(line)
    if removed:
        print(f"  [PATCH] Removed {removed} incomplete gpx/grect line(s) in {label}", file=sys.stderr)
    return "\n".join(out)


def _repair_truncated_icon_functions(js: str, label: str = "") -> str:
    """Fix truncated icon/char function definitions in pixel art JS.

    Detects patterns like:
      name: function(g        (missing closing paren and body)
      name: function(g, w, h  (missing closing paren and body)
    and either completes them with an empty body or removes them.
    """
    # Pattern: property function missing body — e.g. `name: function(args\n};`
    # This happens when LLM output gets truncated mid-function
    truncated_fn = re.compile(
        r'(\w+)\s*:\s*function\s*\([^)]*$',  # function( with no closing paren on same line
        re.MULTILINE,
    )
    fixes = 0
    for m in reversed(list(truncated_fn.finditer(js))):
        fn_name = m.group(1)
        after = js[m.end():m.end() + 40].strip()
        if after.startswith(')') and '{' in after[:10]:
            continue
        js = (
            js[:m.start()]
            + f"{fn_name}: function(g, w, h) {{\n"
            + "    grect(g, 4, 4, 8, 8, '#5a3050');\n"
            + "  }"
            + js[m.end():]
        )
        fixes += 1

    # Also catch: `name: function(g, w, h) {` with body ending abruptly before `};`
    # i.e. function body that is cut off mid-statement
    dangling_fn = re.compile(
        r'(\w+)\s*:\s*function\s*\([^)]*\)\s*\{[^}]{0,20}\n\s*\}',
        re.MULTILINE,
    )
    for m in reversed(list(dangling_fn.finditer(js))):
        fn_name = m.group(1)
        body_start = m.group(0).index('{')
        body = m.group(0)[body_start + 1:].strip().rstrip('}').strip()
        if not body or (not body.endswith(';') and not body.endswith('}')):
            replacement = (
                f"{fn_name}: function(g, w, h) {{\n"
                "    grect(g, 4, 4, 8, 8, '#5a3050');\n"
                "  }"
            )
            js = js[:m.start()] + replacement + js[m.end():]
            fixes += 1

    if fixes:
        print(f"  [PATCH] Repaired {fixes} truncated function(s) in {label}", file=sys.stderr)
    return js


def _detect_truncation(code: str, label: str = "") -> bool:
    """Heuristically detect whether generated code was truncated at the token limit.

    Checks three signals:
    1. Brace imbalance — open > close (accounting for string literals).
    2. Unterminated string / hex color at the very end.
    3. Code ends with a non-terminating character on a long output.

    Returns True if the code appears to be truncated.
    """
    if not code or len(code) < 50:
        return False

    # Signal 1: brace imbalance (skip braces inside string literals)
    in_str = False
    str_char = ""
    escaped = False
    open_b = close_b = 0
    i = 0
    while i < len(code):
        ch = code[i]
        if escaped:
            escaped = False
            i += 1
            continue
        if ch == "\\":
            escaped = True
            i += 1
            continue
        if not in_str:
            if ch in ('"', "'"):
                in_str = True
                str_char = ch
            elif ch == "`":
                # Skip entire template literal (simplified: find matching `)
                end = code.find("`", i + 1)
                i = end + 1 if end != -1 else len(code)
                continue
            elif ch == "{":
                open_b += 1
            elif ch == "}":
                close_b += 1
        else:
            if ch == str_char:
                in_str = False
        i += 1

    if open_b > close_b + 1:
        print(
            f"  [TRUNC] {label}: brace imbalance — open={open_b} close={close_b} "
            f"(diff={open_b - close_b})",
            file=sys.stderr,
        )
        return True

    # Signal 2: ends with an unterminated hex color string (most common pixel art truncation)
    tail = code[-80:] if len(code) > 80 else code
    # Pattern: a single/double quote followed by # and partial hex, at end of line/string
    if re.search(r"""['"]['"]#[0-9a-fA-F]{0,5}\s*$""", tail) or \
       re.search(r"""['"]['"]#[0-9a-fA-F]{0,5}[,);\s]*$""", tail):
        print(f"  [TRUNC] {label}: ends with truncated hex color string", file=sys.stderr)
        return True
    # General unterminated string at end of non-trivially-short output
    if len(code) > 200 and re.search(r"""(?<![\\])['"][^'"{\n]{0,60}$""", tail):
        print(f"  [TRUNC] {label}: ends in unterminated string", file=sys.stderr)
        return True

    # Signal 3: code ends mid-expression on long output
    stripped = code.rstrip()
    if stripped and len(stripped) > 500:
        last_char = stripped[-1]
        if last_char not in ("}", ";", ")", "]", '"', "'"):
            print(
                f"  [TRUNC] {label}: ends with {repr(last_char)} — "
                f"possible mid-expression cut",
                file=sys.stderr,
            )
            return True

    return False


def _repair_truncated_strings(js: str, label: str = "") -> str:
    """Fix truncated string literals in pixel art JS (e.g. gpx(g, 10, 13, '#).

    LLMs hitting max_tokens often truncate mid-string in pixel art code.
    This finds lines ending with an unterminated quoted hex color and
    completes them with a default color + closing paren + semicolon.
    """
    # Match lines ending with an incomplete hex color string like '#  or '#f0  or "#abc
    pattern = re.compile(r"^(.*?)(['\"])#([0-9a-fA-F]{0,5})\s*$", re.MULTILINE)
    fixes = 0
    def _complete(m):
        nonlocal fixes
        prefix, quote, partial_hex = m.group(1), m.group(2), m.group(3)
        # Pad to 6-char hex — fill remaining with 'f' as a safe neutral color
        full_hex = partial_hex + 'f' * (6 - len(partial_hex))
        fixed = f"{prefix}{quote}#{full_hex}{quote});"
        fixes += 1
        return fixed

    js = pattern.sub(_complete, js)
    if fixes:
        print(f"  [PATCH] Completed {fixes} truncated hex color(s) in {label}", file=sys.stderr)
    return js


def _sanitize_pixel_art_piece(js: str, expected_globals: set[str], label: str) -> str:
    """Sanitize a single pixel art JS piece before combining.

    1. Fix unclosed braces (prevents the most common syntax error).
    2. Strip any accidental duplicate `const X = ...` declarations that
       belong to a *different* piece (the AI sometimes echoes globals
       from the prompt example).
    """
    if not js.strip():
        return js

    # Strip top-level gpx/grect re-declarations — engine.js owns these globals.
    # If pixel art JS re-declares them with const/let/var, engine.js gets
    # "Identifier 'gpx' has already been declared" SyntaxError and fails to load.
    _redecl_stripped = 0
    _new_lines = []
    for _line in js.split("\n"):
        _stripped = _line.strip()
        if re.match(r'^(const|let|var)\s+(gpx|grect)\s*[=\(]', _stripped) or \
           re.match(r'^function\s+(gpx|grect)\s*\(', _stripped):
            _new_lines.append("// [engine.js provides gpx/grect — redecl removed]")
            _redecl_stripped += 1
        else:
            _new_lines.append(_line)
    if _redecl_stripped:
        js = "\n".join(_new_lines)
        print(f"  [PATCH] Stripped {_redecl_stripped}× gpx/grect redecl in {label}", file=sys.stderr)

    # Fix common AI mistakes: ctx.rect/ctx.px or g.rect/g.px → grect(ctx,...)/gpx(ctx,...)
    # Also fix g.grect(...) → grect(g, ...) and g.gpx(...) → gpx(g, ...)
    for pattern, repl, name in [
        (r"(\w+)\.px\s*\(", r"gpx(\1, ", "ctx.px/g.px"),
        (r"(\w+)\.rect\s*\(", r"grect(\1, ", "ctx.rect/g.rect"),
        (r"(\w+)\.grect\s*\(", r"grect(\1, ", "g.grect"),
        (r"(\w+)\.gpx\s*\(", r"gpx(\1, ", "g.gpx"),
    ]:
        new_js, n = re.subn(pattern, repl, js)
        if n:
            js = new_js
            print(f"  [PATCH] Fixed {n}× {name} → grect/gpx in {label}", file=sys.stderr)

    # BACKGROUNDS are called as BACKGROUNDS[i](ctx) — engine passes ctx explicitly.
    # grect/gpx need ctx as first arg; patch their first arg to 'ctx' if it's any identifier.
    # NOTE: do NOT patch bare rect()/px() — engine defines rect(x,y,w,h,c) and px(x,y,c)
    # where the first arg IS the coordinate, not ctx. Patching those would break rendering.
    if "window.BACKGROUNDS" in expected_globals:
        bg_js, n1 = re.subn(r'\bgrect\([a-zA-Z_]\w*\s*,', 'grect(ctx,', js)
        bg_js, n2 = re.subn(r'\bgpx\([a-zA-Z_]\w*\s*,', 'gpx(ctx,', bg_js)
        total = n1 + n2
        if total:
            js = bg_js
            print(f"  [PATCH] Fixed {total}× grect/gpx →ctx in BACKGROUNDS in {label}", file=sys.stderr)

    # Note: window.rect / window.px overrides in pixel art are handled at runtime
    # by player.html which restores the engine's correct implementations after
    # pixel art loads. No need to strip here (regex-based stripping is fragile).

    # Fix truncated hex color strings (LLM output cut off mid-string)
    js = _repair_truncated_strings(js, label)

    # Fix incomplete gpx/grect lines (truncated before the opening paren)
    js = _repair_incomplete_draw_calls(js, label)

    # Fix truncated function definitions (LLM output cut off mid-function)
    js = _repair_truncated_icon_functions(js, label)

    # Fix unclosed braces within this individual piece
    js = _fix_unclosed_braces(js, label)

    # Known top-level globals that each piece should produce
    all_globals = {
        "window.ICONS", "window.CHAR_DRAW_FNS", "window.PORTRAITS",
        "window.BACKGROUNDS", "function drawTitleLogo",
    }
    foreign_globals = all_globals - expected_globals

    # Strip declarations that don't belong in this piece
    for foreign in foreign_globals:
        if foreign in js:
            # Only strip if this piece also contains its OWN expected globals
            if any(eg in js for eg in expected_globals):
                idx = js.index(foreign)
                # Skip if inside a comment
                line_start = js.rfind("\n", 0, idx)
                prefix = js[line_start + 1:idx].strip()
                if prefix.startswith("//") or prefix.startswith("*"):
                    continue
                print(
                    f"  [PATCH] Renamed foreign '{foreign}' → _DUP_ in {label}",
                    file=sys.stderr,
                )
                # Rename to var _DUP_X to avoid duplicate const error
                if foreign.startswith("const "):
                    js = js.replace(foreign, foreign.replace("const ", "var _DUP_"), 1)
                elif foreign.startswith("window."):
                    js = js.replace(foreign, foreign.replace("window.", "window._DUP_"), 1)
                elif foreign.startswith("function "):
                    fn_name = foreign.split(" ", 1)[1]
                    js = js.replace(foreign, f"function _DUP_{fn_name}", 1)

    return js


async def _patch_pixel_art(js: str, knowledge: dict) -> str:
    """Detect missing pixel art globals, inject fallbacks, and validate in sandbox."""
    patches = []
    char_ids = [c["id"] for c in knowledge.get("characters", [])]

    if "ICONS" not in js:
        patches.append("\nwindow.ICONS = {};\n")
        print("  [PATCH] Missing ICONS — injected empty", file=sys.stderr)

    if "PORTRAITS" not in js and "var _DUP_PORTRAITS" not in js:
        entries = ", ".join(f"{cid}: {_FALLBACK_PORTRAIT}" for cid in char_ids)
        patches.append(f"\nwindow.PORTRAITS = {{{entries}}};\n")
        print("  [PATCH] Missing PORTRAITS — injected fallbacks", file=sys.stderr)

    if "CHAR_DRAW_FNS" not in js:
        entries = ", ".join(f"{cid}: function(g) {{ grect(g,8,0,8,8,'#c080a0'); grect(g,6,8,12,16,'#5a2848'); grect(g,8,24,8,8,'#3a1030'); }}" for cid in char_ids)
        patches.append(f"\nwindow.CHAR_DRAW_FNS = {{{entries}}};\n")
        print("  [PATCH] Missing CHAR_DRAW_FNS — injected fallbacks", file=sys.stderr)

    if "BACKGROUNDS" not in js:
        bgs = ", ".join([_FALLBACK_BACKGROUND] * 4)
        patches.append(f"\nwindow.BACKGROUNDS = [{bgs}];\n")
        print("  [PATCH] Missing BACKGROUNDS — injected fallbacks", file=sys.stderr)

    if "drawTitleLogo" not in js:
        patches.append(f"\n{_FALLBACK_TITLE_LOGO}\n")
        print("  [PATCH] Missing drawTitleLogo — injected fallback", file=sys.stderr)

    # Final safety: fix incomplete draw calls, truncated functions, unclosed braces
    js = _repair_incomplete_draw_calls(js, "combined pixel art")
    js = _repair_truncated_icon_functions(js, "combined pixel art")
    js = _fix_unclosed_braces(js, "combined pixel art")

    result = js + "\n".join(patches)

    # Validate JS syntax using node --check if available
    result = _validate_js_syntax(result, "pixel_art")

    # Sandbox execution: validate globals and draw functions
    for round_idx in range(_PIXEL_ART_REPAIR_ROUNDS):
        sb = run_in_sandbox(result, label="pixel_art", mode="pixel_art")
        if sb.ok:
            if round_idx > 0:
                print(f"  [SANDBOX] pixel_art — fixed on round {round_idx + 1} ✓", file=sys.stderr)
            return result

        if sb.phase in ("", "UNKNOWN") and not sb.error_message:
            return result

        if sb.phase == "SETUP":
            print(f"  [SANDBOX-SKIP] pixel_art: sandbox unavailable, skipping repair", file=sys.stderr)
            return result

        print(
            f"  [SANDBOX-FIX] pixel_art round {round_idx + 1}/{_PIXEL_ART_REPAIR_ROUNDS}: "
            f"{sb.phase} — {sb.error_message.split(chr(10))[0][:120]}",
            file=sys.stderr,
        )

        repair_prompt = build_repair_prompt(result, sb, repair_mode="pixel_art")
        system = (
            "You are a JavaScript bug-fixer specializing in pixel art code. "
            "The code defines drawing globals (ICONS, CHAR_DRAW_FNS, PORTRAITS, "
            "BACKGROUNDS, drawTitleLogo) using gpx() and grect() helper functions. "
            "Fix the EXACT error — do not rewrite the whole file. "
            "Output ONLY the corrected complete JavaScript code. "
            "No markdown fences. No explanation."
        )
        try:
            fixed_raw = await _get_generate()(repair_prompt, system, max_tokens=_PIXEL_ART_REPAIR_TOKENS, step="pixel_art_repair")
            fixed = _strip_js_fences(fixed_raw)
            if len(fixed) >= len(result) * 0.5:
                result = fixed
                result = _repair_truncated_strings(result, "pixel_art_repair")
                result = _fix_unclosed_braces(result, "pixel_art_repair")
                result = _validate_js_syntax(result, "pixel_art_repair")
            else:
                print(f"  [SANDBOX-FIX] pixel_art repair too short, keeping current", file=sys.stderr)
                break
        except Exception as e:
            print(f"  [SANDBOX-FIX] pixel_art repair attempt {round_idx + 1} failed: {e}", file=sys.stderr)
            break

    # Final check
    final = run_in_sandbox(result, label="pixel_art_final", mode="pixel_art")
    if not final.ok:
        print(
            f"  [SANDBOX-WARN] pixel_art still has errors after {_PIXEL_ART_REPAIR_ROUNDS} repairs: "
            f"{final.phase} — {final.error_message.split(chr(10))[0][:80]}",
            file=sys.stderr,
        )

    return result


def _ckpt_size_label(data) -> str:
    """Human-readable size label for checkpoint data."""
    if isinstance(data, str):
        n = len(data)
        return f"{n:,}ch" if n < 10000 else f"{n/1000:.1f}k ch"
    if isinstance(data, dict):
        keys = list(data.keys())
        return f"dict[{len(keys)} keys: {', '.join(keys[:5])}]"
    if isinstance(data, list):
        return f"list[{len(data)} items]"
    return str(type(data).__name__)


async def generate_game(
    topic: str,
    output_dir: str,
    theme: str = "pink-cute",
    chunk_id: str = "",
    exclude_mechanics: list[str] | None = None,
    game_index: int = 0,
    total_games: int = 1,
    locale: str = DEFAULT_LOCALE,
    forced_title: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    model: str | None = None,
    personal_profile: dict | None = None,
) -> str:
    """Generate a complete educational game from a topic.

    Returns the path to the generated index.html.
    """
    _current_generate_ctx.set(_bind_api_config(api_key, base_url, model))

    t_total = time.monotonic()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    ckpt_path = output_path / "_checkpoint.json"

    engine_dir = Path(__file__).resolve().parent.parent / "engine"
    if not engine_dir.exists():
        raise FileNotFoundError(
            f"Engine directory not found: {engine_dir}. "
            "Make sure the engine/ folder is alongside generator/."
        )

    _ckpt_lock = asyncio.Lock()

    async def _save_ckpt(key: str, data):
        async with _ckpt_lock:
            ckpt = {}
            if ckpt_path.exists():
                try: ckpt = json.loads(ckpt_path.read_text(encoding="utf-8"))
                except Exception: pass
            ckpt[key] = data
            ckpt_path.write_text(json.dumps(ckpt, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  [checkpoint] saved: {key} ({_ckpt_size_label(data)})", file=sys.stderr)

    def _load_ckpt(key: str):
        if not ckpt_path.exists():
            return None
        try:
            ckpt = json.loads(ckpt_path.read_text(encoding="utf-8"))
            if key in ckpt:
                print(f"  [checkpoint] loaded: {key}", file=sys.stderr)
                return ckpt[key]
        except Exception: pass
        return None

    # Step 1: Knowledge decomposition
    topic_display = topic[:80] + "..." if len(topic) > 80 else topic
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"  EdGameClaw Generator — Topic: {topic_display}", file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)

    print(f"\n[1/6] Analyzing topic and building knowledge structure...", file=sys.stderr)
    if exclude_mechanics:
        print(f"  Excluded mechanics: {exclude_mechanics}", file=sys.stderr)

    knowledge = _load_ckpt("knowledge")
    if knowledge is None:
        t0 = time.monotonic()
        knowledge = await _step_with_retry(
            _step_knowledge, topic, theme, exclude_mechanics, game_index, total_games, locale,
            personal_profile,
            label="knowledge",
        )
        print(
            f"  Done in {time.monotonic() - t0:.1f}s — "
            f"{len(knowledge.get('chunks', []))} chunks, "
            f"{knowledge.get('totalChapters', '?')} chapters",
            file=sys.stderr,
        )
        await _save_ckpt("knowledge", knowledge)

    # Respect the caller-provided title (e.g. user's playground input) over LLM-generated title
    if forced_title:
        knowledge["title"] = forced_title

    knowledge_json = json.dumps(knowledge, ensure_ascii=False, indent=2)

    # Slimmed-down knowledge_json variants to reduce token usage in dialog/art steps.
    # dialog only needs narrative fields + chunk content; art only needs visual context.
    _dialog_knowledge = {
        k: knowledge[k]
        for k in ("title", "subtitle", "worldSetting", "narrativeTheme", "characters", "levelNames")
        if k in knowledge
    }
    _dialog_knowledge["chunks"] = [
        {fk: c[fk] for fk in ("title", "content", "conceptSummary", "narrativeHook", "type") if fk in c}
        for c in knowledge.get("chunks", [])
    ]
    dialog_knowledge_json = json.dumps(_dialog_knowledge, ensure_ascii=False, indent=2)

    _art_knowledge = {
        k: knowledge[k]
        for k in ("title", "subtitle", "worldSetting", "narrativeTheme", "characters", "icons")
        if k in knowledge
    }
    # Keep narrativeHook per chunk so backgrounds prompt can build _story_arc
    _art_knowledge["chunks"] = [
        {"title": c.get("title", ""), "narrativeHook": c.get("narrativeHook", "")}
        for c in knowledge.get("chunks", [])
    ]
    art_knowledge_json = json.dumps(_art_knowledge, ensure_ascii=False, indent=2)

    chunks = knowledge.get("chunks", [])
    num_chunks = len(chunks)

    scene_descriptions = _derive_scene_descriptions(knowledge)

    print(f"\n[2/6] Writing story dialog and character interactions...", file=sys.stderr)
    t0 = time.monotonic()

    icon_names = knowledge.get('icons', [])

    _completed_steps = 0
    _total_steps = 6 + len(chunks)
    def _report_step(label: str):
        nonlocal _completed_steps
        _completed_steps += 1
        print(f"[{_completed_steps}/{_total_steps}] {label}", file=sys.stderr)

    async def _ckpt_task(name, coro_factory, done_label: str):
        """coro_factory: callable that returns a coroutine. Avoids creating coro when cached."""
        cached = _load_ckpt(name)
        if cached is not None:
            _report_step(done_label + " (cached)")
            return cached
        result = await coro_factory()
        try:
            await _save_ckpt(name, result)
        except Exception as e:
            print(f"  [checkpoint] WARN: failed to save {name}: {e}", file=sys.stderr)
        _report_step(done_label)
        return result

    dialog_task = asyncio.create_task(_ckpt_task("dialog",
        lambda: _step_dialog(topic, dialog_knowledge_json, theme, locale),
        "Story dialog complete"))
    icons_task = asyncio.create_task(_ckpt_task("pixel_icons",
        lambda: _step_pixel_art_icons(topic, icon_names, theme, locale),
        "Game icons ready"))
    chars_task = asyncio.create_task(_ckpt_task("pixel_chars",
        lambda: _step_pixel_art_chars(topic, art_knowledge_json, theme, locale),
        "Character sprites ready"))
    backgrounds_task = asyncio.create_task(_ckpt_task("pixel_backgrounds",
        lambda: _step_pixel_art_backgrounds(topic, art_knowledge_json, scene_descriptions, theme, locale),
        "Scene backgrounds ready"))
    cover_task = asyncio.create_task(_ckpt_task("cover_art",
        lambda: _step_cover_art(topic, art_knowledge_json, theme, locale, scene_descriptions=scene_descriptions),
        "Cover art ready"))
    # All chunks use custom simulation (one sim_N per chapter)
    custom_chunks = list(enumerate(chunks))
    print(f"  Minigame: {len(custom_chunks)} custom simulations (one per chapter)", file=sys.stderr)

    # Custom simulation only: no template-based minigame data (saves token).
    async def _empty_dict():
        return {}

    minigame_task = asyncio.create_task(_empty_dict())

    core_tasks = [dialog_task, icons_task, chars_task, backgrounds_task, cover_task, minigame_task]
    core_names = ["dialog", "pixel_icons", "pixel_chars", "pixel_backgrounds", "cover_art", "minigame_data"]

    async def _safe_sim(topic_: str, chunk_: dict, idx_: int, theme_: str, locale_: str, all_chunks_: list[dict] | None = None):
        sim_key = f"sim_{idx_}"
        cached = _load_ckpt(sim_key)
        if cached is not None:
            _report_step(f"Custom simulation {idx_+1} ready (cached)")
            return (idx_, cached)
        try:
            result = await _step_simulation_code(
                topic_, chunk_, idx_, theme_, locale_, all_chunks_,
            )
            await _save_ckpt(sim_key, result)
            _report_step(f"Custom simulation {idx_+1}: {chunk_.get('title', '')[:30]}")
            return (idx_, result)
        except Exception as e:
            print(
                f"  [SIM FALLBACK] sim_{idx_}: generation failed ({e}), using fallback",
                file=sys.stderr,
            )
            fb = _build_fallback_sim(idx_, chunk_, theme_)
            await _save_ckpt(sim_key, fb)
            _report_step(f"Custom simulation {idx_+1} (fallback)")
            return (idx_, fb)

    sim_tasks = []
    for idx, chunk in custom_chunks:
        sim_tasks.append(asyncio.create_task(
            _safe_sim(topic, chunk, idx, theme, locale, all_chunks_=chunks)
        ))

    all_results = await asyncio.gather(
        *core_tasks, *sim_tasks, return_exceptions=True,
    )

    core_results = all_results[:6]
    sim_results = all_results[6:]

    for i, (name, result) in enumerate(zip(core_names, core_results)):
        if isinstance(result, Exception):
            print(f"  [ERROR] {name} generation failed: {result}", file=sys.stderr)
            if name in ("dialog", "minigame_data"):
                raise result

    script = core_results[0] if not isinstance(core_results[0], Exception) else []
    script = _fix_script_sim_refs(script, chunks)
    icons_js = core_results[1] if not isinstance(core_results[1], Exception) else ""
    chars_js = core_results[2] if not isinstance(core_results[2], Exception) else ""
    backgrounds_js = core_results[3] if not isinstance(core_results[3], Exception) else ""
    cover_js = core_results[4] if not isinstance(core_results[4], Exception) else ""
    minigame_data = core_results[5] if not isinstance(core_results[5], Exception) else {}

    icons_js = _sanitize_pixel_art_piece(
        icons_js, {"window.ICONS"}, "pixel_icons"
    )
    chars_js = _sanitize_pixel_art_piece(
        chars_js, {"window.CHAR_DRAW_FNS", "window.PORTRAITS"}, "pixel_chars"
    )
    backgrounds_js = _sanitize_pixel_art_piece(
        backgrounds_js, {"window.BACKGROUNDS", "function drawTitleLogo"}, "pixel_backgrounds"
    )
    pixel_art_js = "\n;\n".join(filter(None, [icons_js, chars_js, backgrounds_js]))

    minigame_data = _validate_and_repair_minigame_data(minigame_data, label=f"(topic: {topic[:40]})")

    # Generate supplemental minigame-specific icons
    try:
        mg_extra_icons = await _step_minigame_icons(
            topic, minigame_data, icon_names, theme, locale,
        )
        if mg_extra_icons:
            # Inject extra icon definitions into the ICONS object
            if "window.ICONS" in icons_js and icons_js.rstrip().endswith("};"):
                icons_js = icons_js.rstrip()[:-2] + ",\n" + mg_extra_icons + "\n};"
            else:
                icons_js += "\n" + mg_extra_icons
            print(f"  [minigame-icons] Added {len(mg_extra_icons):,}ch of supplemental icons", file=sys.stderr)
        else:
            print(f"  [minigame-icons] All referenced icons already covered", file=sys.stderr)
    except Exception as e:
        print(f"  [minigame-icons] WARN: supplemental icon generation failed: {e}", file=sys.stderr)

    simulation_codes: dict[str, str] = {}
    for result in sim_results:
        if isinstance(result, Exception):
            print(f"  [WARN] custom simulation generation exception: {result}", file=sys.stderr)
        else:
            idx, code = result
            sim_name = f"sim_{idx}"
            simulation_codes[sim_name] = code

    print(
        f"  Content generation done in {time.monotonic() - t0:.1f}s — "
        f"{len(simulation_codes)} custom simulations",
        file=sys.stderr,
    )

    # ── Pixel Art Review Pass ─────────────────────────────────────────────
    print(f"\n[{_total_steps}/{_total_steps}] Polishing pixel art...", file=sys.stderr)
    t_review = time.monotonic()

    char_requirements = "角色精灵 CHAR_DRAW_FNS（24×36）和头像 PORTRAITS（32×32），共3个角色：mentor（老师人形）, pet（宠物精灵/小动物，非人形）, player"
    bg_requirements = "4个背景 BACKGROUNDS（128×96，无参数函数）和 drawTitleLogo（64×64，带g参数）"
    cover_requirements = "封面 drawCover(g, w, h)，128×96，至少60个绘制命令，分层构图"
    icon_requirements = f"图标集 ICONS，包含 {len(icon_names)} 个图标：{', '.join(icon_names[:10])}"

    review_pieces = {
        "icons":       (icons_js,       icon_requirements),
        "chars":       (chars_js,       char_requirements),
        "backgrounds": (backgrounds_js, bg_requirements),
        "cover":       (cover_js,       cover_requirements),
    }
    review_results = await _step_review_pixel_art_batch(review_pieces, theme)

    icons_js       = review_results.get("icons",       icons_js)
    chars_js       = review_results.get("chars",       chars_js)
    backgrounds_js = review_results.get("backgrounds", backgrounds_js)
    cover_js       = review_results.get("cover",       cover_js)

    await _save_ckpt("reviewed_icons",       icons_js)
    await _save_ckpt("reviewed_chars",       chars_js)
    await _save_ckpt("reviewed_backgrounds", backgrounds_js)
    await _save_ckpt("reviewed_cover",       cover_js)

    icons_js = _sanitize_pixel_art_piece(
        icons_js, {"window.ICONS"}, "reviewed_icons"
    )
    chars_js = _sanitize_pixel_art_piece(
        chars_js, {"window.CHAR_DRAW_FNS", "window.PORTRAITS"}, "reviewed_chars"
    )
    backgrounds_js = _sanitize_pixel_art_piece(
        backgrounds_js, {"window.BACKGROUNDS", "function drawTitleLogo"}, "reviewed_backgrounds"
    )
    pixel_art_js = "\n;\n".join(filter(None, [icons_js, chars_js, backgrounds_js]))

    print(
        f"  Pixel art review done in {time.monotonic() - t_review:.1f}s",
        file=sys.stderr,
    )
    # ────────────────────────────────────────────────────────────────────────

    # Validate and patch pixel art JS for missing globals + sandbox validation
    pixel_art_js = await _patch_pixel_art(pixel_art_js, knowledge)

    # Strip gpx/grect redecls from cover_js (same reason as pixel_art_js)
    cover_js = _sanitize_pixel_art_piece(cover_js, {"function drawCover"}, "cover_js")

    # Sandbox validation for cover art
    cover_js = await _sandbox_validate_cover(cover_js)

    # Build game config (defensive: knowledge may have characters missing "id" or "name")
    characters = {}
    for i, ch in enumerate(knowledge.get("characters", [])):
        if not isinstance(ch, dict):
            continue
        cid = ch.get("id") or f"char_{i}"
        characters[cid] = {"name": ch.get("name", "")}

    mechanics_used = [f"sim_{i}" for i, c in enumerate(knowledge.get("chunks", []))]
    end_screen = {
        "mechanics": [
            {"mechanic": f"sim_{i}", "knowledge": c.get("title", "")}
            for i, c in enumerate(knowledge.get("chunks", []))
        ],
        "icons": list({
            icon
            for mg_data in minigame_data.values()
            if isinstance(mg_data, dict)
            for pair in mg_data.get("pairs", [])
            if (icon := pair.get("icon"))
        })[:8],
    }

    # Add sim_N metadata for every chunk (all use custom simulation)
    for idx, chunk in custom_chunks:
        sim_name = f"sim_{idx}"
        hint = chunk.get("simulationHint", "") or chunk.get("content", "")
        minigame_data[sim_name] = {
            "title": f"🔬 {chunk.get('title', 'Exploration')}",
            "subtitle": hint[:300],
            "_tutorial": hint,  # full text shown in tutorial overlay before sim starts
            "portrait": "mentor",
        }

    ui_strings = get_ui_strings(locale)

    # Override levelNames with content-specific names from knowledge if available
    knowledge_level_names = knowledge.get("levelNames")
    if knowledge_level_names and isinstance(knowledge_level_names, list) and len(knowledge_level_names) >= 3:
        # Pad or trim to exactly 6 entries (ui expects 6: index 0 unused, 1-5 shown)
        names = list(knowledge_level_names)
        while len(names) < 6:
            names.append(names[-1])
        names = names[:6]
        ui_strings = dict(ui_strings)  # copy so we don't mutate module-level dict
        ui_strings["levelNames"] = names
        print(f"  [levelNames] using content-specific: {names}", file=sys.stderr)

    audio_mood = knowledge.get("audioMood")
    audio_bgm = get_audio_profile(theme, mood_hint=audio_mood)
    print(f"  Audio mood: {audio_mood or '(default)'} → profile tracks: {list(audio_bgm.keys())}", file=sys.stderr)

    chapter_titles = [
        (ch.get("title") or "").strip() or f"第{i + 1}章"
        for i, ch in enumerate(chunks)
    ]

    config = {
        "title": knowledge.get("title", topic),
        "subtitle": knowledge.get("subtitle", ""),
        "description": knowledge.get("description", ""),
        "totalChapters": knowledge.get("totalChapters", 6),
        "defaultPlayerName": knowledge.get("defaultPlayerName", ui_strings.get("defaultPlayer", "Explorer")),
        "characters": characters,
        "minigames": minigame_data,
        "endScreen": end_screen,
        "chapterTitles": chapter_titles,
        "theme": get_theme_css(theme),
        "audio": {"bgm": audio_bgm},
        "ui": ui_strings,
        "locale": locale,
    }
    if chunk_id:
        config["chunkId"] = chunk_id

    # ── Pre-assembly validation ─────────────────────────────────────────
    _script_sims = sorted(
        cmd["game"] for cmd in script
        if isinstance(cmd, dict)
        and cmd.get("type") == "minigame"
        and isinstance(cmd.get("game", ""), str)
        and cmd["game"].startswith("sim_")
    )
    _code_sims = sorted(simulation_codes.keys())
    _data_sims = sorted(k for k in minigame_data if k.startswith("sim_"))
    _es_sims = sorted(
        m["mechanic"] for m in end_screen.get("mechanics", [])
        if isinstance(m, dict) and m.get("mechanic", "").startswith("sim_")
    )

    if _script_sims != _code_sims:
        print(
            f"  [WARN] sim key mismatch: script={_script_sims}, codes={_code_sims}. "
            "Assembler will attempt ordered remap.",
            file=sys.stderr,
        )
    if _script_sims != _data_sims:
        print(
            f"  [WARN] sim data mismatch: script={_script_sims}, minigame_data={_data_sims}. "
            "Assembler will attempt remap of config keys.",
            file=sys.stderr,
        )

    for sim_name in _script_sims:
        if sim_name not in simulation_codes:
            cached = _load_ckpt(sim_name)
            if cached:
                simulation_codes[sim_name] = cached
                print(
                    f"  [RECOVERY] {sim_name} not in generation results — recovered from checkpoint",
                    file=sys.stderr,
                )
            else:
                print(
                    f"  [WARN] {sim_name} referenced in script but no custom code generated — "
                    "will use generic fallback simulation template",
                    file=sys.stderr,
                )

    # Step 6: Assembly
    print(f"\n[{_total_steps}/{_total_steps}] Assembling final game...", file=sys.stderr)
    t0 = time.monotonic()
    html_path = str(output_path / "index.html")

    content = {
        "config": config,
        "pixel_art_js": pixel_art_js,
        "script": script,
        "minigame_data": minigame_data,
        "theme": theme,
        "simulation_codes": simulation_codes,
        "cover_js": cover_js,
    }

    out_content = {}
    assemble(str(engine_dir), content, html_path, out_content=out_content)

    # Step 6b: Write data package for player-based playback (encrypt when GAME_PACKAGE_SECRET is set)
    from .package_builder import write_package
    write_package(out_content, str(engine_dir), str(output_path), write_json=True, write_encrypted=True)

    # Save cover art as cover.js (self-registering to window._EDGAME_COVERS)
    if cover_js and "drawCover" in cover_js:
        cover_fn = cover_js
        # Ensure the function is named drawCover
        if not cover_fn.startswith("function drawCover"):
            cover_fn = cover_fn.replace("function(g, w, h)", "function drawCover(g, w, h)", 1)
            cover_fn = cover_fn.replace("function (g, w, h)", "function drawCover(g, w, h)", 1)
        cover_id = chunk_id or f"game_{game_index}"
        cover_registry = (
            f"(function(){{\n"
            f"  window._EDGAME_COVERS = window._EDGAME_COVERS || {{}};\n"
            f"  window._EDGAME_COVERS['{cover_id}'] = {cover_fn};\n"
            f"}})();\n"
        )
        cover_js_path = output_path / "cover.js"
        cover_js_path.write_text(cover_registry, encoding="utf-8")
        print(f"  Cover art saved: {cover_js_path}", file=sys.stderr)
    else:
        print("  [WARN] Cover art not generated or missing drawCover function", file=sys.stderr)

    # Save locale JSON for translation support
    locale_data = extract_locale_content(config, script)
    locales_dir = output_path / "locales"
    locales_dir.mkdir(parents=True, exist_ok=True)
    locale_path = locales_dir / f"{locale}.json"
    locale_path.write_text(
        json.dumps(locale_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"  Locale file: {locale_path}", file=sys.stderr)

    print(f"  Done in {time.monotonic() - t0:.1f}s", file=sys.stderr)

    # Clean up checkpoint on success
    if ckpt_path.exists():
        try: ckpt_path.unlink()
        except Exception: pass

    elapsed_total = time.monotonic() - t_total
    print(
        f"\n{'='*60}\n"
        f"  Generation complete in {elapsed_total:.1f}s\n"
        f"  Output: {html_path}\n"
        f"{'='*60}\n",
        file=sys.stderr,
    )

    return html_path


if __name__ == "__main__":
    topic = sys.argv[1] if len(sys.argv) > 1 else "人类记忆的工作原理"
    output = sys.argv[2] if len(sys.argv) > 2 else "./output"
    theme = sys.argv[3] if len(sys.argv) > 3 else "pink-cute"
    locale = sys.argv[4] if len(sys.argv) > 4 else "zh"
    result = asyncio.run(generate_game(topic, output, theme=theme, locale=locale))
    print(result)
