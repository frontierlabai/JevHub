# 参与 JevHub / Contributing

欢迎帮助大家发现有价值的 Jev / TypeSafe AI 资源。提交项目不要求达到某个 Star 数；清楚的关联、可访问的来源与有用的内容更重要。

## 推荐一个资源

最简单的方式是填写 [资源推荐表](https://github.com/frontierlabai/JevHub/issues/new?template=resource.yml)，提供原始链接、简短介绍，以及它与 Jev / System One 的具体关系。欢迎 SDK、工具、示例、教程、文章、视频和社区讨论。请注明你是否为作者或维护者。

收录范围是 TypeSafe AI 的 Jev 决策模型。同名个人账号、其他领域的 JEV 缩写及无关项目不在收录范围内。付费资源请说明访问条件；不要提交访问凭证或复制受限内容。

## 通过 Pull Request 修改目录

所有来源配置位于 [`config/sources.json`](config/sources.json)。沿用文件现有结构与分类，避免重复链接。

### 精选资源

在 `curated_resources` 数组中新增对象，填写以下字段：

| 字段 | 内容 |
| :--- | :--- |
| `title` | 中文标题；产品名可保留原文 |
| `title_en` | 英文标题 |
| `url` | 可公开访问的原始 HTTPS 链接 |
| `category` | 沿用配置中合适的现有分类 |
| `description` | 简短中文说明，交代内容与 Jev 的关系 |
| `description_en` | 对应的英文说明 |
| `language` | 内容语言，沿用配置中的语言写法 |

描述应可核验，避免“最强”“全网第一”等无来源宣传，也不要把第三方教程描述为官方资料。保留作者身份与原始出处，不把转载页优先于原文。

### GitHub 种子与排除名单

- `seed_repositories` 是 `owner/repository` 格式的字符串数组。适合补充自动搜索尚未找到的相关仓库。Star 数由采集器读取，不手动填写。
- `exclude_repositories` 也是 `owner/repository` 字符串数组。用于排除同名误报或无关仓库；在 PR 中简述排除原因。
- 修改搜索配置时，说明预期找到什么内容，并检查是否引入大量无关结果。

### 修改页面或采集器

中文首页模板是 [`templates/README.zh.md`](templates/README.zh.md)，英文模板是 [`templates/README.en.md`](templates/README.en.md)。两份模板都应保留唯一的 `{{DASHBOARD}}` 占位符，并保持主要说明一致。修改模板后重新生成页面；不要只修改会被下次任务覆盖的根目录 README。

运行环境为 Python 3.11+，无需第三方依赖。修改模板、精选资源或展示数量后，可以使用仓库已有快照离线重建并检查：

```bash
python3 scripts/update.py --render-only
python3 scripts/update.py --render-only --check
python3 -m unittest discover -s tests -v
```

`--render-only` 读取 `data/latest.json`，结合当前模板和精选配置生成 README，不发起网络请求、不修改采集时间。`--render-only --check` 只检查页面与生成结果是否一致，不修改文件。

修改检索词、种子、排除名单或采集逻辑后，用 `python3 scripts/update.py` 联网采集，再运行以上核验命令。仓库尚无 `data/latest.json` 时，也需要先完成一次联网采集。检查更新后的榜单和来源状态，确认链接、相关性、排序与描述符合预期。首次采集没有可比较的增长基线是正常情况，不应人为填充增长值。脚本或排序逻辑变更应附相关测试。

PR 中简要说明修改内容、来源链接和验证方式。自动生成的数据以真实采集为准，不添加模拟 Star 数或虚构的社区热度。

## 报告问题

发现误收录、漏收录、失效链接、翻译问题或异常排序，请在 [Issues](https://github.com/frontierlabai/JevHub/issues) 中说明页面位置和预期结果。接口故障请附不含敏感信息的错误信息与运行时间。

## English contribution guide

Use the [resource form](https://github.com/frontierlabai/JevHub/issues/new?template=resource.yml) to suggest a public resource, or open a PR editing [`config/sources.json`](config/sources.json). Explain its connection to TypeSafe AI's Jev / System One model and disclose whether you maintain it. There is no minimum star count.

Curated entries use `title`, `title_en`, `url`, `category`, `description`, `description_en`, and `language`. Follow existing category and language values. Use original source links and factual descriptions. Add GitHub repositories as `owner/repository` strings to `seed_repositories`; use `exclude_repositories` for unrelated matches and explain the exclusion.

Edit both README templates for static copy changes, retaining one `{{DASHBOARD}}` placeholder in each. Use `python3 scripts/update.py --render-only` for offline changes to templates, curated resources, and display limits; it reuses `data/latest.json` and preserves collection timestamps. Run `python3 scripts/update.py --render-only --check` to check consistency without writing files, plus the tests above with Python 3.11+.

Changes to queries, seeds, exclusions, or collection logic need a live `python3 scripts/update.py` run. A live run is also required if no saved snapshot exists. Review generated content and source status before submitting. Never invent stars, growth, or discussion metrics, and never commit access tokens.
