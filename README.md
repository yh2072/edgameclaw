<p align="center">
  <img src="readme/edgameclaw_logo.png" alt="EdGameClaw" width="160">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/License-AGPL--3.0-orange?style=for-the-badge" alt="License AGPL-3.0" />
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/LLM-OpenAI%20compatible-412991?style=for-the-badge" alt="OpenAI-compatible LLM" />
  <img src="https://img.shields.io/badge/Self--hosted-✓-success?style=for-the-badge" alt="Self-hosted" />
</p>

<p align="center">
  <b>🌐 Language / 语言</b><br />
  <a href="README.md"><img src="https://img.shields.io/badge/English-README-2ea44f?style=for-the-badge" alt="English README" /></a>
  <a href="README_CN.md"><img src="https://img.shields.io/badge/简体中文-README-555?style=for-the-badge" alt="简体中文 README" /></a>
</p>

<p align="center">
  <a href="https://ahafrog.com"><strong>🌐 ahafrog.com</strong></a> &nbsp;·&nbsp;
  <a href="https://github.com/yh2072/edgameclaw">⭐ GitHub</a> &nbsp;·&nbsp;
  <a href="https://openrouter.ai"><strong>🔌 OpenRouter</strong></a> &nbsp;·&nbsp;
  <a href="#citation">📖 Citation</a> &nbsp;·&nbsp;
  <a href="#quick-start">🚀 Quick Start</a>
</p>

---

# EdGameClaw — AI Game-Based Learning Studio

> **Turn any learning material into playable mini-games — in minutes.**

EdGameClaw is a self-hosted, open-source tool that uses AI to convert your notes, textbooks, or any structured content into interactive game-based micro-courses. Each concept gets the mini-game mechanic it deserves.

**No database. No login. No cloud required. Just clone, configure, and play.**

---

## 🏆 What Makes EdGameClaw Different

Most AI learning tools generate slides, lecture transcripts, or talking-head videos. EdGameClaw does something fundamentally different: it turns knowledge into **games you actually play**.

| | AI Slide / Lecture Tools | EdGameClaw |
|---|---|---|
| Output format | Slides, video, text | **Playable browser game** |
| Learning mode | Passive watching / reading | **Active play — score, fail, retry** |
| Visual identity | Generic templates | **AI-generated pixel art per lesson** |
| Game mechanics | None | **Mechanic matched to each concept** |
| Hosting | Cloud SaaS | **Fully self-hosted, runs offline** |
| LLM provider | Locked in | **Any OpenAI-compatible API (BYOK)** |
| Open source | Closed / partial | **Fully open, fork and extend** |

### 🎮 Real Games, Not Decorated Slides

Other tools dress up slides with animations or add a chat window to a video. EdGameClaw runs a **custom pixel-art game engine** in the browser. Learners experience progression bars, scoring, character dialog, animations, and game-over states. The mechanic is designed per concept — a sorting puzzle for taxonomy, a dialog simulation for argument analysis, a timed challenge for recall — not the same quiz widget applied to everything.

### 🖼️ AI-Generated Pixel Art, Every Time

Every lesson gets its own visual world: AI-generated characters, backgrounds, and icons — not stock photos or clip art. 24 built-in themes (from *china-ink* to *sci-fi* to *baroque*) give each course a distinct aesthetic. No two games look the same.

### 🔀 Mechanic-to-Concept Matching

The pipeline doesn't just "generate a quiz about X." It analyzes the concept and assigns the game mechanic that best reinforces it — spatial reasoning gets a placement game, causal chains get a sequencing challenge, vocabulary gets a match-and-eliminate mechanic. This is the core insight EdGameClaw is built on.

### 🔒 Zero Lock-in — Yours to Own

No accounts. No cloud uploads. No subscription. All generated courses live on your machine as plain files. Swap your LLM provider in one env variable. Fork the engine. The content you generate is entirely yours.

---

## 🎬 How It Works

<p align="center">
  <a href="https://github.com/yh2072/edgameclaw/issues/1#issuecomment-4059754684"><img src="https://img.shields.io/badge/▶_Watch-demo-on-GitHub-24292f?style=for-the-badge&logo=github&logoColor=white" alt="Watch demo" /></a>
</p>

Paste your content → AI generates a full game-based course → Play instantly in your browser.

---

## 🎮 Case Study — One Sentence. One Game.

Each game below was generated from **a single sentence or short paragraph**. No manual design. No coding.

<table>
<tr>
<td align="center" width="25%">

**A World in a Square Inch**

![方寸乾坤](readme/方寸乾坤.gif)

</td>
<td align="center" width="25%">

**global vs. local debate in neuroscience**

![神经科学全局局部辩论](readme/神经科学全局局部辩论.gif)

</td>
<td align="center" width="25%">

**basic economics principles**

![经济学原理](readme/经济学原理.gif)

</td>
<td align="center" width="25%">

**Convolutional Neural Networks**

![CNN](readme/cnn.gif)

</td>
</tr>
</table>

> Philosophy, neuroscience, economics, deep learning — EdGameClaw adapts its game mechanics to each subject automatically.

---

## 📋 Generated Course Syllabus

EdGameClaw doesn't just create games — it first generates a structured course syllabus, then maps each chapter to the right game mechanic.

![Course Syllabus — Attention & Residuals](readme/case%20study-%20course%20syllabus-attention%20residuals.png)

---

## 🚀 Quick Start {#quick-start}

### Option 1: Python (Recommended)

**Prerequisites:** Python 3.10+, Node.js 18+

```bash
# 1. Clone the repo
git clone https://github.com/yh2072/edgameclaw
cd edgameclaw

# 2. Create a virtual environment (pick one)
python -m venv .venv && source .venv/bin/activate  # venv (built-in)
# conda create -n edgameclaw python=3.11 && conda activate edgameclaw  # conda

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Configure your API key
cp .env.example .env
# Edit .env and add your API_KEY

# 5. Start the server
 bash start.sh 
# Or: uvicorn server:app --reload
```

Open **http://localhost:8000** → Studio is ready!

### Option 2: Docker

```bash
docker run -p 8000:8000 -e API_KEY=sk-your-key ghcr.io/YOUR_USERNAME/edgameclaw
```

---

## ⚙️ Configuration

Copy `.env.example` to `.env` and set your values:

| Variable | Required | Description |
|----------|----------|-------------|
| `API_KEY` | Yes* | Your OpenAI-compatible API key |
| `MODEL` | No | Model name (default: `google/gemini-3-flash-preview`) |
| `API_BASE_URL` | No | API endpoint (default: OpenRouter) |
| `PORT` | No | Server port (default: `8000`) |
| `BIND_HOST` | No | Bind address (default: `127.0.0.1`) |

*You can also enter your API key directly in the Studio UI — it's stored only in your browser.

### Recommended AI Providers

**Default stack:** [**OpenRouter**](https://openrouter.ai) (`API_BASE_URL=https://openrouter.ai/api/v1`) — one key, [many models](https://openrouter.ai/models), pay-as-you-go.

**Recommended model:** `google/gemini-3-flash-preview` via OpenRouter — fast and cost-effective.

---

## ⚡ How the Pipeline Works

1. **Paste** your learning content in Markdown format
2. **Parse** — EdGameClaw extracts course structure (title, chapters)
3. **Syllabus** — AI generates a structured learning plan with game mechanics mapped to each chapter
4. **Generate** — AI pipeline creates custom mini-games for each chapter:
5. **Play** — Games open instantly in your browser

---

## 📁 Project Structure

```
edgameclaw/
├── server.py           # FastAPI server
├── generator/          # AI course generation pipeline
│   ├── pipeline.py     # Main orchestration
│   ├── api.py          # LLM API client
│   ├── prompts.py      # Prompt templates
│   ├── assembler.py    # Course assembly & theming
│   └── ...
├── engine/             # Game engine
│   ├── engine.js       # Game state machine
│   ├── player.html     # Browser game player
│   └── minigames/      # Mini-game implementations
├── node/               # Node.js engine state server
├── static/             # Frontend
│   ├── index.html      # Landing page
│   └── studio.html     # Studio app
├── courses/            # Generated courses (local storage)
├── .env.example        # Configuration template
├── requirements.txt    # Python dependencies
└── start.sh            # Quick start script
```

---

## 🌍 Supported Languages

Generate courses in: **English, Chinese (中文), Japanese (日本語), Spanish (Español), French (Français), Korean (한국어), Arabic (العربية), German (Deutsch)**

---

## 🎨 Visual Themes

24 built-in themes:
- **Cute/Modern:** pink-cute, ocean-dream, forest-sage, candy-pop, galaxy-purple
- **Chinese:** china-porcelain, china-cinnabar, dunhuang, forbidden-red, china-landscape
- **Historical:** renaissance, baroque, nordic, victorian, mediterranean
- **Fantasy/Genre:** fairy-tale, detective, sci-fi, academy, myth


---

## 📜 License

This project is open source under the **AGPL-3.0** license. See [LICENSE-AGPL-3.0](./LICENSE-AGPL-3.0) for the full text. For commercial licensing, contact: [yh2072@nyu.edu](mailto:yh2072@nyu.edu).

---

## 🌟 Production Use

**[ahafrog](https://ahafrog.com)** is the hosted, full-featured SaaS platform built on top of EdGameClaw — with user accounts, social features, leaderboards, and a managed infrastructure. Try it if you want the full experience without self-hosting.

### 🤝 Share Your Courses with the World

Built something great with EdGameClaw? **Publish it on [ahafrog.com](https://ahafrog.com) and share it with learners everywhere.** Your course will appear in the public course library — free to play for anyone. Physics, math, history, coding, languages — every great course deserves a wider audience. Come contribute.

---

## 📖 Citation {#citation}

If you use EdGameClaw in research or a project, please cite:

```bibtex
@software{hang2026edgameclaw,
  author    = {Hang, Yuqi},
  title     = {EdGameClaw: AI Game-Based Learning Studio},
  year      = {2026},
  url       = {https://github.com/yh2072/edgameclaw},
  note      = {Open-source AI pipeline for converting learning content into interactive mini-games}
}
```

---

## 👤 Author

**Yuqi Hang** — PhD Student @ New York University

Built EdGameClaw as an open-source foundation for AI-powered game-based learning. Research interests include AI for educational games, human-computer interaction, neuroaesthetics and educational neuroscience.

- GitHub: [@yh2072](https://github.com/yh2072)
- Website: [yuqihang.net](https://yuqihang.net)
- Project: [ahafrog.com](https://ahafrog.com)

---

⭐ **If this project is useful to you, please star it on GitHub!** It helps more people discover it.
