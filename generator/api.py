# =============================================================================
# EdGameClaw — AI Game-Based Learning Studio
# Created by Yuqi Hang (github.com/yh2072)
# https://github.com/yh2072/edgameclaw
# =============================================================================
import asyncio
import contextvars
import os
import sys
import time

import httpx
from openai import AsyncOpenAI, RateLimitError, APIConnectionError, APIStatusError

# Default to OpenRouter for backward compatibility; allow override via env so we can
# point to OpenRouter-compatible or other Gemini-capable providers.
_OPENROUTER_BASE = os.environ.get("STUDIO_AI_BASE_URL", "https://openrouter.ai/api/v1")
_DEFAULT_MODEL = os.environ.get("STUDIO_MODEL", "google/gemini-3-flash-preview")

# Per-step model override: STUDIO_MODEL_<STEP> (e.g. STUDIO_MODEL_KNOWLEDGE, STUDIO_MODEL_SIM_DESIGN).
# Step names: knowledge, dialog, pixel_icons, pixel_chars, pixel_backgrounds, cover_art,
# sim_visual_objects, sim_design, sim_implement, sim_judge, sim_refine, review_batch, minigame_icons.
def get_model_for_step(step: str) -> str:
    key = f"STUDIO_MODEL_{step.upper()}"
    return os.environ.get(key, os.environ.get("STUDIO_MODEL", _DEFAULT_MODEL))

_clients: dict[str, AsyncOpenAI] = {}
_api_semaphore: asyncio.Semaphore | None = None

# When set by server (context) before running a studio job, each generate() call appends usage here for aggregation.
# Supports concurrent jobs: each task sets its own list via context.
_studio_usage_collector: list[dict] | None = None  # legacy; prefer _studio_usage_collector_ctx
_studio_usage_collector_ctx: contextvars.ContextVar[list[dict] | None] = contextvars.ContextVar("studio_usage_collector", default=None)


def _get_semaphore() -> asyncio.Semaphore:
    global _api_semaphore
    if _api_semaphore is None:
        _api_semaphore = asyncio.Semaphore(2)
    return _api_semaphore


def _make_client(api_key: str, base_url: str) -> AsyncOpenAI:
    # Strip to avoid Illegal header value (e.g. trailing newline from env)
    key = (api_key or "").strip()
    url = (base_url or "").strip().rstrip("/")
    return AsyncOpenAI(
        api_key=key,
        base_url=url,
        timeout=httpx.Timeout(600, connect=60),  # 10min for thinking models (Kimi K2.5, etc.)
        max_retries=0,
    )


def _get_base_url() -> str:
    """Read base URL at runtime so env changes take effect without restart."""
    return (os.environ.get("STUDIO_AI_BASE_URL") or "https://openrouter.ai/api/v1").strip()


def _get_client(api_key: str | None = None, base_url: str | None = None) -> tuple[AsyncOpenAI, str]:
    """Returns (client, cache_key) so caller can invalidate on error."""
    if api_key:
        api_key = api_key.strip()
        cache_key = f"{api_key[:8]}@{base_url or _get_base_url()}"
    else:
        cache_key = "__default__"
        api_key = (os.environ.get("OPENROUTER_API_KEY_studio") or os.environ.get("OPENROUTER_API_KEY") or "").strip()
        if not api_key:
            raise RuntimeError(
                "OPENROUTER_API_KEY_studio or OPENROUTER_API_KEY environment variable is not set. "
                "Export one before running the pipeline."
            )
        base_url = _get_base_url()

    resolved_url = (base_url or _get_base_url()).strip()
    if cache_key not in _clients:
        _clients[cache_key] = _make_client(api_key, resolved_url)
    return _clients[cache_key], cache_key


def _invalidate_client(cache_key: str):
    _clients.pop(cache_key, None)


def _estimate_tokens(text: str) -> int:
    """Rough token estimate: ~1.5 chars per token for CJK, ~4 for Latin."""
    cjk = sum(1 for c in text if '\u4e00' <= c <= '\u9fff' or '\u3000' <= c <= '\u303f')
    latin = len(text) - cjk
    return int(cjk / 1.5 + latin / 4)



# -- Created by Yuqi Hang (github.com/yh2072) --
async def generate(
    prompt: str,
    system_prompt: str,
    *,
    max_tokens: int = 4096,
    model: str | None = None,
    step: str | None = None,
    max_retries: int = 5,
    api_key: str | None = None,
    base_url: str | None = None,
) -> str:
    """Call the AI API with streaming, concurrency control, retry logic.
    When step= is set, model is taken from STUDIO_MODEL_<STEP> env (same api_key/base_url)."""
    if step:
        model = get_model_for_step(step)
    elif model is None:
        model = os.environ.get("STUDIO_MODEL", _DEFAULT_MODEL)
    last_error: Exception | None = None
    sem = _get_semaphore()

    prompt_est = _estimate_tokens(system_prompt) + _estimate_tokens(prompt)
    sys_len = len(system_prompt)
    usr_len = len(prompt)
    model_short = model.split("/")[-1] if "/" in model else model

    async with sem:
        client, cache_key = _get_client(api_key=api_key, base_url=base_url)
        base_used = base_url or _get_base_url()
        base_host = base_used.split("/")[2] if len(base_used.split("/")) > 2 else base_used

        print(
            f"  [api] → {model_short} @ {base_host}  prompt≈{prompt_est}tok "
            f"(sys={sys_len:,}ch usr={usr_len:,}ch)  max_out={max_tokens}",
            file=sys.stderr,
        )
        for attempt in range(1, max_retries + 1):
            if attempt > 1:
                await asyncio.sleep(0.5)

            t0 = time.monotonic()

            try:
                # OpenAI-compatible: /v1/chat/completions
                response = await client.chat.completions.create(
                    model=model,
                    max_tokens=max_tokens,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    stream=False,
                )
                content = (response.choices[0].message.content or "")
                u = getattr(response, "usage", None)
                if u:
                    collector = _studio_usage_collector_ctx.get()
                    if collector is not None:
                        collector.append({
                            "prompt_tokens": getattr(u, "prompt_tokens", 0) or 0,
                            "completion_tokens": getattr(u, "completion_tokens", 0) or 0,
                            "total_tokens": getattr(u, "total_tokens", 0) or 0,
                        })
                    elif _studio_usage_collector is not None:
                        _studio_usage_collector.append({
                            "prompt_tokens": getattr(u, "prompt_tokens", 0) or 0,
                            "completion_tokens": getattr(u, "completion_tokens", 0) or 0,
                            "total_tokens": getattr(u, "total_tokens", 0) or 0,
                        })

                elapsed = time.monotonic() - t0
                resp_len = len(content)
                out_tok_est = _estimate_tokens(content)
                tps = int(out_tok_est / elapsed) if elapsed > 0 else "?"
                truncation_risk = out_tok_est >= max_tokens * 0.88
                status_icon = "⚠️ TRUNC?" if truncation_risk else "✓"
                print(
                    f"  [api] {status_icon} {elapsed:.1f}s  ~{out_tok_est}tok/{max_tokens}  "
                    f"{tps} tok/s  resp={resp_len:,}ch",
                    file=sys.stderr,
                )
                if truncation_risk:
                    print(
                        f"  [api] ⚠️  output ~{out_tok_est} tok ≥ 88% of max_tokens={max_tokens} — "
                        f"code may be TRUNCATED. Consider increasing max_tokens or prompting for shorter output.",
                        file=sys.stderr,
                    )
                preview = content[:300].replace('\n', ' ') if content else "(empty)"
                print(f"  [api] preview: {preview}{'...' if resp_len > 300 else ''}", file=sys.stderr)

                if not content.strip():
                    wait = 5 * attempt
                    print(
                        f"  [api] ✗ empty response (attempt {attempt}/{max_retries}) "
                        f"— retrying in {wait}s",
                        file=sys.stderr,
                    )
                    last_error = RuntimeError("API returned empty content")
                    await asyncio.sleep(wait)
                    continue

                return content

            except RateLimitError as exc:
                last_error = exc
                wait = 15 * attempt
                print(
                    f"  [api] ⏳ rate limited attempt {attempt}/{max_retries} "
                    f"— waiting {wait}s",
                    file=sys.stderr,
                )
                await asyncio.sleep(wait)

            except APIConnectionError as exc:
                last_error = exc
                elapsed = time.monotonic() - t0
                _invalidate_client(cache_key)
                wait = 5 * attempt
                err_msg = str(exc).strip() or type(exc).__name__
                cause = getattr(exc, "__cause__", None)
                cause_msg = repr(cause) if cause else ""
                print(
                    f"  [api] ✗ connection error after {elapsed:.1f}s "
                    f"attempt {attempt}/{max_retries} — retrying in {wait}s",
                    file=sys.stderr,
                )
                print(f"  [api]   reason: {err_msg}", file=sys.stderr)
                if cause_msg:
                    print(f"  [api]   cause: {cause_msg}", file=sys.stderr)
                print(f"  [api]   base_url={base_used!r}", file=sys.stderr)
                await asyncio.sleep(wait)

            except APIStatusError as exc:
                last_error = exc
                elapsed = time.monotonic() - t0
                if exc.status_code >= 500:
                    wait = 5 * attempt
                    print(
                        f"  [api] ✗ server {exc.status_code} after {elapsed:.1f}s "
                        f"attempt {attempt}/{max_retries} — retrying in {wait}s",
                        file=sys.stderr,
                    )
                    await asyncio.sleep(wait)
                else:
                    raise

            except httpx.HTTPStatusError as exc:
                # httpx path; retry on 5xx/429
                last_error = exc
                elapsed = time.monotonic() - t0
                code = exc.response.status_code
                if code >= 500 or code == 429:
                    wait = 15 * attempt if code == 429 else 5 * attempt
                    print(
                        f"  [api] ✗ HTTP {code} after {elapsed:.1f}s "
                        f"attempt {attempt}/{max_retries} — retrying in {wait}s",
                        file=sys.stderr,
                    )
                    await asyncio.sleep(wait)
                else:
                    raise

    raise RuntimeError(
        f"API call failed after {max_retries} attempts: {last_error!r}"
    )
