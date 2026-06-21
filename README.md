# 紫微斗数 · 命理解读 App

输入生辰 → 浏览器秒出可视化命盘 → Claude AI 生成个性化解读（支持手相互证）。

排盘用 `iztro-py`（确定性计算，不靠 LLM 算命盘），解读用 Claude API。

## 目录结构

```
mingli-app/
├─ static/            前端（纯静态，可任意托管）
│  ├─ index.html
│  ├─ styles.css
│  └─ app.js
├─ mingli_core.py     共享核心：排盘 + Claude 解读
├─ server.py          本地一键服务器（只需 Python）
├─ api/               Vercel serverless 函数
│  ├─ chart.py        POST /api/chart   排盘
│  └─ reading.py      POST /api/reading 解读
├─ requirements.txt   iztro-py
├─ vercel.json        路由配置
└─ .env.example       环境变量样例
```

## 本地运行（推荐先这样验证）

只需要 Python（你已经装了）。

```powershell
# 1. 安装排盘依赖
python -m pip install iztro-py

# 2. 配置 API key（PowerShell）
$env:ANTHROPIC_API_KEY = "sk-ant-你的key"
# 可选：$env:ANTHROPIC_MODEL = "claude-opus-4-8"

# 3. 启动
cd $env:USERPROFILE\mingli-app
python server.py
```

浏览器打开 http://localhost:8000 ——填生辰、点排盘即可。
没配 API key 也能用，命盘照样秒出，只是 AI 解读那一栏会提示需要 key。

## 上线部署（Vercel，免费档够用）

1. 把整个 `mingli-app` 文件夹推到一个 GitHub 仓库。
2. 到 [vercel.com](https://vercel.com) → New Project → 导入该仓库（零配置，自动识别）。
3. 在 Project → Settings → Environment Variables 添加：
   - `ANTHROPIC_API_KEY` = 你的 key
   - （可选）`ANTHROPIC_MODEL` = `claude-opus-4-8`
4. Deploy。完成后会得到一个 `https://你的项目.vercel.app` 网址，手机电脑都能开、能分享。

> Vercel 会用 `requirements.txt` 自动为 `api/*.py` 装好 `iztro-py`；
> `vercel.json` 把 `/` 指向 `static/index.html`，`/api/*` 走 Python 函数。

## 成本

- 排盘：免费（本地/边缘计算，不调 API）。
- 解读：每次一通 Claude API 调用。Sonnet 约几分钱/次，Opus 质量更高、约几毛/次。
  手相互证会多传一张图，略增 token。

## 自定义

- 改解读风格 / 输出结构：编辑 `mingli_core.py` 里的 `SYSTEM_PROMPT`。
- 改命盘配色：编辑 `static/styles.css` 顶部的 CSS 变量。
- 换模型：设 `ANTHROPIC_MODEL` 环境变量。

## 声明

本工具为文化娱乐用途，命盘显示的是概率倾向，不预言、不替代任何专业决策。
