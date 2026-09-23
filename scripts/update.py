#!/usr/bin/env python3
"""Discover public Jev resources and generate bilingual READMEs. Standard library only."""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timedelta, timezone
import html
import json
import os
from pathlib import Path
import re
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
JEV = re.compile(r"(?<![a-z])(?:jev|nanojev|openjev|jevlike|jevify)(?![a-z])", re.I)
CONTEXT = re.compile(r"typesafe|system[ -]one|\bAI\b|\bLLM\b|agent|model|decision|classifier|inference|scoring|routing|模型|决策|智能|复现", re.I)
UNRELATED = re.compile(r"encephalitis|flavivirus|jevons|faze\s+jev|乙型脑炎", re.I)
REPO_NAME = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")


def stamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def relevant(text):
    return bool(JEV.search(text) and CONTEXT.search(text) and not UNRELATED.search(text))


def safe_url(url):
    p = urlparse(str(url))
    if p.scheme not in {"https", "http"} or not p.netloc or p.username:
        return ""
    return quote(str(url), safe=":/?&=%#@+~,;!$*-")


def cell(value, limit=150):
    text = " ".join(str("—" if value is None or value == "" else value).split())
    if len(text) > limit:
        text = text[:limit - 1] + "…"
    text = html.escape(text, quote=False)
    for char in "\\" + chr(96) + "*_[]|":
        text = text.replace(char, "\\" + char)
    return text


def link(title, url):
    return f"[{cell(title)}]({safe_url(url)})" if safe_url(url) else cell(title)


class FetchError(RuntimeError):
    pass


class Client:
    def __init__(self, token=""):
        self.token = token
        self.last_search = 0.0

    def get(self, url, *, raw=False):
        headers = {"User-Agent": "JevHub/1.0 (+https://github.com/frontierlabai/JevHub)"}
        if urlparse(url).hostname == "api.github.com":
            headers.update({"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"})
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
            if "/search/" in url:
                time.sleep(max(0, 6.2 - (time.monotonic() - self.last_search)))
                self.last_search = time.monotonic()
        for attempt in range(3):
            try:
                with urlopen(Request(url, headers=headers), timeout=25) as response:
                    body = response.read(8_000_001)
                    if len(body) > 8_000_000:
                        raise FetchError("response exceeds 8 MB")
                    return body.decode("utf-8") if raw else json.loads(body)
            except HTTPError as error:
                retryable = error.code in {429, 500, 502, 503, 504} or (
                    error.code == 403 and (error.headers.get("X-RateLimit-Remaining") == "0" or error.headers.get("Retry-After")))
                if not retryable or attempt == 2:
                    raise FetchError(f"HTTP {error.code}") from error
                delay = min(60, max(2 ** attempt, int(error.headers.get("Retry-After", "0"))))
                if error.headers.get("X-RateLimit-Reset"):
                    delay = min(60, max(delay, int(error.headers["X-RateLimit-Reset"]) - time.time() + 1))
                time.sleep(delay)
            except (URLError, TimeoutError, OSError) as error:
                if attempt == 2:
                    raise FetchError(type(error).__name__) from error
                time.sleep(2 ** attempt)
            except (ValueError, UnicodeError) as error:
                raise FetchError("invalid response") from error


def category(repo, config):
    name = repo["full_name"]
    override = {k.lower(): v for k, v in config.get("repository_overrides", {}).items()}.get(name.lower(), {})
    if override.get("category"):
        return override["category"]
    if name.split("/")[0].lower() in config["official_owners"]:
        return "official"
    text = (name + " " + (repo.get("description") or "")).lower()
    for label, terms in (
        ("research", ("replica", "jev-like", "alternative", "open model", "nanojev", "reimplement", "复现")),
        ("resources", ("awesome", "curated", "resource", "collection")),
        ("tools", ("sdk", "client", "cli", "mcp", "router", "routing", "skill", "plugin"))):
        if any(t in text for t in terms):
            return label
    return "applications"


def collect_github(client, config):
    found, queries, errors, readme_checks = {}, [], [], 0
    excluded = {x.lower() for x in config["exclude_repositories"]}
    seeds = {x.lower() for x in config["seed_repositories"]}
    recent_since = (datetime.now(timezone.utc) - timedelta(days=config.get("github_recent_days", 30))).date().isoformat()
    search_specs = [(query, "stars") for query in config["github_queries"]]
    search_specs += [(query.replace("{recent_since}", recent_since), "updated")
                     for query in config.get("github_recent_queries", [])]
    for query, sort in search_specs:
        count, total, incomplete = 0, 0, False
        for page in range(1, config["github_pages_per_query"] + 1):
            url = "https://api.github.com/search/repositories?" + urlencode({
                "q": query, "sort": sort, "order": "desc", "per_page": 100, "page": page})
            try:
                data = client.get(url)
                total = data["total_count"]
                incomplete = incomplete or data.get("incomplete_results", False)
                for repo in data["items"]:
                    found[repo["full_name"].lower()] = repo
                count += len(data["items"])
                if len(data["items"]) < 100:
                    break
            except (FetchError, KeyError, TypeError) as error:
                errors.append(f"search {query}: {error}")
                break
        queries.append({"query": query, "sort": sort, "returned": count, "total": total,
                        "truncated": total > count, "incomplete": incomplete})
    for name in config["seed_repositories"]:
        if name.lower() in found or name.lower() in excluded:
            continue
        try:
            found[name.lower()] = client.get("https://api.github.com/repos/" + name)
        except FetchError as error:
            errors.append(f"repo {name}: {error}")
    rows, seen_ids = [], set()
    for repo in sorted(found.values(), key=lambda x: (-x.get("stargazers_count", 0), x.get("full_name", ""))):
        name = repo["full_name"]
        if (not REPO_NAME.fullmatch(name) or name.lower() in excluded or repo.get("fork")
                or repo.get("archived") or repo.get("disabled") or repo.get("private")
                or repo["id"] in seen_ids):
            continue
        metadata = " ".join([name, repo.get("description") or "", " ".join(repo.get("topics", []))])
        official = name.split("/")[0].lower() in config["official_owners"]
        # A generic repository with an opportunistic "jev" topic is not enough.
        direct_mention = JEV.search(name + " " + (repo.get("description") or ""))
        accepted = name.lower() in seeds or (direct_mention and relevant(metadata)) or official
        evidence = "reviewed seed" if name.lower() in seeds else ("official organization" if official else "repository metadata")
        if not accepted and JEV.search(name.split("/")[1]) and not UNRELATED.search(metadata) and readme_checks < config["readme_checks"]:
            readme_checks += 1
            try:
                data = client.get(f"https://api.github.com/repos/{name}/readme")
                readme = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
                accepted, evidence = relevant(readme), "repository README"
            except (FetchError, KeyError, ValueError):
                pass
        if not accepted:
            continue
        seen_ids.add(repo["id"])
        override = {k.lower(): v for k, v in config.get("repository_overrides", {}).items()}.get(name.lower(), {})
        rows.append({"id": repo["id"], "name": name, "url": "https://github.com/" + name,
                     "description": override.get("description", repo.get("description") or "暂无简介；可打开仓库查看"),
                     "description_en": override.get("description_en", repo.get("description") or "No description; open the repository for details"),
                     "stars": repo["stargazers_count"], "forks": repo.get("forks_count", 0),
                     "language": repo.get("language") or "—", "category": category(repo, config),
                     "pushed_at": repo.get("pushed_at"), "evidence": evidence})
    if errors or any(q["incomplete"] for q in queries) or not rows:
        raise FetchError("GitHub collection incomplete; previous files preserved. " + "; ".join(errors[:8]))
    return rows, {"state": "ok", "fetched_at": stamp(), "count": len(rows), "queries": queries,
                  "candidate_count": len(found), "readme_checks": readme_checks}


def collect_hn(client, config):
    data = client.get("https://hn.algolia.com/api/v1/search?" + urlencode({
        "query": "jev", "tags": "story", "hitsPerPage": 100,
        "numericFilters": "created_at_i>=" + str(int(datetime.fromisoformat(config["launched_at"]).timestamp()))}))
    rows = []
    for hit in data["hits"]:
        title = hit.get("title") or ""
        if relevant(title + " " + (hit.get("url") or "") + " " + (hit.get("story_text") or "")):
            rows.append({"title": title, "url": "https://news.ycombinator.com/item?id=" + hit["objectID"],
                         "original_url": safe_url(hit.get("url") or ""), "score": hit.get("points") or 0,
                         "comments": hit.get("num_comments") or 0, "published_at": hit.get("created_at")})
    return sorted(rows, key=lambda x: (-x["score"], x["url"]))[:config["community_limit"]]


def collect_reddit(client, config):
    data = client.get("https://www.reddit.com/search.json?" + urlencode({
        "q": "Jev (TypeSafe OR model OR AI)", "sort": "top", "t": "month", "limit": 100, "raw_json": 1}))
    rows = []
    for item in data["data"]["children"]:
        hit = item["data"]
        if relevant(hit["title"] + " " + hit.get("selftext", "")):
            rows.append({"title": hit["title"], "url": "https://www.reddit.com" + hit["permalink"],
                         "score": hit["score"], "comments": hit["num_comments"], "community": hit["subreddit"]})
    return sorted(rows, key=lambda x: (-x["score"], x["url"]))[:config["community_limit"]]


def collect_huggingface(client, config):
    data = client.get("https://huggingface.co/api/models?" + urlencode({
        "search": "jev", "sort": "likes", "direction": -1, "limit": 30, "full": "true"}))
    rows = []
    for model in data:
        metadata = model["id"] + " " + " ".join(model.get("tags", []))
        if JEV.search(model["id"].split("/")[-1]) and not UNRELATED.search(metadata):
            rows.append({"title": model["id"], "url": "https://huggingface.co/" + model["id"],
                         "likes": model.get("likes", 0), "downloads": model.get("downloads", 0),
                         "pipeline": model.get("pipeline_tag", "—")})
    return sorted(rows, key=lambda x: (-x["likes"], -x["downloads"], x["title"]))[:config["community_limit"]]


def collect_news(client, config):
    feeds = []
    for feed in config["news_feeds"]:
        xml = client.get(feed, raw=True)
        rows = []
        for item in ET.fromstring(xml).findall("./channel/item"):
            title, url = item.findtext("title", ""), item.findtext("link", "")
            if relevant(title) and safe_url(url):
                rows.append({"title": title, "url": url, "publisher": item.findtext("source", ""),
                             "published_at": item.findtext("pubDate", "")})
        feeds.append(rows)
    # Interleave configured languages so the first feed cannot hide all other languages.
    combined = {}
    for index in range(max((len(rows) for rows in feeds), default=0)):
        for rows in feeds:
            if index < len(rows):
                combined.setdefault(rows[index]["url"], rows[index])
    return list(combined.values())[:config["community_limit"]]


def collect_arxiv(client, config):
    """Collect recent papers and preprints that mention Jev in an AI context."""
    atom = "{http://www.w3.org/2005/Atom}"
    rows = {}
    since = datetime.fromisoformat(config.get("arxiv_since") or config.get("launched_at", stamp()[:10])).strftime("%Y%m%d0000")
    until = datetime.now(timezone.utc).strftime("%Y%m%d2359")
    for query in config.get("arxiv_queries", []):
        dated_query = f"({query}) AND submittedDate:[{since} TO {until}]"
        url = "https://export.arxiv.org/api/query?" + urlencode({
            "search_query": dated_query, "start": 0, "max_results": 25,
            "sortBy": "submittedDate", "sortOrder": "descending"})
        root = ET.fromstring(client.get(url, raw=True))
        for entry in root.findall(f"{atom}entry"):
            title = " ".join((entry.findtext(f"{atom}title", "") or "").split())
            summary = " ".join((entry.findtext(f"{atom}summary", "") or "").split())
            paper_url = entry.findtext(f"{atom}id", "")
            if not title or not safe_url(paper_url) or not relevant(title + " " + summary):
                continue
            authors = [name.text.strip() for name in entry.findall(f"{atom}author/{atom}name") if name.text]
            rows[paper_url] = {"title": title, "url": paper_url, "summary": summary,
                               "authors": authors, "published_at": entry.findtext(f"{atom}published", "")}
    return sorted(rows.values(), key=lambda row: row.get("published_at", ""), reverse=True)[:config["community_limit"]]


def load_json(path, default=None):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def hydrate_daily_brief(data):
    """Recover a brief for older snapshots before the field was introduced."""
    if "daily_brief" in data:
        return data
    current_day = data.get("generated_at", "")[:10]
    history_dir = ROOT / "data" / "history"
    snapshots = sorted(history_dir.glob("*.json")) if history_dir.exists() else []
    prior = None
    for path in snapshots:
        if path.stem < current_day:
            candidate = load_json(path)
            if candidate and candidate.get("date") == path.stem:
                prior = candidate
    if not prior:
        return data
    previous_ids = {str(row.get("id")) for row in prior.get("repositories", [])}
    new_repositories = [row for row in data.get("repositories", []) if str(row.get("id")) not in previous_ids]
    hydrated = dict(data)
    hydrated["daily_brief"] = {"count": len(new_repositories), "repositories": new_repositories[:8]}
    return hydrated


LABELS = {
    "official": ("官方项目", "Official"), "research": ("独立复现 / 研究", "Independent research"),
    "resources": ("资源合集", "Resources"), "tools": ("开发工具", "Tools"),
    "applications": ("应用 / 集成", "Apps / integrations")}


def dashboard(data, english=False):
    def tr(zh, en):
        return en if english else zh
    repos, sources = data["repositories"], data["sources"]
    total = sum(r["stars"] for r in repos)
    brief = data.get("daily_brief", {})
    new_repos = brief.get("repositories", [])
    if "daily_brief" not in data:
        brief_line = tr("每日简报将在下一次成功刷新后生成。", "The daily brief will appear after the next successful refresh.")
    elif new_repos:
        brief_line = (tr("本次发现 ", "This refresh found ") + str(brief.get("count", len(new_repos))) +
                      tr(" 个新项目：", " new project(s): ") + "；".join(link(r["name"], r["url"]) for r in new_repos))
    else:
        brief_line = tr("本次没有发现新增项目。", "No new projects were found in this refresh.")
    lines = [
        f"> {tr('更新于', 'Updated')} **{data['generated_at']}** · **{len(repos)}** {tr('个相关仓库', 'related repositories')} · **{total:,}** {tr('个累计 Star', 'total repository stars')}",
        "", tr("仓库 Star 包含其全部功能获得的关注，不等于 Jev 功能的热度；以下为检索范围内的结果。",
               "Repository stars cover all features, not just Jev. Rankings cover the configured search scope."),
        "", '<a id="daily-brief"></a>', "", tr("## 🆕 今日新增", "## 🆕 New today"), "",
        brief_line,
        "", '<a id="github-ranking"></a>', "", tr("## 🔥 项目精选", "## 🔥 Featured projects"), "",
        tr("按当前 Star 总数降序排列；同分按仓库名排序。先看项目，再看热度与一句话介绍。",
           "Sorted by total stars, with repository name as the tie-breaker. Start with the projects, then scan their signals and context."), "",
        tr("| 项目 | 类别 | ⭐ Stars | 一句话介绍 |",
           "| Project | Category | ⭐ Stars | About |"),
        "| :-- | :-- | --: | :-- |"]
    for rank, repo in enumerate(repos[:data["limits"]["repositories"]], 1):
        badge = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, str(rank))
        label = LABELS.get(repo["category"], (repo["category"], repo["category"]))[english]
        desc = repo["description_en"] if english else repo["description"]
        lines.append(f"| {badge} {link(repo['name'], repo['url'])} | {label} | **{repo['stars']:,}** | {cell(desc, 100)} |")
    lines += [
        "", tr("> 💡 排名按项目当前 Star 总数更新；Star 只作为发现信号，不代表项目质量或官方认可。",
               "> 💡 Rankings use current repository stars as a discovery signal, not as a proxy for quality or official endorsement."),
        "", '<a id="community-radar"></a>', "", tr("## 🌐 站外发现与讨论", "## 🌐 Beyond GitHub"), "",
        tr("各平台独立展示：HN points、Reddit score、Hugging Face likes / 近 30 天 downloads 不混算成 Star。新闻是检索发现，未验证传播量。",
           "Platform signals stay separate: HN points, Reddit scores, and Hugging Face likes / trailing 30-day downloads are not GitHub stars. News is discovery, with no verified reach metric.")]
    for name, title in (("hacker_news", "Hacker News"), ("reddit", "Reddit"), ("huggingface", "Hugging Face"), ("news", tr("新闻 / 文章", "News / articles")), ("arxiv", "arXiv")):
        status = sources.get(name, {"state": "unavailable", "fetched_at": None})
        state = {"ok": tr("已更新", "updated"), "stale": tr("旧缓存", "stale cache"),
                 "unavailable": tr("暂不可用", "unavailable")}[status["state"]]
        lines += ["", f"### {title}", "", f"{state} · {tr('最近成功抓取', 'Last successful fetch')}: {status.get('fetched_at') or '—'}", ""]
        if status.get("error"):
            lines += [f"> {cell(status['error'])}", ""]
        rows = data.get(name, [])
        if not rows:
            lines.append(tr("本次没有可展示的相关结果。", "No relevant results available for this snapshot."))
        elif name == "huggingface":
            lines += [tr("社区上传 / 独立实现；不代表 TypeSafe 官方模型权重。",
                         "Community uploads / independent implementations; not official TypeSafe model weights."), "",
                      "| Model | ♥ Likes | ↓ Downloads (30d) |", "| :-- | --: | --: |"]
            lines += [f"| {link(r['title'], r['url'])} | {r['likes']:,} | {r['downloads']:,} |" for r in rows]
        elif name == "arxiv":
            lines += [tr("论文与预印本；仅作为发现入口，不代表同行评审或官方关联。",
                         "Papers and preprints for discovery; not a peer-review or official-affiliation claim."), "",
                      tr("| 论文 | 作者 | 提交时间 |", "| Paper | Authors | Submitted |"), "| :-- | :-- | :-- |"]
            lines += [f"| {link(r['title'], r['url'])} | {cell(', '.join(r.get('authors', [])) or '—', 70)} | {cell(r.get('published_at', '')[:10])} |" for r in rows]
        elif name == "news":
            lines += [f"- {link(r['title'], r['url'])}" for r in rows]
        else:
            lines += [f"| {tr('讨论', 'Discussion')} | {'Points' if name == 'hacker_news' else 'Score'} | {tr('评论', 'Comments')} |", "| :-- | --: | --: |"]
            lines += [f"| {link(r['title'], r['url'])} | {r['score']:,} | {r['comments']:,} |" for r in rows]
    lines += [
        "", '<a id="curated-resources"></a>', "", tr("## 💎 精选阅读与入口", "## 💎 Curated reading & starting points"), "",
        tr("人工核验入口，自动重建展示；不为这些链接编造热度。",
           "Manually reviewed sources, rendered automatically. No invented popularity scores."), "",
        tr("| 资源 | 类型 | 语言 | 看点 |", "| Resource | Type | Language | Why open it |"),
        "| :-- | :-- | :-- | :-- |"]
    for resource in data["curated_resources"]:
        title = resource.get("title_en", resource["title"]) if english else resource["title"]
        desc = resource.get("description_en", resource["description"]) if english else resource["description"]
        types = {"official": ("官方", "Official"), "integration": ("集成", "Integration"),
                 "article": ("文章", "Article"), "video": ("视频", "Video"),
                 "discussion": ("讨论", "Discussion"), "research": ("研究", "Research")}
        kind = types.get(resource["category"], (resource["category"], resource["category"]))[english]
        lines.append(f"| {link(title, resource['url'])} | {cell(kind)} | {cell(resource['language'])} | {cell(desc)} |")
    lines += [
        "", "<details>", f"<summary>{tr('查看检索范围与数据状态', 'Search coverage & data status')}</summary>", "",
        tr("GitHub 每条 query 按 Star 降序取配置页数；这是有界检索，不是全站普查。fork、归档、明确无关项被排除，相关性采用元数据 / README 规则和核验种子。",
           "Each GitHub query fetches a configured number of pages sorted by stars. This is bounded search, not a census. Forks, archived and unrelated repositories are excluded using metadata / README rules and reviewed seeds."), ""]
    for query in sources["github"]["queries"]:
        lines.append(f"- {cell(query['query'])} — {query['returned']} / {query['total']}" +
                     (tr("（达到页数上限）", " (page cap reached)") if query["truncated"] else ""))
    lines += [
        "", tr("完整结果与时间戳：[JSON 数据](data/latest.json) · [历史快照](data/history) · [方法说明](docs/methodology.md)",
               "Full results and timestamps: [JSON data](data/latest.json) · [History](data/history) · [Methodology](docs/methodology.md)"),
        "", "</details>"]
    return "\n".join(lines)


def render(data):
    outputs = {}
    for language, filename in (("zh", "README.md"), ("en", "README.en.md")):
        template = (ROOT / "templates" / f"README.{language}.md").read_text(encoding="utf-8")
        if template.count("{{DASHBOARD}}") != 1:
            raise ValueError("README template must contain exactly one {{DASHBOARD}}")
        outputs[ROOT / filename] = template.replace("{{DASHBOARD}}", dashboard(data, language == "en"))
    return outputs


def write_atomic(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)


def json_text(data):
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def validate_config(config):
    for name in config["seed_repositories"] + config["exclude_repositories"]:
        if not REPO_NAME.fullmatch(name):
            raise ValueError(f"Invalid repository name: {name}")
    if not 1 <= config["github_pages_per_query"] <= 10:
        raise ValueError("GitHub pages must be between 1 and 10")
    for resource in config["curated_resources"]:
        if not safe_url(resource["url"]):
            raise ValueError("Invalid resource URL")


def refresh(config, previous, client):
    print("Collecting GitHub repositories...", flush=True)
    repos, github_status = collect_github(client, config)
    repos.sort(key=lambda r: (-r["stars"], r["name"].lower()))
    previous_ids = {str(row.get("id")) for row in previous.get("repositories", [])}
    new_repositories = [row for row in repos if str(row["id"]) not in previous_ids]
    data = {"schema_version": 1, "generated_at": stamp(), "repositories": repos,
            "sources": {"github": github_status}, "curated_resources": config["curated_resources"],
            "limits": {"repositories": config["readme_limit"]},
            "daily_brief": {"count": len(new_repositories),
                            "repositories": new_repositories[:8]}}
    for name, collector in (("hacker_news", collect_hn), ("reddit", collect_reddit),
                            ("huggingface", collect_huggingface), ("news", collect_news),
                            ("arxiv", collect_arxiv)):
        print(f"Collecting {name}...", flush=True)
        try:
            data[name] = collector(client, config)
            data["sources"][name] = {"state": "ok", "fetched_at": stamp(), "count": len(data[name])}
        except (FetchError, KeyError, TypeError, ValueError, ET.ParseError) as error:
            data[name] = previous.get(name, [])
            prior_status = previous.get("sources", {}).get(name, {})
            data["sources"][name] = {"state": "stale" if data[name] else "unavailable",
                "fetched_at": prior_status.get("fetched_at"), "attempted_at": stamp(), "count": len(data[name]),
                "error": f"{type(error).__name__}: {error}"}
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--render-only", action="store_true", help="Render committed data without network requests")
    parser.add_argument("--check", action="store_true", help="With --render-only, fail if READMEs differ")
    args = parser.parse_args()
    if args.check and not args.render_only:
        parser.error("--check requires --render-only")
    config = load_json(ROOT / "config/sources.json")
    validate_config(config)
    previous = load_json(ROOT / "data/latest.json", {})
    if args.render_only:
        if not previous:
            raise ValueError("No data/latest.json; run a live update first")
        data = dict(previous, curated_resources=config["curated_resources"], limits={"repositories": config["readme_limit"]})
    else:
        data = refresh(config, previous, Client(os.environ.get("GITHUB_TOKEN", "")))
    data = hydrate_daily_brief(data)
    outputs = render(data)  # Validate every template before any persistent writes.
    if args.check:
        mismatches = [str(p.relative_to(ROOT)) for p, content in outputs.items()
                      if not p.exists() or p.read_text(encoding="utf-8") != content]
        if mismatches:
            print("Generated files out of date: " + ", ".join(mismatches), file=sys.stderr)
            return 1
        print("Generated READMEs match committed data.")
        return 0
    if not args.render_only:
        day = data["generated_at"][:10]
        snapshot = {"date": day, "generated_at": data["generated_at"],
                    "repositories": [{k: r[k] for k in ("id", "name", "stars")} for r in data["repositories"]]}
        outputs[ROOT / "data/latest.json"] = json_text(data)
        outputs[ROOT / f"data/history/{day}.json"] = json_text(snapshot)
    for path, content in outputs.items():
        write_atomic(path, content)
    print(f"Updated {len(outputs)} files; {len(data['repositories'])} repositories.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (FetchError, ValueError, KeyError, OSError) as error:
        print(f"Update failed: {error}", file=sys.stderr)
        sys.exit(1)
