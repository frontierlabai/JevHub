<p align="center">
  <img src="assets/hero.svg" alt="JevHub: discover Jev projects daily and track GitHub stars and community activity" width="1200">
</p>

<h1 align="center">JevHub · The Jev ecosystem, in view.</h1>

<p align="center">
  <strong>Projects, guides, and conversations worth following. In one place.</strong><br>
  Automated discovery · Daily refresh · Ranked by stars · 中文 / English
</p>

<p align="center">
  <a href="https://github.com/frontierlabai/JevHub/actions/workflows/refresh.yml"><img src="https://github.com/frontierlabai/JevHub/actions/workflows/refresh.yml/badge.svg" alt="Daily refresh workflow status"></a>
  <a href="https://github.com/frontierlabai/JevHub/stargazers"><img src="https://img.shields.io/github/stars/frontierlabai/JevHub?style=flat&amp;color=6ee7b7" alt="Star JevHub"></a>
  <a href="#automation"><img src="https://img.shields.io/badge/refresh-daily%20%C2%B7%2001%3A17%20UTC-67e8f9?style=flat" alt="Scheduled daily at 01:17 UTC"></a>
  <a href="https://docs.typesafe.ai/"><img src="https://img.shields.io/badge/explore-Jev%20%2F%20System%20One-c4b5fd?style=flat" alt="Official Jev documentation"></a>
</p>

<p align="center">
  <a href="README.md">简体中文</a> · <strong>English</strong><br>
  <a href="#github-ranking">Featured projects</a> · <a href="#community-radar">Community radar</a> · <a href="#curated-resources">Curated resources</a> · <a href="#getting-started">Get started</a>
</p>

> **Which Jev?** This directory covers **Jev / System One**, the model from [TypeSafe AI](https://typesafe.ai/) that provides structured decisions for software. JevHub is an independent community directory and is not affiliated with TypeSafe AI. [Meet Jev →](https://docs.typesafe.ai/introduction)

{{DASHBOARD}}

<a id="getting-started"></a>

## 🚀 Start exploring

| What would you like to do? | Start here |
| :--- | :--- |
| Understand Jev and System One | [Official introduction](https://docs.typesafe.ai/introduction) · [TypeSafe AI](https://typesafe.ai/) |
| Integrate Jev and explore its API | [Official documentation](https://docs.typesafe.ai/) |
| Find SDKs, examples, and community projects | [Featured projects](#github-ranking) · [Curated resources](#curated-resources) |
| Follow emerging projects and discussions | [Featured projects](#github-ranking) · [Community radar](#community-radar) |
| Recommend a useful resource | [Submit a resource](https://github.com/frontierlabai/JevHub/issues/new?template=resource.yml) · [Contributing guide](CONTRIBUTING.md) |

<a id="share"></a>

## 💚 Help useful work travel

**Star the repository** to keep it handy, or share it with someone exploring Jev. Link to this directory in your articles, videos, and communities, and keep the original resource links when citing their work.

[Share on X](https://twitter.com/intent/tweet?text=JevHub%20%E2%80%94%20a%20daily%20radar%20for%20the%20Jev%20ecosystem.%20Projects%2C%20GitHub%20stars%2C%20and%20community%20discussions.&url=https%3A%2F%2Fgithub.com%2Ffrontierlabai%2FJevHub) · [Share on LinkedIn](https://www.linkedin.com/sharing/share-offsite/?url=https%3A%2F%2Fgithub.com%2Ffrontierlabai%2FJevHub) · [Recommend a resource](https://github.com/frontierlabai/JevHub/issues/new?template=resource.yml)

Share this link: **https://github.com/frontierlabai/JevHub**

<a id="automation"></a>

## ⚙️ How daily updates work

Once the workflow is on the repository's default branch and GitHub Actions is enabled, updates are scheduled for **01:17 UTC / 09:17 Beijing time** every day. You can also trigger an update from the [Actions page](https://github.com/frontierlabai/JevHub/actions/workflows/refresh.yml). Scheduled runs may be delayed; use the collection timestamp shown in the dashboard.

1. Discover public content using the search configuration in [`config/sources.json`](config/sources.json), plus seed repositories and curated links.
2. Fetch GitHub metadata and show the top 30 repositories by total stars, keeping the project context front and center.
3. Collect public results from Hacker News, Reddit, and Hugging Face, then render the Chinese and English READMEs.
4. Save [`data/latest.json`](data/latest.json) and `data/history/YYYY-MM-DD.json` for inspection and future comparisons.

Run locally with **Python 3.11+**. No third-party dependencies are required:

```bash
git clone https://github.com/frontierlabai/JevHub.git
cd JevHub
python3 scripts/update.py
python3 -m unittest discover -s tests -v
```

For changes to templates, curated resources, or display limits, reuse the existing `data/latest.json` without network access:

```bash
python3 scripts/update.py --render-only
python3 scripts/update.py --render-only --check
```

`--render-only` rebuilds both READMEs. Adding `--check` verifies that the generated content matches without writing files. Offline rendering preserves the collection timestamp and does not refresh stars. Run a live update after changing search queries, seeds, or exclusions.

For your own fork, make sure the workflow is on the default branch, Actions is enabled, and the workflow can write repository contents. See [`.github/workflows/refresh.yml`](.github/workflows/refresh.yml). For more frequent local searches, supply a GitHub token through the `GITHUB_TOKEN` environment variable; keep tokens out of configuration files and commits.

<details>
<summary><strong>Maintenance and file guide</strong></summary>

| File | Purpose |
| :--- | :--- |
| [`config/sources.json`](config/sources.json) | Search configuration, seed repositories, exclusions, and curated resources |
| [`scripts/update.py`](scripts/update.py) | Collection, ranking, snapshots, and README generation |
| [`templates/README.zh.md`](templates/README.zh.md) / [`README.en.md`](templates/README.en.md) | Static templates; the script inserts the dashboard |
| [`data/latest.json`](data/latest.json) | Latest collection results and source status |
| `data/history/YYYY-MM-DD.json` | Daily snapshots keyed by UTC date |
| [`assets/hero.svg`](assets/hero.svg) | Editable vector header |

Edit the templates and run `python3 scripts/update.py --render-only`. Direct edits to generated READMEs will be replaced on the next update.

</details>

<a id="methodology"></a>

## 🔎 Sources and interpretation

- **Attention is not quality.** Stars, discussion scores, and interactions help surface content. They do not establish model performance, code safety, or official endorsement. Metrics from different platforms are not ranked together.
- **Public sources have limited coverage.** Search terms, indexing, access permissions, and rate limits affect discovery. This directory cannot cover the entire web or establish that an item has gone viral. Check source status for failures or partial results.
- **Discovery needs correction.** Unrelated names, false matches, missing projects, and stale links can occur. Exclusions, curated resources, and issue reports help improve the results.
- **Keep the original context.** Counts and descriptions reflect information at collection time. Visit the original source for full content, licensing, pricing, and terms of use.

<a id="contributing"></a>

## 🤝 Help map the Jev ecosystem

Recommend a project, tutorial, article, video, model page, or useful discussion. Include a public original link and explain its connection to Jev / TypeSafe AI. Chinese and English resources are welcome.

**[Submit a resource →](https://github.com/frontierlabai/JevHub/issues/new?template=resource.yml)** · **[Read the contributing guide →](CONTRIBUTING.md)**

<p align="center">
  <sub>Built for curious builders. Powered by public sources and community contributions.</sub>
</p>
