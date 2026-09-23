<p align="center">
  <img src="assets/hero.svg" alt="JevHub：每天发现 Jev 生态项目，追踪 GitHub Stars 与社区动态" width="1200">
</p>

<h1 align="center">JevHub · Jev 生态热榜</h1>

<p align="center">
  <strong>把值得关注的 Jev 项目、教程和讨论，汇到一页。</strong><br>
  自动发现 · 每日更新 · 按 Stars 排序 · 中英双语
</p>

<p align="center">
  <a href="https://frontierlabai.github.io/JevHub/"><img src="assets/website-badge.zh.svg" alt="访问 JevHub 网站 — https://frontierlabai.github.io/JevHub/" width="380"></a>
</p>

<p align="center">
  <a href="https://hits.sh/github.com/frontierlabai/JevHub/"><img src="https://hits.sh/github.com/frontierlabai/JevHub.svg?label=README%20views&amp;color=163e64&amp;labelColor=182129" alt="README 访问次数（徽章请求计数，非独立访客）"></a>
</p>

<p align="center">
  <a href="https://github.com/frontierlabai/JevHub/actions/workflows/refresh.yml"><img src="https://github.com/frontierlabai/JevHub/actions/workflows/refresh.yml/badge.svg" alt="每日更新工作流状态"></a>
  <a href="https://github.com/frontierlabai/JevHub/stargazers"><img src="https://img.shields.io/github/stars/frontierlabai/JevHub?style=flat&amp;color=6ee7b7" alt="Star JevHub"></a>
  <a href="#automation"><img src="https://img.shields.io/badge/refresh-daily%20%C2%B7%2009%3A17%20CST-67e8f9?style=flat" alt="计划每日北京时间 09:17 更新"></a>
  <a href="https://docs.typesafe.ai/"><img src="https://img.shields.io/badge/explore-Jev%20%2F%20System%20One-c4b5fd?style=flat" alt="Jev 官方文档"></a>
</p>

<p align="center">
  <strong>简体中文</strong> · <a href="README.en.md">English</a><br>
  <a href="#github-ranking">项目精选</a> · <a href="#community-radar">社区雷达</a> · <a href="#curated-resources">精选资源</a> · <a href="#getting-started">快速入门</a>
</p>

> **这是哪个 Jev？** 本站关注 [TypeSafe AI](https://typesafe.ai/) 的 **Jev / System One** 决策模型：面向软件提供结构化决策。JevHub 是独立社区目录，与 TypeSafe AI 无官方隶属关系。[了解 Jev →](https://docs.typesafe.ai/introduction)

{{DASHBOARD}}

<a id="getting-started"></a>

## 🚀 从这里开始

| 你想做什么 | 推荐入口 |
| :--- | :--- |
| 认识 Jev 和 System One | [官方介绍](https://docs.typesafe.ai/introduction) · [TypeSafe AI](https://typesafe.ai/) |
| 接入应用、理解 API | [官方文档](https://docs.typesafe.ai/) |
| 找 SDK、示例与社区项目 | [项目精选](#github-ranking) · [精选资源](#curated-resources) |
| 追踪新项目和讨论 | [项目精选](#github-ranking) · [社区雷达](#community-radar) |
| 推荐你发现的好资源 | [提交资源](https://github.com/frontierlabai/JevHub/issues/new?template=resource.yml) · [贡献指南](CONTRIBUTING.md) |

<a id="share"></a>

## 💚 让好内容被更多人看见

觉得有用，可以 **Star 收藏**，把项目链接发给正在研究 Jev 的朋友。欢迎在文章、视频和社群里引用本目录，并保留原始资源的来源链接。

[分享到 X](https://twitter.com/intent/tweet?text=JevHub%20%E2%80%94%20a%20daily%20radar%20for%20the%20Jev%20ecosystem.%20Projects%2C%20GitHub%20stars%2C%20and%20community%20discussions.&url=https%3A%2F%2Fgithub.com%2Ffrontierlabai%2FJevHub) · [分享到 LinkedIn](https://www.linkedin.com/sharing/share-offsite/?url=https%3A%2F%2Fgithub.com%2Ffrontierlabai%2FJevHub) · [推荐一个资源](https://github.com/frontierlabai/JevHub/issues/new?template=resource.yml)

分享地址：**https://github.com/frontierlabai/JevHub**

<a id="automation"></a>

## ⚙️ 自动更新如何工作

将工作流推送到仓库默认分支并启用 GitHub Actions 后，系统按计划每天 **UTC 01:17 / 北京时间 09:17** 更新，也可在 [Actions 页面](https://github.com/frontierlabai/JevHub/actions/workflows/refresh.yml) 手动运行。GitHub 定时任务可能延迟，实际采集时间以榜单记录为准。

1. 根据 [`config/sources.json`](config/sources.json) 的检索配置发现公开内容，补充种子仓库与人工精选链接。
2. 获取 GitHub 仓库信息，按 Star 总数展示前 30 个项目，突出项目本身与维护者简介。
3. 汇总 Hacker News、Reddit、Hugging Face 等公开来源，把结果写入中英文 README。
4. 保存 [`data/latest.json`](data/latest.json) 和 `data/history/YYYY-MM-DD.json`，供核验与后续比较。

本地更新只需 **Python 3.11+**，无需安装第三方依赖：

```bash
git clone https://github.com/frontierlabai/JevHub.git
cd JevHub
python3 scripts/update.py
python3 -m unittest discover -s tests -v
```

只修改模板、精选资源或展示数量时，可以复用已有的 `data/latest.json`，无需联网：

```bash
python3 scripts/update.py --render-only
python3 scripts/update.py --render-only --check
```

`--render-only` 重建中英文 README；加上 `--check` 则只检查生成内容是否一致，不写文件。离线重渲染保留原采集时间，不刷新 Stars；修改检索词、种子或排除名单后，应运行一次联网更新。

在自己的 Fork 中，请确保工作流已位于默认分支、Actions 已启用，且工作流有写入仓库内容的权限。配置见 [`.github/workflows/refresh.yml`](.github/workflows/refresh.yml)。高频本地检索可通过环境变量 `GITHUB_TOKEN` 提供 GitHub 令牌；请勿把令牌写进配置或提交到仓库。

<details>
<summary><strong>维护入口与文件说明</strong></summary>

| 文件 | 用途 |
| :--- | :--- |
| [`config/sources.json`](config/sources.json) | 检索配置、种子仓库、排除名单与精选资源 |
| [`scripts/update.py`](scripts/update.py) | 采集、排序、快照与 README 生成 |
| [`templates/README.zh.md`](templates/README.zh.md) / [`README.en.md`](templates/README.en.md) | 中英文静态模板；榜单由脚本插入 |
| [`data/latest.json`](data/latest.json) | 最近一次采集结果与来源状态 |
| `data/history/YYYY-MM-DD.json` | 按 UTC 日期保存的日快照 |
| [`assets/hero.svg`](assets/hero.svg) | 可编辑的矢量头图 |

请修改模板后运行 `python3 scripts/update.py --render-only`；直接修改生成的 README 会在下次更新时被覆盖。

</details>

<a id="methodology"></a>

## 🔎 来源与阅读方式

- **关注度不等于质量。** Stars、讨论分数和互动量用于发现内容，不代表模型效果、代码安全或官方认可；不同平台的指标不直接混排。
- **公开来源，有限覆盖。** 搜索词、平台索引、接口权限与请求限额都会影响收录；不能保证检索到全网内容，也不能证明收录项目已经“爆火”。来源故障与部分结果请结合榜单状态阅读。
- **自动发现需要校正。** 同名项目、误报、漏报与失效链接可能存在。可通过排除名单、精选资源和 Issue 修正。
- **保留原始上下文。** 数字与描述反映采集时的信息；完整内容、授权、价格及使用条件以原站为准。

<a id="contributing"></a>

## 🤝 一起完善 Jev 生态地图

欢迎提交项目、教程、文章、视频、模型页面或有价值的讨论。请附上可公开访问的原始链接，以及它与 Jev / TypeSafe AI 的具体关系。支持中文与英文内容。

**[提交资源 →](https://github.com/frontierlabai/JevHub/issues/new?template=resource.yml)** · **[阅读贡献指南 →](CONTRIBUTING.md)**

<p align="center">
  <sub>Built for curious builders. Powered by public sources and community contributions.</sub>
</p>
