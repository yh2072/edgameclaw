<p align="center">
  <img src="edgameclaw/readme/edgameclaw_logo.png" alt="EdGameClaw" width="160">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/License-AGPL--3.0-orange?style=for-the-badge" alt="AGPL-3.0" />
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/LLM-OpenAI%20compatible-412991?style=for-the-badge" alt="LLM" />
  <img src="https://img.shields.io/badge/Self--hosted-✓-success?style=for-the-badge" alt="Self-hosted" />
  <a href="https://pypi.org/project/edgameclaw/"><img src="https://img.shields.io/pypi/v/edgameclaw.svg?style=for-the-badge&amp;label=PyPI" alt="PyPI version" /></a>
  <a href="https://discord.gg/wesebXsxHV"><img src="https://img.shields.io/badge/Discord-Community-5865F2?style=for-the-badge&amp;logo=discord&amp;logoColor=white" alt="Discord" /></a>
</p>

<p align="center">
  <a href="#english"><strong>English</strong></a> &nbsp;·&nbsp;
  <a href="#简体中文"><strong>简体中文</strong></a> &nbsp;·&nbsp;
  <a href="#quick-start-zh">快速开始</a><br />
  <a href="https://ahafrog.com"><strong>ahafrog.com</strong></a> &nbsp;·&nbsp;
  <a href="https://github.com/yh2072/edgameclaw">GitHub</a> &nbsp;·&nbsp;
  <a href="https://pypi.org/project/edgameclaw/"><strong>PyPI</strong></a> &nbsp;·&nbsp;
  <a href="https://discord.gg/wesebXsxHV"><strong>Discord</strong></a> &nbsp;·&nbsp;
  <a href="https://openrouter.ai"><strong>OpenRouter</strong></a> &nbsp;·&nbsp;
  <a href="#citation">Citation</a> &nbsp;·&nbsp;
  <a href="#quick-start">Quick Start</a>
</p>

---

<a id="english"></a>

# EdGameClaw — AI Game-Based Learning Studio

> **Turn any learning material into playable mini-games — in minutes.**

<p align="center">
  <a href="https://www.producthunt.com/products/edgameclaw?embed=true&amp;utm_source=badge-featured&amp;utm_medium=badge&amp;utm_campaign=badge-edgameclaw" target="_blank" rel="noopener noreferrer">
    <img alt="edgameclaw - Convert any learning material into a game-based course | Product Hunt" width="250" height="54" src="https://api.producthunt.com/widgets/embed-image/v1/featured.svg?post_id=1103079&amp;theme=light&amp;t=1774003206790">
  </a>
</p>

**What is this?** A small **self-hosted** app on your computer: paste notes or a textbook chapter, and AI turns them into **playable browser games** (pixel art, scoring, different mechanics per topic). **No account.** **No vendor lock-in.** Your courses stay as files on your machine.

---

## 🚀 Start here {#quick-start}

**You need:** Python **3.10+**, **Node.js 18+**, and an **API key** for any [OpenAI-compatible](https://openrouter.ai) model.

**What you do:** install the package → add your key → run one server → open the Studio in a browser.

| I want to… | Do this |
|------------|---------|
| **Try it fast (PyPI)** | `pip install edgameclaw` → put `API_KEY` in `.env` or your shell → run `uvicorn edgameclaw.server:app --host 127.0.0.1 --port 8000` |
| **Hack on the source** | `git clone` the repo → `pip install -e .` → copy `.env.example` to `.env` → on macOS/Linux run `bash start.sh`, or run `uvicorn` on any OS (see below) |
| **Use Docker** | `docker run …` (see bottom of this section) |

Open **http://127.0.0.1:8000** — paste your material and click generate.

**Behind the scenes:** a tiny **Node** helper (for playing games) is **included in the package** and starts on port **3100** when that port is free. You only need `node` installed and on your `PATH`. To run Node yourself, set `EDGAMECLAW_ENGINE_STATE_AUTO=0`.

<details>
<summary><strong>Copy-paste commands</strong></summary>

**From PyPI**

```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate
pip install edgameclaw
# In the folder where you run uvicorn: create .env with API_KEY=...  (see Configuration)
uvicorn edgameclaw.server:app --host 127.0.0.1 --port 8000
```

**From source**

```bash
git clone https://github.com/yh2072/edgameclaw && cd edgameclaw
python -m venv .venv && source .venv/bin/activate   # or Windows: .venv\Scripts\activate
pip install -e .
cp .env.example .env   # add your API_KEY
bash start.sh          # macOS / Linux only
# Any OS:  uvicorn edgameclaw.server:app --host 127.0.0.1 --port 8000
```

**Docker**

```bash
docker run -p 8000:8000 -e API_KEY=sk-your-key ghcr.io/YOUR_USERNAME/edgameclaw
```

</details>

**Something wrong?** Install Node from [nodejs.org](https://nodejs.org) if you see a Node error. If port **8000** or **3100** is taken, close the other app or change `PORT` / `ENGINE_STATE_URL` in `.env`.

---

## 🎬 Watch a demo

<p align="center">
  <video
    controls
    playsinline
    preload="metadata"
    muted
    poster="edgameclaw/readme/edgameclaw_logo.png"
    src="https://github.com/user-attachments/assets/d5c19a93-6f8d-4ed2-855d-d57046bcf008"
    width="100%"
    style="max-width: 920px; border-radius: 12px;"
  >
    Your browser does not support the video tag.
  </video>
</p>

*Paste content → AI builds a game-based course → Play in the browser.*

---

## 🏆 Why EdGameClaw

Most “AI learning” tools give you slides or narrated videos. Here you get **real mini-games**: retries, scores, and a mechanic chosen to fit the topic — plus **AI-generated pixel art** and **24 themes**. Everything runs **on your machine** with **any OpenAI-compatible API** you like.

| | Typical AI course tools | EdGameClaw |
|---|---|---|
| Output | Slides, video, text | **Playable browser games** |
| Learning | Mostly passive | **Active — score, fail, retry** |
| Look | Generic templates | **Pixel art per lesson** |
| Mechanics | One quiz style | **Matched to each concept** |
| Host | Often cloud-only | **Self-hosted, offline-friendly, BYOK** |

---

## 🎮 Case Study — One Sentence. One Game.

Each game below was generated from **a single sentence or short paragraph**. No manual design. No coding.

**A World in a Square Inch**

![方寸乾坤](edgameclaw/readme/方寸乾坤.gif)

**global vs. local debate in neuroscience**

![神经科学全局局部辩论](edgameclaw/readme/神经科学全局局部辩论.gif)

**basic economics principles**

![经济学原理](edgameclaw/readme/经济学原理.gif)

**Convolutional Neural Networks**

![CNN](edgameclaw/readme/cnn.gif)

> Philosophy, neuroscience, economics, deep learning — EdGameClaw adapts its game mechanics to each subject automatically.

---

## 🧩 More Generated Mini-Games

![Generated Mini-Game Showcase](edgameclaw/readme/showcase.png)

---

## 📋 Generated Course Syllabus

EdGameClaw doesn't just create games — it first generates a structured course syllabus, then maps each chapter to the right game mechanic.

![Course Syllabus — Attention & Residuals](edgameclaw/readme/case%20study-%20course%20syllabus-attention%20residuals.png)

---

## ⚙️ Configuration

**Minimum to get going:** set **`API_KEY`** (or paste it only in the Studio UI — it stays in your browser).

Copy `.env.example` to `.env` when you run from a git clone, or create `.env` yourself in the folder where you start `uvicorn`:

| Setting | Required? | What it does |
|---------|-----------|--------------|
| `API_KEY` | Yes* | Your OpenAI-compatible API key |
| `MODEL` | No | Model name (default: `google/gemini-3-flash-preview`) |
| `API_BASE_URL` | No | API base URL (default: OpenRouter) |
| `PORT` | No | Web app port (default `8000`) |
| `BIND_HOST` | No | Listen address (default `127.0.0.1`) |
| `EDGAMECLAW_HOME` | No | Where to save `courses/`, `assets/`, `jobs/`, and `courses.json` (defaults: repo root when developing from git; **current folder** when installed from pip) |
| `EDGAMECLAW_ENGINE_STATE_AUTO` | No | `1` (default) = auto-start bundled Node on port 3100 if free. `0` = you run Node yourself. |
| `ENGINE_STATE_URL` | No | URL of the engine helper (default `http://127.0.0.1:3100`) — must match the Node port. |

\*Or enter the key **only in the Studio** (browser-only, not sent to our servers).

**Suggested provider:** [**OpenRouter**](https://openrouter.ai) — one key, [many models](https://openrouter.ai/models). Default model `google/gemini-3-flash-preview` is fast and cheap for testing.

---

## How generation works

1. Paste your content (Markdown).
2. EdGameClaw reads structure (title, chapters).
3. AI writes a **syllabus** and picks a **game mechanic** per chapter.
4. AI builds each **mini-game** (pixel art + logic).
5. You **play** in the browser — no extra export step.

---

## 📁 Project layout (for contributors)

```
edgameclaw/                    # repository root
├── pyproject.toml             # Python package metadata (pip install)
├── edgameclaw/                # importable package
│   ├── server.py              # FastAPI app
│   ├── generator/             # AI course generation pipeline
│   │   ├── pipeline.py
│   │   ├── api.py
│   │   └── ...
│   ├── engine/                # Game engine (JS + HTML)
│   ├── static/                # Landing + Studio UI
│   ├── readme/                # README assets (GIFs, screenshots)
│   └── node/                  # Engine-state server (bundled; auto-started by default)
├── courses/                   # Generated courses (local storage)
├── server.py                  # optional shim: re-exports `app` for `uvicorn server:app`
├── .env.example
├── requirements.txt           # usually: editable install (`-e .`)
└── start.sh
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

Built something great with EdGameClaw? **Publish it on [ahafrog.com](https://ahafrog.com) and share it with learners everywhere.** Your course will appear in the public course library — free to play for anyone.

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
- Community: [Discord — EdGameClaw](https://discord.gg/wesebXsxHV)

---

⭐ **If this project is useful to you, please star it on GitHub!**

---

<a id="简体中文"></a>

# 简体中文说明

> **将任何学习材料转化为可玩的小游戏 — 只需几分钟。**

**这是什么？** 装在你电脑上的**自托管**小工具：粘贴笔记或教材片段，AI 会生成**可在浏览器里玩的小游戏**（像素风、计分、每个知识点不同玩法）。**不用注册账号**，**不绑定某一家云**，课程以文件形式保存在本机。

---

## 🚀 从这里开始 {#quick-start-zh}

**需要准备：** Python **3.10+**、**Node.js 18+**、任意 [OpenAI 兼容](https://openrouter.ai) 的 **API 密钥**。

**你要做的：** 安装 → 填密钥 → 启动服务 → 浏览器里打开 Studio。

| 我想… | 怎么做 |
|--------|--------|
| **最快试用（PyPI）** | `pip install edgameclaw` → 配置 `API_KEY` → `uvicorn edgameclaw.server:app --host 127.0.0.1 --port 8000` |
| **改源码 / 用脚本启动** | `git clone` → `pip install -e .` → 复制 `.env` → macOS/Linux 可用 `bash start.sh`，或任意系统直接 `uvicorn` |
| **用 Docker** | 见下方折叠块 |

浏览器打开 **http://127.0.0.1:8000**，粘贴内容即可生成。

**说明：** 包里自带一个很小的 **Node** 辅助进程（玩游戏时用），默认在 **3100** 端口空闲时**自动启动**。本机装好 Node 并能在终端里运行 `node` 即可。想自己起 Node 时，设 `EDGAMECLAW_ENGINE_STATE_AUTO=0`。

<details>
<summary><strong>可复制命令</strong></summary>

**PyPI 安装**

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install edgameclaw
# 在运行 uvicorn 的目录创建 .env，写入 API_KEY=…
uvicorn edgameclaw.server:app --host 127.0.0.1 --port 8000
```

**源码安装**

```bash
git clone https://github.com/yh2072/edgameclaw && cd edgameclaw
python -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env
bash start.sh
# 任意系统也可: uvicorn edgameclaw.server:app --host 127.0.0.1 --port 8000
```

**Docker**

```bash
docker run -p 8000:8000 -e API_KEY=sk-your-key ghcr.io/YOUR_USERNAME/edgameclaw
```

</details>

**常见问题：** 提示找不到 Node → 到 [nodejs.org](https://nodejs.org) 安装 18+ 并重开终端。端口被占用 → 关掉占用程序，或改 `.env` 里的 `PORT` / `ENGINE_STATE_URL`。

---

## 🎬 演示视频

<p align="center">
  <video
    controls
    playsinline
    preload="metadata"
    muted
    poster="edgameclaw/readme/edgameclaw_logo.png"
    src="https://github.com/user-attachments/assets/d5c19a93-6f8d-4ed2-855d-d57046bcf008"
    width="100%"
    style="max-width: 920px; border-radius: 12px;"
  >
    您的浏览器不支持 video 标签。
  </video>
</p>

*粘贴内容 → AI 生成课程 → 浏览器里开玩。*

---

## 一句话看懂 EdGameClaw

多数「AI 学习」只会出幻灯片或配音视频。这里是**真正能玩的迷你游戏**：重试、得分、按知识点选机制，还有 **AI 像素画** 和 **24 套主题**。数据在你自己电脑上，**任意 OpenAI 兼容 API** 都能接。

| | 常见 AI 课工具 | EdGameClaw |
|---|---|---|
| 输出 | 幻灯片、视频、文字 | **浏览器里可玩的游戏** |
| 学习 | 偏被动 | **主动玩 — 得分、失败、重试** |
| 画面 | 模板感 | **每课独立像素风** |
| 机制 | 一种测验 | **按知识点换玩法** |
| 部署 | 常依赖云 | **自托管、可离线、自带密钥（BYOK）** |

---

## 🎮 案例展示 — 一句话，一个游戏

以下每个游戏都由**一句话或一小段文字**生成，无需手动设计，无需编程。

**方寸乾坤**

![方寸乾坤](edgameclaw/readme/方寸乾坤.gif)

**神经科学：全局 vs 局部**

![神经科学全局局部辩论](edgameclaw/readme/神经科学全局局部辩论.gif)

**经济学原理**

![经济学原理](edgameclaw/readme/经济学原理.gif)

**卷积神经网络**

![CNN](edgameclaw/readme/cnn.gif)

> 哲学、神经科学、经济学、深度学习 — EdGameClaw 会自动为每个学科匹配最合适的游戏机制。

---

## 🧩 更多生成小游戏展示

![更多生成小游戏展示](edgameclaw/readme/showcase.png)

---

## 📋 自动生成的课程大纲

EdGameClaw 不只是生成游戏 — 它会先生成结构化的课程大纲，再将每个章节映射到对应的游戏机制。

![课程大纲 — Attention & Residuals](edgameclaw/readme/case%20study-%20course%20syllabus-attention%20residuals.png)

---

## ⚙️ 配置说明

**最少要配：** **`API_KEY`**（或只在 Studio 网页里粘贴，密钥只留在浏览器）。

从 git 克隆时，把 `.env.example` 复制成 `.env`；只用 pip 时，在运行 `uvicorn` 的目录下自己建 `.env`：

| 变量 | 必填？ | 说明 |
|------|--------|------|
| `API_KEY` | 是* | OpenAI 兼容的 API 密钥 |
| `MODEL` | 否 | 模型名（默认 `google/gemini-3-flash-preview`） |
| `API_BASE_URL` | 否 | API 地址（默认 OpenRouter） |
| `PORT` | 否 | 网页端口（默认 `8000`） |
| `BIND_HOST` | 否 | 监听地址（默认 `127.0.0.1`） |
| `EDGAMECLAW_HOME` | 否 | 存放课程与数据的目录（git 开发时默认仓库根；pip 安装时默认**当前目录**） |
| `EDGAMECLAW_ENGINE_STATE_AUTO` | 否 | `1`（默认）= 3100 空闲时自动起内置 Node；`0` = 自己起 Node |
| `ENGINE_STATE_URL` | 否 | 引擎辅助服务地址（默认 `http://127.0.0.1:3100`） |

\*也可仅在 Studio 里输入密钥。

**推荐接入：** [**OpenRouter**](https://openrouter.ai) — 一把密钥，[多模型](https://openrouter.ai/models)。默认模型适合试玩。

---

## 生成流程（五步）

1. 粘贴 Markdown 内容  
2. 解析课程结构  
3. AI 写大纲并匹配每章游戏机制  
4. AI 生成各章小游戏  
5. 浏览器里直接玩  

---

## 📁 项目结构（给开发者）

```
edgameclaw/                    # 仓库根目录
├── pyproject.toml             # Python 包元数据（pip install）
├── edgameclaw/                # 可导入的包
│   ├── server.py              # FastAPI 应用
│   ├── generator/             # AI 课程生成流水线
│   ├── engine/                # 游戏引擎（JS + HTML）
│   ├── static/                # 落地页与 Studio
│   ├── readme/                # README 配图资源
│   └── node/                  # 引擎状态服务（默认随 uvicorn 自动启动）
├── courses/                   # 生成的课程（本地存储）
├── server.py                  # 可选：供 `uvicorn server:app` 转发到包内应用
├── .env.example
├── requirements.txt           # 通常为可编辑安装（`-e .`）
└── start.sh
```

---

## 🌍 支持语言

支持生成以下语言的课程：**英语、中文、日语、西班牙语、法语、韩语、阿拉伯语、德语**

---

## 🎨 视觉主题

24 种内置主题：

- **可爱/现代：** pink-cute、ocean-dream、forest-sage、candy-pop、galaxy-purple
- **中国风：** china-porcelain、china-cinnabar、dunhuang、forbidden-red、china-landscape
- **历史风：** renaissance、baroque、nordic、victorian、mediterranean
- **幻想/类型：** fairy-tale、detective、sci-fi、academy、myth

---

## 📜 许可证

本项目基于 [AGPL-3.0](./LICENSE-AGPL-3.0) 协议开源。商业授权合作请联系：[yh2072@nyu.edu](mailto:yh2072@nyu.edu)。

---

## 🌟 生产环境使用

**[ahafrog.com](https://ahafrog.com)** 是基于 EdGameClaw 构建的托管 SaaS 平台，提供用户账号、社交功能、排行榜和托管基础设施。如需完整体验而无需自托管，欢迎试用。

### 🤝 欢迎贡献课程、与大家一起分享

用 EdGameClaw 生成了有趣的课程？**欢迎来 [ahafrog.com](https://ahafrog.com) 发布并与全球学习者共享。** 你的课程将出现在公共课程库中，供任何人免费游玩。无论是中学物理、大学数学、编程入门还是历史人文——每一门好课都值得被更多人看到。

---

## 📖 引用

如果你在研究或项目中使用了 EdGameClaw，请引用：

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

## 👤 作者

**Hang Yuqi（杭雨琪）** — 纽约大学博士生

EdGameClaw 是 AI 驱动游戏化学习的开源基础框架。  
研究方向包括教育游戏 AI、人机交互、神经美学与教育神经科学。

- GitHub: [@yh2072](https://github.com/yh2072)
- 个人网站：[yuqihang.net](https://yuqihang.net)
- 官网：[ahafrog.com](https://ahafrog.com)
- 社区：[Discord — EdGameClaw](https://discord.gg/wesebXsxHV)

**微信交流群：** 使用微信扫描下方二维码加入「edgameclaw 交流」群。微信群二维码会定期失效；若无法扫码加入，请开 [GitHub Issue](https://github.com/yh2072/edgameclaw/issues) 或通过上方联系方式告知，我们会更新图片。

<p align="center">
  <img src="edgameclaw/readme/wechat.png" alt="EdGameClaw 微信群聊二维码" width="280" />
</p>

---

⭐ **若对你有帮助欢迎点个 Star！**

---

## Star History

<a href="https://www.star-history.com/?repos=yh2072%2Fedgameclaw&type=date&legend=top-left">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=yh2072/edgameclaw&type=date&theme=dark&legend=top-left" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=yh2072/edgameclaw&type=date&legend=top-left" />
   <img alt="Star History Chart" src="https://api.star-history.com/image?repos=yh2072/edgameclaw&type=date&legend=top-left" />
 </picture>
</a>

**Interactive chart (opens in new tab):** [Star History](https://www.star-history.com/?repos=yh2072%2Fedgameclaw&type=date&legend=top-left) · **可交互图表（新标签打开）**：[Star History](https://www.star-history.com/?repos=yh2072%2Fedgameclaw&type=date&legend=top-left)
