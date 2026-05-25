# Steam Game Insight Copilot

Steam Game Insight Copilot 是一个基于 Streamlit 的 Steam 玩家反馈与竞品分析工具。用户输入 Steam 游戏名称、AppID 或商店链接后，系统会搜索游戏、获取玩家评论、清洗文本、统计口碑指标、提取关键词、识别游戏业务标签，并生成“玩家情感 × 热度”四象限图和 Markdown 分析报告。

## 项目背景

游戏团队在立项、版本复盘、竞品拆解和商店页优化时，常常需要快速理解大量玩家评论。手工阅读效率低，且结论难以复用。本项目把“信息收集 → 数据清洗 → 分析建模 → 方案整理 → 内容产出 → 复盘沉淀”串成一个可演示的 AI 辅助工作流。

## 核心功能

- Steam 游戏名称搜索与 AppID/商店链接解析
- Steam 公开评论分页获取，支持语言、评论类型、购买类型和排序筛选
- 评论清洗、好评率、游玩时长、评论长度等基础统计
- 中文 jieba / 英文 CountVectorizer 关键词提取
- 游戏行业业务标签分类：玩法、内容、性能、价格、平衡、新手、联机、BUG、更新、美术音乐
- 玩家情感 × 热度四象限图：核心卖点、优先修复问题、潜力亮点、长尾问题、分歧反馈
- 单款游戏 Markdown 分析报告
- 多款游戏竞品对比分析报告
- CSV、Markdown、ZIP 导出
- Demo 模式：无网络或无 API Key 也能体验完整流程

## 功能截图占位

> 可在运行后截图：单款游戏分析页、四象限气泡图、竞品对比表、Markdown 报告。

## 技术栈

- Python 3.10+
- Streamlit
- requests
- pandas
- jieba
- scikit-learn
- plotly
- beautifulsoup4
- python-dotenv
- pyyaml
- pytest

## 安装方式

```bash
cd steam-game-insight-copilot
pip install -r requirements.txt
```

## 运行方式

```bash
streamlit run app.py
```

## 公网部署

### Streamlit Community Cloud

1. 将本项目上传到 GitHub。
2. 打开 Streamlit Community Cloud，新建 App。
3. Repository 选择本项目仓库。
4. Main file path 填写：

```text
app.py
```

5. 点击 Deploy，即可获得公网访问链接。

项目已包含：

- `runtime.txt`：指定 Python 版本
- `packages.txt`：安装中文字体，保证词云中文正常显示
- `.streamlit/config.toml`：云端 Streamlit 配置

### Render

项目也包含 `render.yaml`。在 Render 中选择 Blueprint 部署，或手动配置：

```bash
pip install -r requirements.txt
streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

## 使用示例

1. 输入 `1942280` 或 `https://store.steampowered.com/app/1942280/Brotato/`。
2. 选择评论数量、语言和筛选条件。
3. 点击“开始分析”。
4. 查看指标卡片、关键词图、标签分布、四象限图和 Markdown 报告。
5. 下载 CSV、Markdown 或 ZIP。

如果只是想快速演示，可以直接点击“使用示例数据体验”。

## 数据来源说明

评论数据来自 Steam 商店公开评论接口：`https://store.steampowered.com/appreviews/<appid>?json=1`。项目不会保存 steamid，仅保留评论内容、推荐状态、投票数、游玩时长等分析字段。

## 合规说明

本项目用于学习、研究、作品集和面试展示。请求设置了 timeout、分页上限和短暂 sleep，避免高频访问。请遵守 Steam 服务条款，不将导出数据用于侵犯用户权益的场景。

## 四象限分析模型说明

- 横轴：热度，即某类业务标签在全部标签反馈中的出现占比。
- 纵轴：玩家情感，即该类反馈中好评占比。
- 热度高且情感高：核心卖点。
- 热度高且情感低：优先修复问题。
- 热度低且情感高：潜力亮点。
- 热度低且情感低：长尾问题。
- 中间区间：分歧反馈。

这个模型帮助把零散评论转化为研发、运营、宣发都能理解的优先级语言。

## 简历写法

Steam Game Insight Copilot｜Python / Streamlit / NLP / 数据分析

- 从零开发 Steam 玩家反馈与竞品分析工具，支持游戏搜索、评论抓取、文本清洗、关键词提取、业务标签分类、四象限优先级分析和 Markdown 报告导出。
- 设计“玩家情感 × 热度”模型，将评论数据转化为核心卖点、优先修复问题和潜力亮点，辅助版本复盘与宣发素材提炼。
- 支持无 OpenAI API Key 的本地模板报告，同时预留 AI 报告润色入口，体现 AI 工具提升信息收集、分析和内容产出效率。

## 面试讲解稿

这个项目解决的是游戏团队读 Steam 评论效率低的问题。我把它做成一个端到端工具：输入游戏名或 AppID 后，自动获取评论、清洗文本、统计好评率和游玩时长，再通过关键词和业务标签把玩家反馈归因到玩法、内容、性能、价格、平衡、BUG 等维度。核心亮点是“玩家情感 × 热度”四象限模型，可以快速判断哪些是核心卖点，哪些是优先修复问题。最后系统会生成 Markdown 报告和 CSV 导出，适合版本复盘、竞品分析和面试展示。项目默认不依赖 OpenAI Key，用模板也能完整运行，如果配置 Key 则可以进一步润色报告。

## 后续迭代方向

- 接入更多数据源，例如 TapTap、Bilibili、Reddit 或 Discord 摘要
- 增加时间序列分析，观察更新前后口碑变化
- 增加主题聚类和相似评论合并
- 增加目标产品与竞品的差异化机会点自动生成
- 增加团队协作能力，例如导出为飞书/Notion 文档
