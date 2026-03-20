# EdGameClaw

**Turn learning materials into playable browser mini-games** — self-hosted, OpenAI-compatible API, no account required.

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-orange)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

**Full documentation, demo video, screenshots, and bilingual (English / 中文) guide:**  
**https://github.com/yh2072/edgameclaw#readme**

**Hosted product:** [ahafrog.com](https://ahafrog.com)

---

## Install

Requires **Python 3.10+** and **Node.js 18+** (`node` on your `PATH`).

```bash
pip install edgameclaw
```

Create `.env` in the directory where you run the server (or export env vars):

```env
API_KEY=sk-your-openai-compatible-key
```

Start the app:

```bash
uvicorn edgameclaw.server:app --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000** in your browser.

A small bundled **Node** service (for playing games) starts on port **3100** when that port is free. Set `EDGAMECLAW_ENGINE_STATE_AUTO=0` if you run it yourself.

**From source:** `git clone https://github.com/yh2072/edgameclaw` → `pip install -e .` → see GitHub README for `start.sh` and `.env.example`.

---

## Configuration (common)

| Variable | Notes |
|----------|--------|
| `API_KEY` | Required for generation (or paste in Studio UI only — browser-local). |
| `API_BASE_URL` | Default: OpenRouter. |
| `MODEL` | Default: `google/gemini-3-flash-preview`. |
| `EDGAMECLAW_HOME` | Optional: where to store courses and data (default: current working directory when installed via pip). |

---

## Links

- **Source & full README:** https://github.com/yh2072/edgameclaw  
- **License:** AGPL-3.0 — see `LICENSE-AGPL-3.0` in the repository  
- **Citation / author:** see GitHub README  
