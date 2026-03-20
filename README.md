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
  <a href="#english"><img src="https://img.shields.io/badge/English-README-2ea44f?style=for-the-badge" alt="English README" /></a>
  <a href="#cn"><img src="https://img.shields.io/badge/简体中文-README-555?style=for-the-badge" alt="简体中文 README" /></a>
</p>

<p align="center"><sub>简体中文与英文在下方以<strong>左右两列同位对照</strong>展示（点击徽标可跳到对应列）。演示视频在「How It Works」全宽播放。</sub></p>

<p align="center">
  <a href="https://ahafrog.com"><strong>🌐 ahafrog.com</strong></a> &nbsp;·&nbsp;
  <a href="https://github.com/yh2072/edgameclaw">⭐ GitHub</a> &nbsp;·&nbsp;
  <a href="https://openrouter.ai"><strong>🔌 OpenRouter</strong></a> &nbsp;·&nbsp;
  <a href="#citation">📖 Citation</a> &nbsp;·&nbsp;
  <a href="#quick-start">🚀 Quick Start</a>
</p>

---

<!-- Bilingual intro + differentiators: English (left) and 简体中文 (right), same vertical position -->

<table>
<tr>
<td width="50%" valign="top">

<a id="english"></a>

<h2>EdGameClaw — AI Game-Based Learning Studio</h2>

<p><strong>Turn any learning material into playable mini-games — in minutes.</strong></p>

<p>EdGameClaw is a self-hosted, open-source tool that uses AI to convert your notes, textbooks, or any structured content into interactive game-based micro-courses. Each concept gets the mini-game mechanic it deserves.</p>

<p><strong>No database. No login. No cloud required. Just clone, configure, and play.</strong></p>

<h3>🏆 What Makes EdGameClaw Different</h3>

<p>Most AI learning tools generate slides, lecture transcripts, or talking-head videos. EdGameClaw does something fundamentally different: it turns knowledge into <strong>games you actually play</strong>.</p>

<table>
<thead>
<tr><th></th><th>AI Slide / Lecture Tools</th><th>EdGameClaw</th></tr>
</thead>
<tbody>
<tr><td>Output format</td><td>Slides, video, text</td><td><strong>Playable browser game</strong></td></tr>
<tr><td>Learning mode</td><td>Passive watching / reading</td><td><strong>Active play — score, fail, retry</strong></td></tr>
<tr><td>Visual identity</td><td>Generic templates</td><td><strong>AI-generated pixel art per lesson</strong></td></tr>
<tr><td>Game mechanics</td><td>None</td><td><strong>Mechanic matched to each concept</strong></td></tr>
<tr><td>Hosting</td><td>Cloud SaaS</td><td><strong>Fully self-hosted, runs offline</strong></td></tr>
<tr><td>LLM provider</td><td>Locked in</td><td><strong>Any OpenAI-compatible API (BYOK)</strong></td></tr>
<tr><td>Open source</td><td>Closed / partial</td><td><strong>Fully open, fork and extend</strong></td></tr>
</tbody>
</table>

<h4>🎮 Real Games, Not Decorated Slides</h4>

<p>Other tools dress up slides with animations or add a chat window to a video. EdGameClaw runs a <strong>custom pixel-art game engine</strong> in the browser. Learners experience progression bars, scoring, character dialog, animations, and game-over states. The mechanic is designed per concept — a sorting puzzle for taxonomy, a dialog simulation for argument analysis, a timed challenge for recall — not the same quiz widget applied to everything.</p>

<h4>🖼️ AI-Generated Pixel Art, Every Time</h4>

<p>Every lesson gets its own visual world: AI-generated characters, backgrounds, and icons — not stock photos or clip art. 24 built-in themes (from <em>china-ink</em> to <em>sci-fi</em> to <em>baroque</em>) give each course a distinct aesthetic. No two games look the same.</p>

<h4>🔀 Mechanic-to-Concept Matching</h4>

<p>The pipeline doesn't just &quot;generate a quiz about X.&quot; It analyzes the concept and assigns the game mechanic that best reinforces it — spatial reasoning gets a placement game, causal chains get a sequencing challenge, vocabulary gets a match-and-eliminate mechanic. This is the core insight EdGameClaw is built on.</p>

<h4>🔒 Zero Lock-in — Yours to Own</h4>

<p>No accounts. No cloud uploads. No subscription. All generated courses live on your machine as plain files. Swap your LLM provider in one env variable. Fork the engine. The content you generate is entirely yours.</p>

</td>
<td width="50%" valign="top">

<a id="cn"></a>

<h2>EdGameClaw — AI 游戏化学习工作室</h2>

<p><strong>将任何学习材料转化为可玩的小游戏 — 只需几分钟。</strong></p>

<p>EdGameClaw 是一个自托管的开源工具，利用 AI 将你的笔记、教材或任何结构化内容转换为互动式游戏化微课程。每个知识点都会获得最适合它的游戏机制。</p>

<p><strong>无需数据库，无需登录，无需云服务。只需克隆、配置、开玩。</strong></p>

<h3>🏆 EdGameClaw 的独特优势</h3>

<p>大多数 AI 学习工具生成的是幻灯片、讲座稿或 AI 配音视频。EdGameClaw 做的是完全不同的事：它把知识变成<strong>真正可玩的游戏</strong>。</p>

<table>
<thead>
<tr><th></th><th>AI 幻灯片 / 讲课工具</th><th>EdGameClaw</th></tr>
</thead>
<tbody>
<tr><td>输出形式</td><td>幻灯片、视频、文字</td><td><strong>可在浏览器中直接游玩的游戏</strong></td></tr>
<tr><td>学习方式</td><td>被动观看 / 阅读</td><td><strong>主动游玩 — 得分、失败、重试</strong></td></tr>
<tr><td>视觉风格</td><td>通用模板</td><td><strong>AI 为每节课生成独立像素画</strong></td></tr>
<tr><td>游戏机制</td><td>无</td><td><strong>根据每个知识点匹配最合适的机制</strong></td></tr>
<tr><td>部署方式</td><td>云端 SaaS</td><td><strong>完全自托管，支持离线运行</strong></td></tr>
<tr><td>LLM 提供商</td><td>被锁定</td><td><strong>任意 OpenAI 兼容 API（BYOK）</strong></td></tr>
<tr><td>开源</td><td>闭源 / 部分开源</td><td><strong>完全开源，可 Fork 并自由扩展</strong></td></tr>
</tbody>
</table>

<h4>🎮 真正的游戏，不是美化的幻灯片</h4>

<p>其他工具不过是给幻灯片加了动效，或在视频旁边挂了个聊天窗口。EdGameClaw 在浏览器中运行一套<strong>自研像素画游戏引擎</strong>。学习者会体验进度条、得分、角色对话、动画效果和游戏失败状态——这是真实的游戏体验，不是套了皮的测验。</p>

<h4>🖼️ AI 生成像素画，每次都不同</h4>

<p>每节课都有自己的视觉世界：AI 生成的角色、背景与图标，而非通用图库素材。24 套内置主题（从「中国水墨」到「科幻」到「巴洛克」）让每门课程拥有独特的视觉气质，没有两个游戏长得一样。</p>

<h4>🔀 机制与概念精准匹配</h4>

<p>流水线不只是「生成一道关于 X 的题目」。它会分析知识点本质，并分配最能强化理解的游戏机制——空间推理用摆放游戏，因果链用排序挑战，词汇记忆用消除配对。<strong>这正是 EdGameClaw 的核心洞察</strong>。</p>

<h4>🔒 零锁定 — 内容完全归你</h4>

<p>无账号、无云端上传、无订阅费。所有生成的课程以普通文件形式存储在本地。换 LLM 提供商只需改一行环境变量。引擎可随意 Fork。你生成的内容完全属于你自己。</p>

</td>
</tr>
</table>

---

## 🎬 How It Works / 工作原理

<p align="center">
  <video
    controls
    playsinline
    preload="metadata"
    muted
    poster="readme/edgameclaw_logo.png"
    src="https://github.com/user-attachments/assets/d5c19a93-6f8d-4ed2-855d-d57046bcf008"
    width="100%"
    style="max-width: 920px; border-radius: 12px;"
  >
    Your browser does not support the video tag.
  </video>
</p>

<table>
<tr>
<td width="50%" valign="top"><strong>EN:</strong> Paste your content → AI generates a full game-based course → Play instantly in your browser.</td>
<td width="50%" valign="top"><strong>中文：</strong> 粘贴内容 → AI 生成完整游戏课程 → 立即在浏览器中游玩。</td>
</tr>
</table>

---

## 🎮 Case Study / 案例展示 — One Sentence · 一句话

<table>
<tr>
<td width="50%" valign="top">Each game below was generated from <strong>a single sentence or short paragraph</strong>. No manual design. No coding.</td>
<td width="50%" valign="top">以下每个游戏都由<strong>一句话或一小段文字</strong>生成，无需手动设计，无需编程。</td>
</tr>
</table>

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

<table>
<tr>
<td width="50%" valign="top"><strong>EN:</strong> Philosophy, neuroscience, economics, deep learning — EdGameClaw adapts its game mechanics to each subject automatically.</td>
<td width="50%" valign="top"><strong>中文：</strong> 哲学、神经科学、经济学、深度学习 — EdGameClaw 会自动为每个学科匹配最合适的游戏机制。</td>
</tr>
</table>

---

## 📋 Generated Course Syllabus / 自动生成的课程大纲

<table>
<tr>
<td width="50%" valign="top">EdGameClaw doesn't just create games — it first generates a structured course syllabus, then maps each chapter to the right game mechanic.</td>
<td width="50%" valign="top">EdGameClaw 不只是生成游戏 — 它会先生成结构化的课程大纲，再将每个章节映射到对应的游戏机制。</td>
</tr>
</table>

![Course Syllabus — Attention & Residuals](readme/case%20study-%20course%20syllabus-attention%20residuals.png)

---

## 🚀 Quick Start / 快速开始 {#quick-start}

### Option 1: Python (Recommended) / 方式一：Python（推荐）

**Prerequisites / 前置条件:** Python 3.10+, Node.js 18+

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

Open **http://localhost:8000** → Studio is ready! · 打开 **http://localhost:8000** → Studio 已就绪！

### Option 2: Docker ·  Docker

```bash
docker run -p 8000:8000 -e API_KEY=sk-your-key ghcr.io/YOUR_USERNAME/edgameclaw
```

---

## ⚙️ Configuration / 配置说明

Copy `.env.example` to `.env` and set your values: · 将 `.env.example` 复制为 `.env` 并填写：

| Variable | Required | Description (EN) | 说明（中文） |
|----------|----------|------------------|--------------|
| `API_KEY` | Yes* / 是* | Your OpenAI-compatible API key | OpenAI 兼容的 API 密钥 |
| `MODEL` | No / 否 | Model name (default: `google/gemini-3-flash-preview`) | 模型名称（默认：`google/gemini-3-flash-preview`） |
| `API_BASE_URL` | No / 否 | API endpoint (default: OpenRouter) | API 地址（默认：OpenRouter） |
| `PORT` | No / 否 | Server port (default: `8000`) | 服务端口（默认：`8000`） |
| `BIND_HOST` | No / 否 | Bind address (default: `127.0.0.1`) | 绑定地址（默认：`127.0.0.1`） |

*You can also enter your API key directly in the Studio UI — it's stored only in your browser. · *也可以直接在 Studio 界面输入 API 密钥 — 仅存储在你的浏览器中。

### Recommended AI Providers · 推荐 AI 提供商

**Default stack / 默认方案:** [**OpenRouter**](https://openrouter.ai) (`API_BASE_URL=https://openrouter.ai/api/v1`) — one key, [many models](https://openrouter.ai/models), pay-as-you-go. · 一把密钥接入[多种模型](https://openrouter.ai/models)，按量计费。

**Recommended model / 推荐模型:** `google/gemini-3-flash-preview` via OpenRouter — fast and cost-effective. · 通过 OpenRouter 使用 — 速度快，性价比高。

---

## ⚡ How the Pipeline Works / 流水线工作原理

<table>
<tr><th width="50%">EN</th><th width="50%">中文</th></tr>
<tr>
<td valign="top">
<ol>
<li><strong>Paste</strong> your learning content in Markdown format</li>
<li><strong>Parse</strong> — EdGameClaw extracts course structure (title, chapters)</li>
<li><strong>Syllabus</strong> — AI generates a structured learning plan with game mechanics mapped to each chapter</li>
<li><strong>Generate</strong> — AI pipeline creates custom mini-games for each chapter</li>
<li><strong>Play</strong> — Games open instantly in your browser</li>
</ol>
</td>
<td valign="top">
<ol>
<li><strong>粘贴</strong> Markdown 格式的学习内容</li>
<li><strong>解析</strong> — EdGameClaw 提取课程结构（标题、章节）</li>
<li><strong>大纲</strong> — AI 生成结构化学习计划，为每个章节匹配游戏机制</li>
<li><strong>生成</strong> — AI 流水线为每个章节创建定制小游戏</li>
<li><strong>游玩</strong> — 游戏立即在浏览器中可玩</li>
</ol>
</td>
</tr>
</table>

---

## 📁 Project Structure / 项目结构

```
edgameclaw/
├── server.py           # FastAPI server / FastAPI 服务器
├── generator/          # AI course generation pipeline / AI 课程生成流水线
│   ├── pipeline.py     # Main orchestration / 主调度逻辑
│   ├── api.py          # LLM API client / LLM API 客户端
│   ├── prompts.py      # Prompt templates / Prompt 模板
│   ├── assembler.py    # Course assembly & theming / 课程组装与主题
│   └── ...
├── engine/             # Game engine / 游戏引擎
│   ├── engine.js       # Game state machine / 游戏状态机
│   ├── player.html     # Browser game player / 浏览器游戏播放器
│   └── minigames/      # Mini-game implementations / 小游戏实现
├── node/               # Node.js engine state server / Node.js 引擎状态服务器
├── static/             # Frontend / 前端页面
│   ├── index.html      # Landing page / 落地页
│   └── studio.html     # Studio app / Studio 应用
├── courses/            # Generated courses (local storage) / 生成的课程（本地存储）
├── .env.example        # Configuration template / 配置模板
├── requirements.txt    # Python dependencies / Python 依赖
└── start.sh            # Quick start script / 快速启动脚本
```

---

## 🌍 Supported Languages / 支持语言

<table>
<tr>
<td width="50%" valign="top">Generate courses in: <strong>English, Chinese (中文), Japanese (日本語), Spanish (Español), French (Français), Korean (한국어), Arabic (العربية), German (Deutsch)</strong></td>
<td width="50%" valign="top">支持生成以下语言的课程：<strong>英语、中文、日语、西班牙语、法语、韩语、阿拉伯语、德语</strong></td>
</tr>
</table>

---

## 🎨 Visual Themes / 视觉主题

<table>
<tr>
<td width="50%" valign="top">
24 built-in themes:
<ul>
<li><strong>Cute/Modern:</strong> pink-cute, ocean-dream, forest-sage, candy-pop, galaxy-purple</li>
<li><strong>Chinese:</strong> china-porcelain, china-cinnabar, dunhuang, forbidden-red, china-landscape</li>
<li><strong>Historical:</strong> renaissance, baroque, nordic, victorian, mediterranean</li>
<li><strong>Fantasy/Genre:</strong> fairy-tale, detective, sci-fi, academy, myth</li>
</ul>
</td>
<td width="50%" valign="top">
24 种内置主题：
<ul>
<li><strong>可爱/现代：</strong> pink-cute、ocean-dream、forest-sage、candy-pop、galaxy-purple</li>
<li><strong>中国风：</strong> china-porcelain、china-cinnabar、dunhuang、forbidden-red、china-landscape</li>
<li><strong>历史风：</strong> renaissance、baroque、nordic、victorian、mediterranean</li>
<li><strong>幻想/类型：</strong> fairy-tale、detective、sci-fi、academy、myth</li>
</ul>
</td>
</tr>
</table>


---

## 📜 License / 许可证

<table>
<tr>
<td width="50%" valign="top">This project is open source under the <strong>AGPL-3.0</strong> license. See <a href="./LICENSE-AGPL-3.0">LICENSE-AGPL-3.0</a> for the full text. For commercial licensing, contact: <a href="mailto:yh2072@nyu.edu">yh2072@nyu.edu</a>.</td>
<td width="50%" valign="top">本项目基于 <a href="./LICENSE-AGPL-3.0">AGPL-3.0</a> 协议开源。商业授权合作请联系：<a href="mailto:yh2072@nyu.edu">yh2072@nyu.edu</a>。</td>
</tr>
</table>

---

## 🌟 Production Use / 生产环境使用

<table>
<tr>
<td width="50%" valign="top"><strong><a href="https://ahafrog.com">ahafrog</a></strong> is the hosted, full-featured SaaS platform built on top of EdGameClaw — with user accounts, social features, leaderboards, and a managed infrastructure. Try it if you want the full experience without self-hosting.</td>
<td width="50%" valign="top"><strong><a href="https://ahafrog.com">ahafrog.com</a></strong> 是基于 EdGameClaw 构建的托管 SaaS 平台，提供用户账号、社交功能、排行榜和托管基础设施。如需完整体验而无需自托管，欢迎试用。</td>
</tr>
</table>

### 🤝 Share your courses / 欢迎贡献课程

<table>
<tr>
<td width="50%" valign="top">Built something great with EdGameClaw? <strong>Publish it on <a href="https://ahafrog.com">ahafrog.com</a> and share it with learners everywhere.</strong> Your course will appear in the public course library — free to play for anyone.</td>
<td width="50%" valign="top">用 EdGameClaw 生成了有趣的课程？<strong>欢迎来 <a href="https://ahafrog.com">ahafrog.com</a> 发布并与全球学习者共享。</strong> 你的课程将出现在公共课程库中，供任何人免费游玩。</td>
</tr>
</table>

---

## 📖 Citation {#citation}

If you use EdGameClaw in research or a project, please cite: · 如果你在研究或项目中使用了 EdGameClaw，请引用：

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

## 👤 Author / 作者

<table>
<tr>
<td width="50%" valign="top">
<strong>Yuqi Hang</strong> — PhD Student @ New York University
<p>Built EdGameClaw as an open-source foundation for AI-powered game-based learning. Research interests include AI for educational games, human-computer interaction, neuroaesthetics and educational neuroscience.</p>
<ul>
<li>GitHub: <a href="https://github.com/yh2072">@yh2072</a></li>
<li>Website: <a href="https://yuqihang.net">yuqihang.net</a></li>
<li>Project: <a href="https://ahafrog.com">ahafrog.com</a></li>
</ul>
</td>
<td width="50%" valign="top">
<strong>Hang Yuqi（杭雨琪）</strong> — 纽约大学博士生
<p>EdGameClaw 是 AI 驱动游戏化学习的开源基础框架。研究方向包括教育游戏 AI、人机交互、神经美学与教育神经科学。</p>
<ul>
<li>GitHub: <a href="https://github.com/yh2072">@yh2072</a></li>
<li>个人网站: <a href="https://yuqihang.net">yuqihang.net</a></li>
<li>官网: <a href="https://ahafrog.com">ahafrog.com</a></li>
</ul>
</td>
</tr>
</table>

---

⭐ **If this project is useful to you, please star it on GitHub!** · **若对你有帮助欢迎点个 Star！**
