# 数据方法 / Data methodology

JevHub 是 TypeSafe Jev 生态的公开资源目录。它按 GitHub 关注度帮助读者发现项目，不评估模型性能，也不宣称覆盖全网。所有配置见 [sources.json](../config/sources.json)。

## 发现与过滤

| 来源 | 自动发现范围 | 展示顺序 |
| --- | --- | --- |
| GitHub REST Search | 名称/描述、topic、README 组合关键词，以及最近 30 天更新的 Jev 仓库；每条 query 最多 2 页，每页 100 条；另补核验种子 | 项目榜按总 Star 降序；近期检索按更新时间发现新项目 |
| Hacker News Algolia | 发布以来匹配 Jev 的前 100 条 story，再按模型上下文过滤 | points 降序 |
| Reddit public JSON | 最近一个月检索结果前 100 条，再按 Jev 与 AI 上下文过滤 | score 降序 |
| Hugging Face API | Jev 关键词模型检索，按 likes 获取前 30 条 | likes 降序，downloads 作为同分排序 |
| Google News RSS | Jev + TypeSafe 的中英文公开新闻检索 | 各语言交替，保留来源内部顺序；无热度分数 |
| 精选资源 | 人工核验的官方入口、作者文章、视频元数据与讨论链接 | 编辑顺序 |

GitHub 搜索总数可能大于采集数；README 的“检索范围与数据状态”逐条列出实际数量。超过页数上限的结果不是抓取错误，但可能漏掉排名靠后的资源。近期检索通道按更新时间排序，专门补捉低 Star 但刚出现的仓库。API 返回 incomplete_results、搜索或种子请求失败时，整次 GitHub 更新失败，保留已提交数据。工作流保持失败状态，方便维护者发现问题。

名称或描述需要直接提及 Jev，且元数据中包含 AI、model、agent、decision、TypeSafe 等上下文；只有 Jev topic 不足以自动收录。仅名称命中但元数据不足的仓库，按 Star 顺序最多读取 12 份 README。人工核验种子补充名字中没有 Jev 的 SDK、集成和独立模型。排除 fork、归档、禁用、私有仓库以及排除名单。启发式相关性仍可能误报或漏报，欢迎提交修正。

项目类别首先采用人工覆盖值，再根据官方组织或关键词分类。独立复现不是 TypeSafe 官方模型权重；仓库描述是维护者的说明，不是 JevHub 对性能的背书。大型框架的 Star 属于整个框架，不应视为某个 Jev 集成的独立热度。

2026-09-22 的首批 Top 30 审查补充了五项排除记录：[anything_about_game](https://github.com/killop/anything_about_game) 的 README 没有 Jev 模型内容，普通词语 `typesafe` 指的是消息库；[Reticle](https://github.com/reticlehq/reticle) 将 Jev 集成列为未来计划，并明确表示尚未交付；[agent-beacon](https://github.com/Asymptote-Labs/agent-beacon)、[phi](https://github.com/pulseaiclub/phi) 和 [Crane](https://github.com/lucasjinreal/Crane) 的当前主分支 README 未提供 Jev 用途说明，只有相关 topic。后三项属于本次核验范围内的证据不足，并非断言仓库代码没有集成。此次审查核对仓库元数据与 README，没有执行或全面审计第三方代码；后续提供直接用途说明后可重新评估收录。

## Star 与时间

- GitHub Star 来自采集时的 stargazers_count；完整计数保存在 latest.json。
- 快照按 UTC 日期存为 data/history/YYYY-MM-DD.json。同一天再次成功更新会替换该日快照，保留最后一次采集。
- Star 只用于项目发现与排序，不用于计算增长榜，也不代表项目质量或官方认可。
- 最新时间记录在 `latest.json`；数据有采集耗时，不是同一瞬间的全局快照。

## 站外信号与降级

HN points、Reddit score、HF likes 与下载量按各平台原始定义分别展示，不换算成 GitHub Star。HF downloads 是平台统计的近 30 天下载量，不是独立用户人数。新闻检索没有经过验证的传播量，展示链接不表示新闻排名。

某站外源请求失败时，有缓存则展示旧缓存及上次成功时间，没有缓存则展示 unavailable。失败不会把数值重置为零，也不阻止成功的 GitHub 更新。Reddit 可能拒绝匿名请求；精选阅读区仍提供已核验的原帖入口。本站不绕过登录或访问限制。

精选资源只保存短标题、作者自述的内容主题和链接。视频仅核验公开元数据，不意味着完整观看或验证视频中的论断。新增精选内容请提供一手来源。

## 运行与维护

Python 3.11+，仅用标准库。请求超时 25 秒，瞬时错误最多尝试 3 次，每次等待最多 60 秒；GitHub token 仅发送给 api.github.com。搜索请求限速；本地无 token 时仍可能触及 GitHub 的匿名限额。

每天 UTC 01:17（北京时间 09:17）运行，支持 Actions 手动触发。首次推送到 main 后会运行更新。Fork 需要自行启用 Actions；工作流必须在默认分支，且仓库策略允许 bot 写入。分支保护可能阻止直接提交。GitHub 调度可能延迟，长期无活动的公开仓库可能被停用定时任务。

更新脚本先完成抓取和两份 README 渲染，再逐文件原子替换。GitHub 必需数据失败时不写任何产物；极端的磁盘写入失败仍可能导致本地文件不一致，可重跑恢复。GitHub Actions 只在前序步骤全部成功后提交产物。

修改模板或精选配置后，运行：

    python3 scripts/update.py --render-only
    python3 -m unittest discover -s tests -v
    python3 scripts/update.py --render-only --check

离线渲染不会更新快照时间，不会请求外网。CI 在 Python 3.11 / 3.13 上测试并检查 README 是否与已保存数据一致；它不验证当下的第三方网络可用性。

## Sources / API references

- [GitHub repository search](https://docs.github.com/en/rest/search/search#search-repositories)
- [GitHub scheduled workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)
- [Hacker News Search API](https://hn.algolia.com/api)
- [Hugging Face Hub API](https://huggingface.co/docs/hub/api)
- [Hugging Face download counting](https://huggingface.co/docs/hub/models-download-stats)

## English summary

This is bounded public discovery, not a web census or a performance ranking. GitHub queries fetch up to 200 repositories each, with reviewed seeds and relevance rules. Total stars belong to the entire repository. Independent implementations are distinguished from official TypeSafe projects.

The initial Top 30 review on 2026-09-22 excluded `anything_about_game` for unrelated README content and Reticle for a planned, unshipped Jev integration. `agent-beacon`, `phi`, and `Crane` were withheld because their current main-branch READMEs did not substantiate their Jev topics. This is a metadata and README evidence boundary, not a claim that their code contains no integration; listings can be reconsidered when direct usage documentation is available.

Repository stars are used as a discovery and sorting signal only; JevHub does not publish a star-growth leaderboard.

HN points, Reddit scores, and HF likes / trailing 30-day downloads stay separate. Google News results are discovery links without a reach metric. Optional-source failures retain timestamped caches; GitHub collection failures stop publication. The saved JSON records queries, coverage, evidence and source status. Offline rendering is deterministic and never changes collection timestamps.
