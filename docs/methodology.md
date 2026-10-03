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
| arXiv API | Jev 爆火起始日之后的 Jev、System One 与 decision 论文和预印本；多个发现条件合并查询，每页 100 条，分页至完成 | 按 submitted date 倒序；保留全部已收录论文，不受 community_limit 限制 |
| 精选资源 | 人工核验的官方入口、作者文章、视频元数据与讨论链接 | 编辑顺序 |

GitHub 搜索总数可能大于采集数；README 的“检索范围与数据状态”逐条列出实际数量。超过页数上限的结果不是抓取错误，但可能漏掉排名靠后的资源。近期检索通道按更新时间排序，专门补捉低 Star 但刚出现的仓库。API 返回 incomplete_results、搜索或种子请求失败时，整次 GitHub 更新失败，保留已提交数据。工作流保持失败状态，方便维护者发现问题。

名称或描述需要直接提及 Jev，且元数据中包含 AI、model、agent、decision、TypeSafe 等上下文；只有 Jev topic 不足以自动收录。仅名称命中但元数据不足的仓库，按 Star 顺序最多读取 12 份 README。人工核验种子补充名字中没有 Jev 的 SDK、集成和独立模型。排除 fork、归档、禁用、私有仓库以及排除名单。启发式相关性仍可能误报或漏报，欢迎提交修正。

项目类别首先采用人工覆盖值，再根据官方组织或关键词分类。独立复现不是 TypeSafe 官方模型权重；仓库描述是维护者的说明，不是 JevHub 对性能的背书。大型框架的 Star 属于整个框架，不应视为某个 Jev 集成的独立热度。

2026-09-22 的首批 Top 30 审查补充了五项排除记录：[anything_about_game](https://github.com/killop/anything_about_game) 的 README 没有 Jev 模型内容，普通词语 `typesafe` 指的是消息库；[Reticle](https://github.com/reticlehq/reticle) 将 Jev 集成列为未来计划，并明确表示尚未交付；[agent-beacon](https://github.com/Asymptote-Labs/agent-beacon)、[phi](https://github.com/pulseaiclub/phi) 和 [Crane](https://github.com/lucasjinreal/Crane) 的当前主分支 README 未提供 Jev 用途说明，只有相关 topic。后三项属于本次核验范围内的证据不足，并非断言仓库代码没有集成。此次审查核对仓库元数据与 README，没有执行或全面审计第三方代码；后续提供直接用途说明后可重新评估收录。

## 全部论文与新增记录

网页与中英文 README 默认展示前 4 篇，可展开查看全部已收录论文，沿用 `arxiv_since` 与 Jev 相关性规则；不再截取最新 8 篇。每次抓取完整查询范围，合并历史记录；暂时未被搜索返回的论文仍保留。按不带版本号的 arXiv ID 去重，统一 HTTPS 链接，v2/v3 修订不作为新论文。

“本次新增”指此次成功抓取中、历史上从未收录过的论文，保存在 `arxiv_update.ids`，网页与 README 据此标记。`first_seen_at` 是首次收录时间，不是论文提交日期。重复运行无新记录时新增为 0；抓取失败时保留旧论文，清除本次新增标记并显示抓取不可用，不把旧记录伪装成新增。分页中途失败、重复页面或 API 错误 feed 均按失败处理。

迁移时从 Git 历史恢复了 41 篇曾收录的论文，再与完整抓取结果合并，避免把原来被 8 篇上限隐藏的论文重新算作新增。新补录的早期论文可以计入新增收录，与论文发表日期无关。

项目简报同样对比历史记录：`recorded_repository_ids` 累计保存不可变的 GitHub 仓库 ID，并合并 `data/history`。改名、Star 变化、退出搜索后重新出现均不会再次计为新增。迁移时也恢复了日内 Git 提交中曾记录的仓库 ID。

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

Python 3.11+，仅用标准库。请求超时 25 秒，瞬时错误最多尝试 3 次，每次等待最多 60 秒；GitHub token 仅发送给 api.github.com。GitHub 搜索请求限速；连续 arXiv API 请求至少间隔 3 秒，遇到其限流使用的 HTTP 406 时自动冷却重试。本地无 token 时仍可能触及 GitHub 的匿名限额。

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

All recorded arXiv papers are retained and displayed on the website and in both READMEs. Pagination completes before publishing; failures preserve the archive. New additions use version-independent IDs against the entire archive, not publication dates. Repository briefs likewise compare immutable IDs against all recorded history.

HN points, Reddit scores, HF likes / trailing 30-day downloads, and arXiv papers stay separate. Google News results are discovery links without a reach metric. Optional-source failures retain timestamped caches; GitHub collection failures stop publication. The saved JSON records queries, coverage, evidence and source status. Offline rendering is deterministic and never changes collection timestamps.
