<p align="center">
  <img src="readme/edgameclaw_logo.png" alt="EdGameClaw" width="160">
</p>

<p align="center">
  <a href="https://ahafrog.com"><strong>🌐 ahafrog.com</strong></a> &nbsp;·&nbsp;
  <a href="https://github.com/yh2072/edgameclaw">GitHub</a> &nbsp;·&nbsp;
  <a href="#引用">引用</a> &nbsp;·&nbsp;
  <a href="README.md">English</a>
</p>

---

# EdGameClaw — AI 游戏化学习工作室

> **将任何学习材料转化为可玩的小游戏 — 只需几分钟。**

EdGameClaw 是一个自托管的开源工具，利用 AI 将你的笔记、教材或任何结构化内容转换为互动式游戏化微课程。每个知识点都会获得最适合它的游戏机制。

**无需数据库，无需登录，无需云服务。只需克隆、配置、开玩。**

---

## 🏆 EdGameClaw 的独特优势

大多数 AI 学习工具生成的是幻灯片、讲座稿或 AI 配音视频。EdGameClaw 做的是完全不同的事：它把知识变成**真正可玩的游戏**。

| | AI 幻灯片 / 讲课工具 | EdGameClaw |
|---|---|---|
| 输出形式 | 幻灯片、视频、文字 | **可在浏览器中直接游玩的游戏** |
| 学习方式 | 被动观看 / 阅读 | **主动游玩 — 得分、失败、重试** |
| 视觉风格 | 通用模板 | **AI 为每节课生成独立像素画** |
| 游戏机制 | 无 | **根据每个知识点匹配最合适的机制** |
| 部署方式 | 云端 SaaS | **完全自托管，支持离线运行** |
| LLM 提供商 | 被锁定 | **任意 OpenAI 兼容 API（BYOK）** |
| 开源 | 闭源 / 部分开源 | **完全开源，可 Fork 并自由扩展** |

### 🎮 真正的游戏，不是美化的幻灯片

其他工具不过是给幻灯片加了动效，或在视频旁边挂了个聊天窗口。EdGameClaw 在浏览器中运行一套**自研像素画游戏引擎**。学习者会体验进度条、得分、角色对话、动画效果和游戏失败状态——这是真实的游戏体验，不是套了皮的测验。

### 🖼️ AI 生成像素画，每次都不同

每节课都有自己的视觉世界：AI 生成的角色、背景与图标，而非通用图库素材。24 套内置主题（从「中国水墨」到「科幻」到「巴洛克」）让每门课程拥有独特的视觉气质，没有两个游戏长得一样。

### 🔀 机制与概念精准匹配

流水线不只是「生成一道关于 X 的题目」。它会分析知识点本质，并分配最能强化理解的游戏机制——空间推理用摆放游戏，因果链用排序挑战，词汇记忆用消除配对。**这正是 EdGameClaw 的核心洞察**。

### 🔒 零锁定 — 内容完全归你

无账号、无云端上传、无订阅费。所有生成的课程以普通文件形式存储在本地。换 LLM 提供商只需改一行环境变量。引擎可随意 Fork。你生成的内容完全属于你自己。

---

## 🎬 工作原理

**演示：** [demo](https://github.com/yh2072/edgameclaw/issues/1#issuecomment-4059754684)

粘贴内容 → AI 生成完整游戏课程 → 立即在浏览器中游玩。

---

## 🎮 案例展示 — 一句话，一个游戏

以下每个游戏都由**一句话或一小段文字**生成，无需手动设计，无需编程。

<table>
<tr>
<td align="center" width="25%">

**方寸乾坤**

![方寸乾坤](readme/方寸乾坤.gif)

</td>
<td align="center" width="25%">

**神经科学：全局 vs 局部**

![神经科学全局局部辩论](readme/神经科学全局局部辩论.gif)

</td>
<td align="center" width="25%">

**经济学原理**

![经济学原理](readme/经济学原理.gif)

</td>
<td align="center" width="25%">

**卷积神经网络**

![CNN](readme/cnn.gif)

</td>
</tr>
</table>

> 哲学、神经科学、经济学、深度学习 — EdGameClaw 会自动为每个学科匹配最合适的游戏机制。

---

## 📋 自动生成的课程大纲

EdGameClaw 不只是生成游戏 — 它会先生成结构化的课程大纲，再将每个章节映射到对应的游戏机制。

![课程大纲 — Attention & Residuals](readme/case%20study-%20course%20syllabus-attention%20residuals.png)

---

## 🚀 快速开始

### 方式一：Python（推荐）

**前置条件：** Python 3.10+，Node.js 18+

```bash
# 1. 克隆仓库
git clone https://github.com/yh2072/edgameclaw
cd edgameclaw

# 2. 创建虚拟环境（任选其一）
python -m venv .venv && source .venv/bin/activate  # venv（内置）
# conda create -n edgameclaw python=3.11 && conda activate edgameclaw  # conda

# 3. 安装 Python 依赖
pip install -r requirements.txt

# 4. 配置 API 密钥
cp .env.example .env
# 编辑 .env 文件，填入你的 API_KEY

# 5. 启动服务器
bash start.sh
# 或者：uvicorn server:app --reload
```

打开 **http://localhost:8000** → Studio 已就绪！

### 方式二：Docker

```bash
docker run -p 8000:8000 -e API_KEY=sk-your-key ghcr.io/YOUR_USERNAME/edgameclaw
```

---

## ⚙️ 配置说明

将 `.env.example` 复制为 `.env` 并填写：

| 变量 | 必填 | 说明 |
|------|------|------|
| `API_KEY` | 是* | OpenAI 兼容的 API 密钥 |
| `MODEL` | 否 | 模型名称（默认：`google/gemini-3-flash-preview`） |
| `API_BASE_URL` | 否 | API 地址（默认：OpenRouter） |
| `PORT` | 否 | 服务端口（默认：`8000`） |
| `BIND_HOST` | 否 | 绑定地址（默认：`127.0.0.1`） |

*也可以直接在 Studio 界面输入 API 密钥 — 仅存储在你的浏览器中。

### 推荐 AI 提供商

**推荐模型：** 通过 OpenRouter 使用 `google/gemini-3-flash-preview` — 速度快，性价比高。

---

## ⚡ 流水线工作原理

1. **粘贴** Markdown 格式的学习内容
2. **解析** — EdGameClaw 提取课程结构（标题、章节）
3. **大纲** — AI 生成结构化学习计划，为每个章节匹配游戏机制
4. **生成** — AI 流水线为每个章节创建定制小游戏
5. **游玩** — 游戏立即在浏览器中可玩

---

## 📁 项目结构

```
edgameclaw/
├── server.py           # FastAPI 服务器
├── generator/          # AI 课程生成流水线
│   ├── pipeline.py     # 主调度逻辑
│   ├── api.py          # LLM API 客户端
│   ├── prompts.py      # Prompt 模板
│   ├── assembler.py    # 课程组装与主题
│   └── ...
├── engine/             # 游戏引擎
│   ├── engine.js       # 游戏状态机
│   ├── player.html     # 浏览器游戏播放器
│   └── minigames/      # 小游戏实现
├── node/               # Node.js 引擎状态服务器
├── static/             # 前端页面
│   ├── index.html      # 落地页
│   └── studio.html     # Studio 应用
├── courses/            # 生成的课程（本地存储）
├── .env.example        # 配置模板
├── requirements.txt    # Python 依赖
└── start.sh            # 快速启动脚本
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

本项目基于 [AGPL-3.0](./LICENSE) 协议开源。商业授权合作请联系：[yh2072@nyu.edu](mailto:yh2072@nyu.edu)。

---

## 🌟 生产环境使用

**[ahafrog.com](https://ahafrog.com)** 是基于 EdGameClaw 构建的托管 SaaS 平台，提供用户账号、社交功能、排行榜和托管基础设施。如需完整体验而无需自托管，欢迎试用。

### 🤝 欢迎贡献课程、与大家一起分享！

用 EdGameClaw 生成了有趣的课程？**欢迎来 [ahafrog.com](https://ahafrog.com) 发布并与全球学习者共享。** 你的课程将出现在公共课程库中，供任何人免费游玩。无论是中学物理、大学数学、编程入门还是历史人文——每一门好课都值得被更多人看到。

---

## 📖 引用

如果你在研究或项目中使用了 EdGameClaw，请引用：

```bibtex
@software{hang2025edgameclaw,
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
雨琪的研究方向包括教育游戏 AI、人机交互、神经美学与教育神经科学。

- GitHub: [@yh2072](https://github.com/yh2072)
- 官网：[ahafrog.com](https://ahafrog.com)

---

⭐ **如果这个项目对你有帮助，请在 GitHub 上给个 Star！** 这将帮助更多人发现它。
