# Created by Yuqi Hang (github.com/yh2072)
"""Sandbox execution for generated game code (simulations, pixel art, cover art).

Priority:
  1. Node.js full sandbox (best — catches syntax + runtime errors)
  2. esprima Python syntax check (fallback — catches syntax errors only)
  3. Skip entirely (if neither available)

The repair loop (generate → sandbox → LLM-fix → retry) lives in pipeline.py.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

_HARNESS = Path(__file__).with_name("sandbox_harness.js")
_TIMEOUT = 15  # seconds


# ── 1. Locate Node.js ────────────────────────────────────────────────────────

def _find_node() -> str | None:
    if os.environ.get("NODE_BINARY"):
        return os.environ["NODE_BINARY"]
    found = shutil.which("node")
    if found:
        return found
    for p in [
        "/usr/local/bin/node", "/usr/bin/node",
        "/opt/homebrew/bin/node",
        "/root/.nix-profile/bin/node",
        "/nix/var/nix/profiles/default/bin/node",
    ]:
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    return None

_NODE_BIN: str | None = _find_node()


# ── 2. Check esprima availability ────────────────────────────────────────────

def _esprima_available() -> bool:
    try:
        import esprima  # pyright: ignore[reportMissingImports]  # noqa: F401
        return True
    except ImportError:
        return False

_HAS_ESPRIMA: bool = _esprima_available()

if _NODE_BIN:
    print(f"  [sandbox] node found at: {_NODE_BIN}", file=sys.stderr)
elif _HAS_ESPRIMA:
    print("  [sandbox] node not found — using esprima for syntax-only validation", file=sys.stderr)
else:
    print("  [sandbox] WARNING: no JS validator available (node + esprima both missing)", file=sys.stderr)


# ── Data types ────────────────────────────────────────────────────────────────

@dataclass
class SandboxResult:
    ok: bool
    phase: str          # "SYNTAX" | "EXEC" | "RUNTIME" | "NO_REGISTER" | ""
    error_message: str  # human-readable error
    sim_name: str       # which sim failed (for RUNTIME errors)
    raw_stderr: str     # full stderr for debugging


# ── esprima fallback ──────────────────────────────────────────────────────────

def _run_esprima(js_code: str, label: str) -> SandboxResult:
    """Syntax-only check via esprima (no runtime validation)."""
    try:
        import esprima  # pyright: ignore[reportMissingImports]
        esprima.parseScript(js_code, tolerant=False)
        tag = f"[{label}] " if label else ""
        print(f"  {tag}esprima syntax ✓", file=sys.stderr)
        return SandboxResult(ok=True, phase="", error_message="", sim_name="", raw_stderr="")
    except Exception as e:
        err_msg = str(e)
        tag = f"[{label}] " if label else ""
        print(f"  {tag}esprima syntax ✗ SYNTAX: {err_msg[:120]}", file=sys.stderr)
        return SandboxResult(
            ok=False, phase="SYNTAX",
            error_message=err_msg,
            sim_name="", raw_stderr=err_msg,
        )


# ── Main entry point ──────────────────────────────────────────────────────────

def run_in_sandbox(js_code: str, label: str = "", mode: str = "sim") -> SandboxResult:
    """Validate JS code.

    Tries Node.js full sandbox first; falls back to esprima syntax check
    if Node.js is not available; returns ok=True (skip) if neither works.
    """
    # ── Node.js path ──
    if _NODE_BIN and _HARNESS.exists():
        fd, tmp = tempfile.mkstemp(suffix=".js", prefix="sandbox_")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(js_code)

            cmd = [_NODE_BIN, str(_HARNESS)]
            if mode != "sim":
                cmd += ["--mode", mode]
            cmd.append(tmp)

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=_TIMEOUT,
            )

            stderr = result.stderr.strip()
            stdout = result.stdout.strip()

            if result.returncode == 0 and stdout.startswith("SANDBOX_OK:"):
                tag = f"[{label}] " if label else ""
                sims = stdout.split(":", 1)[1]
                print(f"  {tag}sandbox ✓ ({sims})", file=sys.stderr)
                return SandboxResult(ok=True, phase="", error_message="", sim_name=sims, raw_stderr="")

            m = re.search(r"SANDBOX_ERROR:(\w+):(?:(\w+):)?(.*)", stderr)
            if m:
                phase = m.group(1)
                extra = m.group(2) or ""
                msg = m.group(3) or ""
                sim_name = extra if phase == "RUNTIME" else ""
                err_msg = msg
                stack_lines = [l for l in stderr.split("\n") if l and not l.startswith("SANDBOX_ERROR")]
                if stack_lines:
                    err_msg += "\n" + "\n".join(stack_lines[:4])
            else:
                phase = "UNKNOWN"
                sim_name = ""
                err_msg = stderr[:500] if stderr else f"exit code {result.returncode}"

            tag = f"[{label}] " if label else ""
            print(f"  {tag}sandbox ✗ {phase}: {err_msg.split(chr(10))[0][:120]}", file=sys.stderr)
            return SandboxResult(ok=False, phase=phase, error_message=err_msg, sim_name=sim_name, raw_stderr=stderr)

        except subprocess.TimeoutExpired:
            print(f"  [{label}] sandbox ✗ TIMEOUT ({_TIMEOUT}s)", file=sys.stderr)
            return SandboxResult(
                ok=False, phase="TIMEOUT",
                error_message=f"Code execution timed out after {_TIMEOUT}s (possible infinite loop)",
                sim_name="", raw_stderr="timeout",
            )
        except FileNotFoundError:
            pass  # fall through to esprima
        finally:
            try:
                os.unlink(tmp)
            except OSError:
                pass

    # ── esprima fallback ──
    if _HAS_ESPRIMA:
        return _run_esprima(js_code, label)

    # ── No validator available — skip ──
    return SandboxResult(ok=True, phase="", error_message="", sim_name="", raw_stderr="(no validator)")


def _extract_first_line_number(text: str) -> int | None:
    """Extract the first JS line number mentioned in a stack trace/message."""
    matches = re.findall(r":(\d+):\d+", text or "")
    if not matches:
        return None
    try:
        return int(matches[0])
    except ValueError:
        return None


def _extract_code_window(js_code: str, line_no: int | None, radius: int = 18) -> str:
    """Return a small numbered snippet around the failing line."""
    lines = js_code.splitlines()
    if not lines:
        return ""

    if line_no is None or line_no < 1:
        start = max(0, len(lines) - radius * 2)
        end = len(lines)
    else:
        start = max(0, line_no - radius - 1)
        end = min(len(lines), line_no + radius)

    snippet = []
    for idx in range(start, end):
        snippet.append(f"{idx + 1}: {lines[idx]}")
    return "\n".join(snippet)


def _extract_fix_template(error_message: str) -> str:
    """Extract an explicit fix template from sandbox text if one is present."""
    if not error_message:
        return ""
    match = re.search(r"Fix template:\s*(.+)", error_message, flags=re.IGNORECASE)
    if match:
        return match.group(1).strip()
    match = re.search(r"Suggested fix:\s*(.+)", error_message, flags=re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ""


def _repair_mode_label(repair_mode: str) -> str:
    repair_mode = (repair_mode or "implement").strip().lower()
    return {
        "implement": "first-pass implementation repair",
        "refine": "targeted refinement repair",
        "cover": "cover-art repair",
        "pixel_art": "pixel-art repair",
    }.get(repair_mode, repair_mode.replace("_", " "))


def build_repair_prompt(js_code: str, sandbox_result: SandboxResult, repair_mode: str = "implement") -> str:
    """Build a prompt for the LLM to fix the code based on sandbox errors."""
    message = sandbox_result.error_message or sandbox_result.raw_stderr or ""
    line_no = _extract_first_line_number(message)
    window = _extract_code_window(js_code, line_no)

    repair_mode = (repair_mode or "implement").strip().lower()
    mode_label = _repair_mode_label(repair_mode)
    code_limit = 24000 if repair_mode != "refine" else 16000
    context_limit = 12000 if repair_mode != "refine" else 8000

    extra_rules = []
    msg_lower = message.lower()
    fix_template = _extract_fix_template(message)
    if fix_template:
        extra_rules.append(f"- Suggested fix template: {fix_template}")
    if repair_mode == "refine":
        extra_rules.append("- This is a refinement pass: make the smallest possible patch and keep working parts untouched.")
    else:
        extra_rules.append("- This is a direct repair pass: preserve the overall structure and patch only the broken area.")
    if "addEventListener" in message or "addeventlistener" in msg_lower:
        extra_rules.append("- Event binding template: const el = ct.querySelector('#id'); if (el) el.addEventListener('click', handler).")
    if "re-declared" in msg_lower:
        extra_rules.append("- Rename only the conflicting local binding and keep using the engine global directly.")
    if "top-level return" in msg_lower or "illegal return" in msg_lower:
        extra_rules.append("- Do not use top-level return. Move returns inside a function or callback, or replace them with a branch guard.")
    if "cannot read properties of undefined" in msg_lower and "addeventlistener" in msg_lower:
        extra_rules.append("- Null-check the query result before calling addEventListener().")

    extra_rules_text = "\n".join(extra_rules)
    if extra_rules_text:
        extra_rules_text += "\n"

    context_block = window if window else js_code[:code_limit]
    return (
        f"The following JavaScript code FAILED in the sandbox.\n\n"
        f"## Repair Mode: {mode_label}\n"
        f"## Error Phase: {sandbox_result.phase}\n"
        f"## Error Message:\n```\n{message[:800]}\n```\n\n"
        f"## Suggested Fix Template:\n{extra_rules_text or '- No explicit template available; fix the smallest broken section and keep the rest unchanged.'}\n"
        f"## Focused Context Around The Error:\n"
        f"```text\n{context_block[:context_limit]}\n```\n\n"
        f"## The Code (fix it and return the COMPLETE corrected version):\n"
        f"```javascript\n{js_code[:code_limit]}\n```\n\n"
        f"## Rules:\n"
        f"- Fix ONLY the error described above. Do not rewrite the entire file.\n"
        f"- Keep the same function names, same logic, same visual design.\n"
        f"- Prefer the smallest possible patch near the failing line.\n"
        f"- If a variable is undefined, declare it. If a method doesn't exist, fix the call.\n"
        f"- If there's a syntax error, fix the exact line.\n"
        f"- Output ONLY the complete corrected JavaScript code. No markdown fences. No explanation.\n"
    )
