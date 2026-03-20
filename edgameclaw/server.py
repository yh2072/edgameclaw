# =============================================================================
# EdGameClaw — AI Game-Based Learning Studio
# Created by Yuqi Hang (github.com/yh2072)
# https://github.com/yh2072/edgameclaw
# =============================================================================
"""EdGameClaw — Self-hosted AI Game-Based Learning Studio

Convert any learning material into playable game-based micro-courses using AI.
No database, no login, no cloud infrastructure required.

Usage:
    pip install -e .
    cp .env.example .env  # edit with your API key
    python -m uvicorn edgameclaw.server:app --reload --port 8000
    # OR: bash start.sh (sets PYTHONPATH for you)

Environment variables (set in .env):
    API_KEY         Your OpenAI-compatible API key (required)
    API_BASE_URL    API base URL (default: https://openrouter.ai/api/v1)
    MODEL           Model name (default: google/gemini-3-flash-preview)
    PORT            Server port (default: 8000)
    BIND_HOST       Listen address (default: 127.0.0.1; use 0.0.0.0 for LAN)
    EDGAMECLAW_HOME Optional. Data directory for courses/, assets/, jobs/, courses.json
                    (default: repo root in dev; current working directory when installed)
"""

from pathlib import Path as _PathForEnv

_pkg = _PathForEnv(__file__).resolve().parent
_repo = _pkg.parent
for _env_candidate in (
    _PathForEnv.cwd() / ".env",
    _repo / ".env",
    _pkg / ".env",
):
    if _env_candidate.exists():
        from dotenv import load_dotenv

        load_dotenv(_env_candidate)
        break

import asyncio
import contextvars
import io
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
import uuid
from pathlib import Path
from urllib.parse import urlparse

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# ── Paths ──────────────────────────────────────────────────────────────────
PACKAGE_DIR = Path(__file__).resolve().parent


def _install_root() -> Path:
    env = (os.environ.get("EDGAMECLAW_HOME") or "").strip()
    if env:
        return Path(env).expanduser().resolve()
    # Editable / git checkout: package is edgameclaw/edgameclaw/, repo root has pyproject.toml
    if (_repo / "pyproject.toml").exists():
        return _repo.resolve()
    # Installed wheel: mutable data lives next to cwd unless EDGAMECLAW_HOME is set
    return Path.cwd().resolve()


INSTALL_ROOT = _install_root()
COURSES_DIR = INSTALL_ROOT / "courses"
ASSETS_DIR = INSTALL_ROOT / "assets"
AUDIO_DIR = ASSETS_DIR / "audio"
JOBS_DIR = INSTALL_ROOT / "jobs"
STATIC_DIR = PACKAGE_DIR / "static"
ENGINE_DIR = PACKAGE_DIR / "engine"
REGISTRY = INSTALL_ROOT / "courses.json"

COURSES_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)
JOBS_DIR.mkdir(parents=True, exist_ok=True)

# ── AI Config ───────────────────────────────────────────────────────────────
API_KEY      = (os.environ.get("API_KEY") or "").strip()
API_BASE_URL = os.environ.get("API_BASE_URL", "https://openrouter.ai/api/v1").strip()
MODEL        = os.environ.get("MODEL", "google/gemini-3-flash-preview").strip()

# Node engine state server (starts alongside this server via Procfile)
ENGINE_STATE_URL = os.environ.get("ENGINE_STATE_URL", "http://127.0.0.1:3100").rstrip("/")

# Auto-spawn bundled node/ when nothing is listening (e.g. pip install without cloning).
# Set EDGAMECLAW_ENGINE_STATE_AUTO=0 to disable and run `node server.js` yourself.
_embedded_node_proc: subprocess.Popen | None = None


def _engine_state_port() -> int:
    u = urlparse(ENGINE_STATE_URL)
    if u.port:
        return int(u.port)
    return 3100


def _tcp_port_in_use(host: str, port: int) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.settimeout(0.25)
        return s.connect_ex((host, port)) == 0
    except OSError:
        return False
    finally:
        s.close()


def _maybe_start_embedded_node() -> None:
    """If bundled ``edgameclaw/node`` exists and the engine-state HTTP service is down, start it."""
    global _embedded_node_proc

    flag = (os.environ.get("EDGAMECLAW_ENGINE_STATE_AUTO") or "1").strip().lower()
    if flag in ("0", "false", "no", "off"):
        return
    nd = PACKAGE_DIR / "node"
    if not (nd / "server.js").exists():
        return
    host = urlparse(ENGINE_STATE_URL).hostname or "127.0.0.1"
    port = _engine_state_port()
    if _tcp_port_in_use(host, port):
        return
    node_exe = shutil.which("node")
    if not node_exe:
        print("[WARN] Node.js not found in PATH; install Node 18+ or set EDGAMECLAW_ENGINE_STATE_AUTO=0 if you run engine-state elsewhere.", flush=True)
        return
    env = {**os.environ, "PORT": str(port)}
    try:
        _embedded_node_proc = subprocess.Popen(
            [node_exe, "server.js"],
            cwd=str(nd),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        print(f"[EdGameClaw] Started bundled engine-state (Node) on port {port}", flush=True)
    except Exception as exc:
        print(f"[WARN] Could not start bundled engine-state Node service: {exc}", flush=True)


def _stop_embedded_node() -> None:
    global _embedded_node_proc
    if _embedded_node_proc is None:
        return
    try:
        _embedded_node_proc.terminate()
        _embedded_node_proc.wait(timeout=5)
    except Exception:
        try:
            _embedded_node_proc.kill()
        except Exception:
            pass
    _embedded_node_proc = None

# ── Themes (must match generator/assembler.py) ──────────────────────────────
THEMES = [
    "pink-cute", "ocean-dream", "forest-sage", "sunset-warm", "galaxy-purple",
    "candy-pop", "retro-amber", "china-porcelain", "china-cinnabar", "china-ink",
    "dunhuang", "forbidden-red", "china-landscape", "china-rouge",
    "renaissance", "baroque", "nordic", "victorian", "mediterranean",
    "fairy-tale", "detective", "sci-fi", "academy", "myth",
]

ALLOWED_LOCALES = frozenset({"zh", "en", "ja", "es", "fr", "ko", "ar", "de"})

# ── Logging filter ───────────────────────────────────────────────────────────
import logging as _logging

class _PollFilter(_logging.Filter):
    def filter(self, record):
        msg = record.getMessage()
        if "/api/jobs/" in msg and "GET" in msg:
            return False
        return True

_logging.getLogger("uvicorn.access").addFilter(_PollFilter())

# ── FastAPI app ──────────────────────────────────────────────────────────────
app = FastAPI(title="EdGameClaw")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def _startup():
    _maybe_start_embedded_node()
    _prune_registry()
    if not API_KEY:
        print("[WARN] API_KEY not set. Add it to .env to enable generation.", flush=True)
    print(f"[EdGameClaw] Studio ready at http://localhost:{os.environ.get('PORT', 8000)}/", flush=True)

@app.on_event("shutdown")
async def _shutdown():
    global _ai_client
    _stop_embedded_node()
    if _ai_client:
        try: await _ai_client.aclose()
        except Exception: pass
        _ai_client = None


# -- Created by Yuqi Hang (github.com/yh2072) --
# ── Job Manager ──────────────────────────────────────────────────────────────
_STEP_PATTERNS = [
    (re.compile(r'\[Game (\d+)/(\d+)\].*Generating:\s*(.+?)(?:\s*\(theme:.*\))?$'), 'game'),
    (re.compile(r'\[(\d+)/(\d+)\]\s*(.+?)(?:\s*\(theme:.*\))?\.\.\.'), 'substep'),
    (re.compile(r'Course generation complete in ([\d.]+)s'), 'course_complete'),
    (re.compile(r'Games:\s*(\d+)/(\d+)\s*successful'), 'games_summary'),
    (re.compile(r'✅'), 'done'),
    (re.compile(r'❌'), 'error'),
]

def _to_safe_log(line: str) -> str | None:
    for pat, kind in _STEP_PATTERNS:
        m = pat.search(line)
        if not m:
            continue
        if kind == 'game':
            return json.dumps({"type": "game", "current": int(m.group(1)), "total": int(m.group(2)), "title": m.group(3).strip()})
        if kind == 'substep':
            cur, tot = int(m.group(1)), int(m.group(2))
            pct = int((cur / tot) * 100) if tot > 0 else 0
            return json.dumps({"type": "substep", "current": cur, "total": tot, "label": m.group(3).strip(), "pct": pct})
        if kind == 'course_complete':
            return json.dumps({"type": "info", "label": "course_complete", "value": f"{m.group(1)}s"})
        if kind == 'games_summary':
            return json.dumps({"type": "info", "label": "games_summary", "value": f"{m.group(1)}/{m.group(2)} successful"})
        if kind == 'done':
            return json.dumps({"type": "done"})
        if kind == 'error':
            return json.dumps({"type": "error", "msg": line})
        return None
    if '[ERROR]' in line or '[SIM FALLBACK]' in line:
        return json.dumps({"type": "error", "msg": line.strip()})
    if 'Game ' in line and ' done in ' in line:
        m2 = re.search(r'Game (\d+) done in ([\d.]+)s', line)
        if m2:
            return json.dumps({"type": "game_done", "game": int(m2.group(1)), "time": float(m2.group(2))})
    return None


class JobManager:
    def __init__(self):
        self.jobs: dict[str, dict] = {}

    def _path(self, jid: str) -> Path:
        return JOBS_DIR / f"{jid}.json"

    def _save(self, jid: str) -> None:
        try:
            job = self.jobs[jid]
            snapshot = {k: v for k, v in job.items() if k != "logs"}
            self._path(jid).write_text(json.dumps(snapshot), encoding="utf-8")
        except Exception:
            pass

    def _load(self, jid: str) -> dict | None:
        try:
            p = self._path(jid)
            if not p.exists():
                return None
            data = json.loads(p.read_text(encoding="utf-8"))
            data.setdefault("logs", [])
            self.jobs[jid] = data
            return data
        except Exception:
            return None

    def create(self, course_id: str) -> str:
        jid = uuid.uuid4().hex[:10]
        self.jobs[jid] = {
            "id": jid, "course_id": course_id, "status": "running",
            "logs": [], "result": None, "error": None, "created_at": time.time(),
        }
        self._save(jid)
        return jid

    def log(self, jid: str, msg: str):
        if jid in self.jobs and msg.strip():
            self.jobs[jid]["logs"].append({"t": time.time(), "msg": msg.strip()})

    def done(self, jid: str, result=None, error=None):
        if jid in self.jobs:
            self.jobs[jid].update({
                "status": "failed" if error else "completed",
                "result": result, "error": str(error) if error else None,
            })
            self._save(jid)

    def get(self, jid: str) -> dict | None:
        if jid in self.jobs:
            return self.jobs[jid]
        return self._load(jid)


job_mgr = JobManager()
_current_job_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar("current_job_id", default=None)
_REAL_STDERR = sys.__stderr__


class StderrDispatcher(io.TextIOBase):
    def __init__(self, mgr: JobManager, real_stderr):
        self._mgr = mgr
        self._real = real_stderr
        self._buffers: dict[str, str] = {}

    def write(self, s: str):
        jid = _current_job_id_ctx.get()
        if jid and jid in self._mgr.jobs:
            self._buffers.setdefault(jid, "")
            self._buffers[jid] += s
            while "\n" in self._buffers[jid]:
                line, self._buffers[jid] = self._buffers[jid].split("\n", 1)
                cleaned = line.strip()
                if not cleaned or cleaned.startswith('='):
                    continue
                safe = _to_safe_log(cleaned)
                if safe:
                    self._mgr.log(jid, safe)
        prefix = f"[{jid}] " if jid else ""
        lines = s.split("\n")
        for i, line in enumerate(lines):
            if i < len(lines) - 1:
                self._real.write(prefix + line + "\n")
            elif line:
                self._real.write(prefix + line)
        self._real.flush()
        return len(s)

    def flush(self):
        jid = _current_job_id_ctx.get()
        if jid and self._buffers.get(jid, "").strip():
            buf = self._buffers[jid].strip()
            self._buffers[jid] = ""
            safe = _to_safe_log(buf)
            if safe:
                self._mgr.log(jid, safe)
        self._real.flush()


sys.stderr = StderrDispatcher(job_mgr, _REAL_STDERR)


# ── Safety helpers ───────────────────────────────────────────────────────────
def _safe_course_id(s: str) -> str:
    if not s or ".." in s or "/" in s or "\\" in s:
        raise HTTPException(400, "Invalid course_id")
    if not re.match(r"^[a-zA-Z0-9_.-]+$", s):
        raise HTTPException(400, "Invalid course_id")
    return s

def _safe_chunk_id(s: str) -> str:
    if not s or ".." in s or "/" in s or "\\" in s:
        raise HTTPException(400, "Invalid chunk_id")
    if not re.match(r"^[a-zA-Z0-9_.-]+$", s):
        raise HTTPException(400, "Invalid chunk_id")
    return s


# ── Registry (courses.json) ─────────────────────────────────────────────────
def _read_registry() -> list[dict]:
    if REGISTRY.exists():
        try: return json.loads(REGISTRY.read_text(encoding="utf-8"))
        except: pass
    return []

def _write_registry(courses: list[dict]):
    REGISTRY.write_text(json.dumps(courses, ensure_ascii=False, indent=2), encoding="utf-8")

def _upsert_course(entry: dict):
    courses = _read_registry()
    idx = next((i for i, c in enumerate(courses) if c["id"] == entry["id"]), None)
    if idx is not None:
        courses[idx] = entry
    else:
        courses.insert(0, entry)
    _write_registry(courses)

def _remove_course(course_id: str):
    courses = [c for c in _read_registry() if c["id"] != course_id]
    _write_registry(courses)

def _prune_registry():
    courses = _read_registry()
    kept = [c for c in courses if (COURSES_DIR / c.get("id", "")).is_dir()]
    if len(kept) < len(courses):
        _write_registry(kept)

def _course_entry_from_manifest(course_id: str, manifest: dict) -> dict:
    meta = manifest.get("course", {})
    games = manifest.get("games", [])
    return {
        "id": course_id,
        "title": meta.get("title", course_id),
        "subtitle": meta.get("subtitle", ""),
        "description": meta.get("description", ""),
        "subject": meta.get("subject", ""),
        "level": meta.get("level", ""),
        "estimated_time": meta.get("estimated_time", ""),
        "learning_objectives": meta.get("learning_objectives", []),
        "total_lessons": len([g for g in games if g.get("status") == "success"]),
        "created_at": manifest.get("generated_at", ""),
        "tags": meta.get("tags", []),
    }

def scan_courses() -> list[dict]:
    _prune_registry()
    courses = _read_registry()
    if courses:
        return courses
    # Fallback: scan manifest files
    result = []
    if not COURSES_DIR.exists():
        return result
    for d in sorted(COURSES_DIR.iterdir(), reverse=True):
        if not d.is_dir(): continue
        mp = d / "course-manifest.json"
        if not mp.exists(): continue
        try:
            m = json.loads(mp.read_text(encoding="utf-8"))
            result.append(_course_entry_from_manifest(d.name, m))
        except: pass
    return result


# ── Markdown parser ─────────────────────────────────────────────────────────
def parse_markdown(md: str) -> dict:
    lines = md.splitlines()
    course = {
        "title": "", "subtitle": "", "description": "", "subject": "",
        "level": "", "estimated_time": "", "learning_objectives": [], "tags": [],
    }
    chunks, current = [], None
    in_desc = False

    def flush():
        nonlocal current
        if current:
            current["content"] = current["content"].strip()
            chunks.append(current)
            current = None

    for line in lines:
        raw = line.rstrip()
        if re.match(r'^# [^#]', raw):
            flush(); course["title"] = raw[2:].strip(); in_desc = True
        elif re.match(r'^## [^#]', raw):
            flush(); in_desc = False
            current = {
                "id": f"chunk-{len(chunks)+1}", "title": raw[3:].strip(),
                "subtitle": "", "theme": THEMES[len(chunks) % len(THEMES)],
                "learning_objectives": [], "content": "",
            }
        elif re.match(r'^### ', raw):
            title = raw[4:].strip()
            if current:
                if not current["subtitle"]: current["subtitle"] = title
                if current["content"]: current["content"] += "\n\n"
                current["content"] += f"**{title}**"
        elif re.match(r'^[-*] ', raw):
            item = raw[2:].strip()
            if current: current["content"] += f"\n• {item}"
            elif in_desc: course["learning_objectives"].append(item)
        elif not raw.strip():
            if current and current["content"] and not current["content"].endswith("\n\n"):
                current["content"] += "\n"
        else:
            if current:
                if current["content"] and not current["content"].endswith("\n"): current["content"] += "\n"
                current["content"] += raw
            elif in_desc and course["title"]:
                course["description"] = (course["description"] + " " + raw.strip()).strip()

    flush()
    if not course["subtitle"] and chunks:
        course["subtitle"] = " · ".join(c["title"] for c in chunks[:3])
        if len(chunks) > 3: course["subtitle"] += " ..."
    return {"course": course, "chunks": chunks}


# ── AI client (shared, persistent) ──────────────────────────────────────────
import socket
_orig_getaddrinfo = socket.getaddrinfo
_dns_cache: dict[tuple, list] = {}

def _cached_getaddrinfo(*args, **kwargs):
    key = args[:2]
    if key in _dns_cache:
        return _dns_cache[key]
    result = _orig_getaddrinfo(*args, **kwargs)
    if result:
        _dns_cache[key] = result
    return result

socket.getaddrinfo = _cached_getaddrinfo

_ai_client: httpx.AsyncClient | None = None

def _get_ai_client() -> httpx.AsyncClient:
    global _ai_client
    if _ai_client is None:
        _ai_client = httpx.AsyncClient(
            timeout=180, trust_env=False, http2=False,
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )
    return _ai_client


# -- Created by Yuqi Hang (github.com/yh2072) --
# ── Generation background task ───────────────────────────────────────────────
async def _run_generation(
    jid: str, content: dict, locale: str = "en",
    api_key: str | None = None, base_url: str | None = None, model: str | None = None,
):
    old_err = _REAL_STDERR
    course_id = job_mgr.get(jid)["course_id"]
    out_dir = COURSES_DIR / course_id
    _current_job_id_ctx.set(jid)

    def _register_course():
        mp = out_dir / "course-manifest.json"
        if not mp.exists():
            return
        try:
            manifest = json.loads(mp.read_text(encoding="utf-8"))
            entry = _course_entry_from_manifest(course_id, manifest)
            _upsert_course(entry)
        except Exception as exc:
            print(f"  [WARN] Failed to register course: {exc}", file=old_err)

    def _rlog(msg: str):
        print(f"[{course_id}] {msg}", file=old_err, flush=True)
        job_mgr.log(jid, json.dumps({"type": "info", "label": "status", "value": msg}))

    try:
        from .generator import api as gen_api
        from .generator.course_pipeline import generate_course_with_platform

        gen_api._studio_usage_collector_ctx.set([])
        out_dir.mkdir(parents=True, exist_ok=True)

        content_path = out_dir / "_content.json"
        content_path.write_text(json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8")

        ASSETS_DIR.mkdir(parents=True, exist_ok=True)
        num_chunks = len(content.get("chunks", []))
        _rlog(f"Generating {num_chunks} game(s)…")

        await generate_course_with_platform(
            str(content_path), str(out_dir),
            audio_base=str(AUDIO_DIR),
            locale=locale,
            api_key=api_key, base_url=base_url, model=model,
        )

        _rlog("Pipeline complete, registering course…")
        _register_course()
        job_mgr.done(jid, result={"course_id": course_id})
        _rlog("✅ Done! Open the Studio to play your course.")

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"[{course_id}] ❌ FAILED: {e}\n{tb}", file=old_err, flush=True)
        _register_course()
        job_mgr.done(jid, error=str(e))
        job_mgr.log(jid, f"❌ Failed: {e}")
    finally:
        _current_job_id_ctx.set(None)


# ══════════════════════════════════════════════════════════════════════════════
# API Routes
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
async def index():
    p = STATIC_DIR / "index.html"
    if p.exists():
        return HTMLResponse(p.read_text(encoding="utf-8"))
    return HTMLResponse("<meta http-equiv='refresh' content='0;url=/studio'>")

@app.get("/studio", response_class=HTMLResponse)
@app.get("/studio/", response_class=HTMLResponse)
async def studio():
    p = STATIC_DIR / "studio.html"
    if p.exists():
        return HTMLResponse(p.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Studio not found</h1>", 404)

@app.get("/play", response_class=HTMLResponse)
@app.get("/play/", response_class=HTMLResponse)
async def play_page():
    player_path = ENGINE_DIR / "player.html"
    if not player_path.exists():
        raise HTTPException(404, "Player not found")
    return HTMLResponse(player_path.read_text(encoding="utf-8"))


# -- Created by Yuqi Hang (github.com/yh2072) --
# ── Courses API ──────────────────────────────────────────────────────────────

@app.get("/api/courses")
async def list_courses():
    return scan_courses()

@app.get("/courses.json")
async def courses_json():
    return JSONResponse(content=scan_courses())

@app.get("/api/courses/{course_id}/manifest")
async def get_manifest(course_id: str):
    course_id = _safe_course_id(course_id)
    mp = COURSES_DIR / course_id / "course-manifest.json"
    if mp.exists():
        try:
            return json.loads(mp.read_text(encoding="utf-8"))
        except Exception as e:
            raise HTTPException(500, f"Invalid manifest: {e}")
    raise HTTPException(404, "Course manifest not found")

@app.delete("/api/courses/{course_id}")
async def delete_course(course_id: str):
    course_id = _safe_course_id(course_id)
    course_dir = COURSES_DIR / course_id
    if not course_dir.exists():
        raise HTTPException(404, "Course not found")
    shutil.rmtree(course_dir)
    _remove_course(course_id)
    return {"ok": True}


# ── Parse markdown ───────────────────────────────────────────────────────────

@app.post("/api/parse-md-text")
async def parse_md_text(body: dict):
    md = body.get("markdown", "")
    if not md.strip():
        raise HTTPException(400, "Empty markdown")
    return parse_markdown(md)


# -- Created by Yuqi Hang (github.com/yh2072) --
# ── Generate course ──────────────────────────────────────────────────────────

@app.post("/api/generate")
async def generate(body: dict):
    content = body.get("content", {})
    locale = body.get("locale", "en")
    if locale not in ALLOWED_LOCALES:
        locale = "en"

    # API key: from body (BYOK) or server env
    api_key = body.get("api_key") or API_KEY
    base_url = body.get("base_url") or API_BASE_URL
    model = body.get("model") or MODEL

    if not api_key:
        raise HTTPException(400, "api_key is required. Set API_KEY in .env or pass api_key in request body.")
    if not content.get("chunks"):
        raise HTTPException(400, "No chunks provided. Parse your content first.")
    if not content.get("course", {}).get("title"):
        raise HTTPException(400, "Course title required")

    course_id = _safe_course_id(body.get("course_id") or f"course-{int(time.time())}")
    resumed = (COURSES_DIR / course_id / "games").exists()
    jid = job_mgr.create(course_id)
    status_msg = "Resuming (cached steps reused)..." if resumed else "Starting generation..."
    job_mgr.log(jid, json.dumps({"type": "info", "label": "status", "value": status_msg}))

    asyncio.create_task(_run_generation(
        jid, content, locale=locale,
        api_key=api_key, base_url=base_url, model=model,
    ))
    return {"job_id": jid, "course_id": course_id}


# ── Jobs ─────────────────────────────────────────────────────────────────────

@app.get("/api/jobs/{jid}")
async def get_job(jid: str):
    j = job_mgr.get(jid)
    if not j:
        raise HTTPException(404, "Job not found")
    return j


# ── AI chat proxy (BYOK) ─────────────────────────────────────────────────────

@app.post("/api/ai-chat")
async def ai_chat(body: dict):
    api_key = body.get("api_key") or API_KEY
    base_url = body.get("base_url") or API_BASE_URL
    model = body.get("model") or MODEL
    messages = body.get("messages", [])
    max_tokens = body.get("max_tokens", 1024)

    if not api_key:
        raise HTTPException(400, "api_key is required")
    if not messages:
        raise HTTPException(400, "messages are required")

    client = _get_ai_client()
    url = base_url.rstrip("/") + "/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": messages, "temperature": 0.7, "max_tokens": max_tokens}

    try:
        resp = await client.post(url, json=payload, headers=headers)
        if resp.status_code != 200:
            raise HTTPException(resp.status_code, f"AI API error: {resp.text[:500]}")
        data = resp.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return {"content": content}
    except httpx.ConnectError as e:
        _dns_cache.clear()
        raise HTTPException(502, f"Cannot connect to AI provider: {e}")
    except httpx.TimeoutException:
        raise HTTPException(504, "AI request timed out. Try again.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"AI request error: {type(e).__name__}: {e}")


# -- Created by Yuqi Hang (github.com/yh2072) --
# ── Game player ──────────────────────────────────────────────────────────────

@app.get("/api/play/{course_id}/{chunk_id}/package")
async def get_game_package(course_id: str, chunk_id: str):
    course_id = _safe_course_id(course_id)
    chunk_id = _safe_chunk_id(chunk_id)

    game_dir = COURSES_DIR / course_id / "games" / chunk_id
    if not game_dir.exists():
        raise HTTPException(404, "Game not found")

    json_path = game_dir / "game.pkg.json"
    if not json_path.exists():
        raise HTTPException(404, "Game package not found. Try regenerating the course.")

    try:
        pkg = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise HTTPException(500, f"Invalid package: {e}")

    if "config" not in pkg:
        pkg["config"] = {}
    pkg["config"]["courseId"] = course_id
    pkg["config"]["chunkId"] = chunk_id

    # Inject next game URL
    games_dir = game_dir.parent
    if games_dir.is_dir():
        siblings = sorted(p.name for p in games_dir.iterdir() if p.is_dir())
        try:
            idx = siblings.index(chunk_id)
            if idx + 1 < len(siblings):
                next_chunk = siblings[idx + 1]
                pkg["config"]["nextGameUrl"] = f"/play?course={course_id}&game={next_chunk}"
        except ValueError:
            pass

    return pkg

@app.post("/api/play/{course_id}/{chunk_id}/state")
async def play_state_proxy(request: Request, course_id: str, chunk_id: str):
    course_id = _safe_course_id(course_id)
    chunk_id = _safe_chunk_id(chunk_id)
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, "Invalid JSON")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(f"{ENGINE_STATE_URL}/state", json=body)
        return JSONResponse(
            status_code=r.status_code,
            content=r.json() if r.headers.get("content-type", "").startswith("application/json") else {"error": r.text},
        )
    except httpx.ConnectError:
        raise HTTPException(503, "Engine state service unavailable (start with: cd node && node server.js)")
    except Exception as e:
        raise HTTPException(502, str(e))

@app.post("/api/play/{course_id}/{chunk_id}/next")
async def play_next_proxy(request: Request, course_id: str, chunk_id: str):
    course_id = _safe_course_id(course_id)
    chunk_id = _safe_chunk_id(chunk_id)
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, "Invalid JSON")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(f"{ENGINE_STATE_URL}/next", json=body)
        return JSONResponse(
            status_code=r.status_code,
            content=r.json() if r.headers.get("content-type", "").startswith("application/json") else {"error": r.text},
        )
    except httpx.ConnectError:
        raise HTTPException(503, "Engine state service unavailable")
    except Exception as e:
        raise HTTPException(502, str(e))


# ── Config info endpoint ──────────────────────────────────────────────────────
@app.get("/api/config")
async def get_config():
    """Return public config info (no secrets)."""
    return {
        "has_api_key": bool(API_KEY),
        "model": MODEL,
        "base_url": API_BASE_URL,
    }


# ── Static file mounts ────────────────────────────────────────────────────────
if ENGINE_DIR.exists():
    app.mount("/engine", StaticFiles(directory=str(ENGINE_DIR)), name="engine")

if COURSES_DIR.exists():
    app.mount("/courses", StaticFiles(directory=str(COURSES_DIR), html=True), name="courses")

if ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

readme_dir = PACKAGE_DIR / "readme"
if readme_dir.exists():
    app.mount("/readme", StaticFiles(directory=str(readme_dir)), name="readme")
