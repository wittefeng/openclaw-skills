---
name: market-scan
label: 市场扫描
description: 每日自动扫描 Hacker News、GitHub Trending、Reddit、Dev.to 等平台，生成科技市场趋势简报。适用于发现新产品、开源项目、副业机会和 AI 工具趋势。
---

# 市场扫描技能

## 功能

自动抓取以下平台的热门内容：
- **Hacker News** - 科技创业社区热门讨论
- **GitHub Trending** - 热门开源项目（Python/JS/TS/Go/Rust）
- **Reddit** - r/SideProject, r/Entrepreneur, r/startups 等
- **Dev.to** - 开发者社区热门文章

## 智能分类

自动识别内容类别：
- 🤖 **AI** - LLM、GPT、Claude、机器学习
- 💻 **Vibe Coding** - Cursor、Windsurf、AI 编程工具
- 💰 **副业/一人公司** - Indie Hacker、SaaS、被动收入
- ⚡ **效率工具** - 生产力、自动化、工作流
- 📦 **开源** - 自托管、开源项目

## 使用方式

### 手动运行
```bash
python ~/.openclaw/workspace/skills/market-scan/scripts/market_scan.py
```

### 在 OpenClaw 中使用
直接说：
- "运行市场扫描"
- "看看今天有什么新产品"
- "扫描一下 GitHub 热门"

## 输出

生成结构化简报，包含：
- 🔥 今日 Top 5 热门内容
- 💡 分类洞察统计
- 自动去重（7天窗口）
- 保存到 `data/latest_briefing.txt`

## 数据源配置

编辑 `scripts/market_scan.py` 中的以下变量：
- `DB_PATH` - SQLite 数据库路径
- `BRIEFING_PATH` - 简报输出路径

## 依赖

```bash
pip install requests
```

## 定时运行

添加到 crontab（每天早上 9 点）：
```
0 9 * * * cd ~/.openclaw/workspace/skills/market-scan && python scripts/market_scan.py
```
