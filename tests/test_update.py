"""Offline regression tests for discovery, ranking history, and Markdown safety."""
import base64
from contextlib import ExitStack, redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from email.message import Message
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import sys
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlparse
import xml.etree.ElementTree as ET


SPEC = importlib.util.spec_from_file_location(
    "jevhub_update", Path(__file__).resolve().parents[1] / "scripts" / "update.py"
)
update = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(update)


def repository(name="community/jev-agent", *, ident=1, stars=10, **changes):
    data = {
        "id": ident,
        "full_name": name,
        "description": "Jev AI decision model",
        "stargazers_count": stars,
        "forks_count": 2,
        "topics": [],
        "language": "Python",
        "fork": False,
        "archived": False,
        "private": False,
        "disabled": False,
    }
    data.update(changes)
    return data


def settings(**changes):
    config = {
        "github_queries": ["jev model"],
        "github_pages_per_query": 3,
        "exclude_repositories": [],
        "seed_repositories": [],
        "official_owners": ["typesafe-ai"],
        "repository_overrides": {},
        "readme_checks": 5,
    }
    config.update(changes)
    return config


def search_result(items, *, total=None, incomplete=False):
    return {
        "items": items,
        "total_count": len(items) if total is None else total,
        "incomplete_results": incomplete,
    }


class FakeClient:
    """Only explicitly supplied fixtures can be fetched; never accesses the network."""

    def __init__(self, *, searches=None, repositories=None, readmes=None):
        self.searches = searches or {}
        self.repositories = repositories or {}
        self.readmes = readmes or {}
        self.calls = []

    def get(self, url, *, raw=False):
        self.calls.append(url)
        parsed = urlparse(url)
        if parsed.path == "/search/repositories":
            query = parse_qs(parsed.query)
            if query.get("sort", [""])[0] not in {"stars", "updated"} or query.get("order") != ["desc"]:
                raise AssertionError("Search must request descending stars or updated order")
            if query.get("per_page") != ["100"]:
                raise AssertionError("Search must request full pages")
            value = self.searches[(query["q"][0], int(query["page"][0]))]
        elif parsed.path.endswith("/readme"):
            value = self.readmes[parsed.path[len("/repos/"):-len("/readme")]]
        elif parsed.path.startswith("/repos/"):
            value = self.repositories[parsed.path[len("/repos/"):]]
        else:
            raise AssertionError(f"Unexpected request: {url}")
        if isinstance(value, Exception):
            raise value
        return value


class RelevanceTests(unittest.TestCase):
    def test_accepts_brand_and_multilingual_model_context(self):
        for text in (
            "TypeSafe's Jev",
            "Jev: a System One model for decisions",
            "NanoJev open model replica",
            "OpenJev AI agent routing",
            "Jev 模型的中文复现与智能决策",
        ):
            with self.subTest(text=text):
                self.assertTrue(update.relevant(text))

    def test_rejects_virus_economics_gaming_and_substrings(self):
        for text in (
            "JEV Japanese encephalitis classifier model",
            "JEV flavivirus AI model",
            "JEV 乙型脑炎预测模型",
            "Jevons paradox in AI models",
            "Jev models and the Jevons paradox",
            "FaZe Jev AI-generated gaming highlights",
            "Jev gaming highlights",
            "Jevgeny develops a model",
            "TypeSafe classifier without a named model",
            "Just Jev",
        ):
            with self.subTest(text=text):
                self.assertFalse(update.relevant(text))


class MarkdownSafetyTests(unittest.TestCase):
    def test_cells_cannot_break_tables_or_inject_html(self):
        value = update.cell("first|second\n<script>alert(1)</script> [x](url) `code` *bold*")
        self.assertNotIn("\n", value)
        self.assertNotIn("<script>", value)
        self.assertIn("first\\|second", value)
        self.assertIn("&lt;script&gt;", value)
        self.assertIn("\\[x\\]", value)
        self.assertIn("\\`code\\`", value)
        self.assertIn("\\*bold\\*", value)

    def test_long_cells_are_truncated(self):
        self.assertEqual(update.cell("a" * 100, limit=10), "a" * 9 + "…")
        self.assertEqual(update.cell(0), "0")

    def test_urls_reject_active_content_and_credentials(self):
        for url in (
            "javascript:alert(1)",
            "data:text/html,<script>alert(1)</script>",
            "file:///etc/passwd",
            "//example.com/path",
            "https://user:password@example.com/",
            "https:///missing-host",
        ):
            with self.subTest(url=url):
                self.assertEqual(update.safe_url(url), "")
                self.assertEqual(update.link("safe title", url), "safe title")

    def test_urls_escape_markdown_terminators_and_whitespace(self):
        value = update.safe_url("https://example.com/a(b)[c] space?q=x|y")
        self.assertEqual(value, "https://example.com/a%28b%29%5Bc%5D%20space?q=x%7Cy")
        self.assertEqual(update.link("[name]", "https://example.com"),
                         "[\\[name\\]](https://example.com)")


class GitHubCollectionTests(unittest.TestCase):
    def test_topic_only_generic_projects_are_excluded_with_reviewed_and_official_exceptions(self):
        candidates = [
            repository("broad/general-toolkit", ident=1, stars=100_000,
                       description="General AI model and agent toolkit", topics=["jev"]),
            repository("reviewed/decision-engine", ident=2, description="A small engine"),
            repository("typesafe-ai/utilities", ident=3, description="Shared utilities"),
            repository("community/model-bridge", ident=4, description="A bridge for the Jev model"),
            repository("community/nanojev", ident=5, description="A tiny experiment", topics=["model"]),
        ]
        client = FakeClient(searches={("jev model", 1): search_result(candidates)})
        rows, _ = update.collect_github(client, settings(seed_repositories=["reviewed/decision-engine"]))
        self.assertEqual({row["id"] for row in rows}, {2, 3, 4, 5})
        self.assertEqual(next(row for row in rows if row["id"] == 2)["evidence"], "reviewed seed")
        self.assertEqual(next(row for row in rows if row["id"] == 3)["evidence"], "official organization")
        self.assertEqual(len(client.calls), 1)

    def test_repository_rename_between_queries_does_not_duplicate_immutable_id(self):
        client = FakeClient(searches={
            ("jev model", 1): search_result([repository("old/jev", ident=42, stars=10)]),
            ("jev agent", 1): search_result([repository("new/jev", ident=42, stars=12)]),
        })
        rows, _ = update.collect_github(client, settings(github_queries=["jev model", "jev agent"]))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["id"], 42)
        self.assertEqual(rows[0]["name"], "new/jev")

    def test_recent_query_uses_updated_sort_to_surface_new_repositories(self):
        candidate = repository("community/new-jev", ident=77, stars=0)
        client = FakeClient(searches={("jev model", 1): search_result([candidate])})
        rows, status = update.collect_github(client, settings(github_recent_queries=["jev model"]))
        self.assertEqual(rows[0]["id"], 77)
        recent = [url for url in client.calls if "sort=updated" in url]
        self.assertEqual(len(recent), 1)
        self.assertEqual(status["queries"][1]["sort"], "updated")

    def test_paginates_deduplicates_filters_noise_and_fetches_named_seed(self):
        first = repository("community/jev-agent", ident=1, stars=25)
        second = repository("community/nanojev", ident=2, stars=9)
        noise = [repository(f"people/unrelated-{n}", ident=100 + n,
                            description="An unrelated utility") for n in range(99)]
        discarded = [
            repository("other/jev-fork", ident=10, fork=True),
            repository("other/jev-archived", ident=11, archived=True),
            repository("other/jev-private", ident=12, private=True),
            repository("other/jev-disabled", ident=13, disabled=True),
            repository("other/jev-noise", ident=14, description="JEV encephalitis model"),
            repository("faze/jev", ident=15, description="FaZe Jev AI gaming clips"),
            repository("catalog/JevHub", ident=16),
        ]
        seed = repository("typesafe-ai/system-one", ident=3, stars=50,
                          description="Decision engine")
        client = FakeClient(
            searches={
                ("jev model", 1): search_result(noise + [first], total=101),
                ("jev model", 2): search_result([second], total=101),
                ("nanojev", 1): search_result([first] + discarded),
            },
            repositories={"typesafe-ai/system-one": seed},
        )
        rows, status = update.collect_github(client, settings(
            github_queries=["jev model", "nanojev"],
            seed_repositories=["typesafe-ai/system-one"],
            exclude_repositories=["CATALOG/jevhub"],
        ))
        self.assertEqual({row["id"] for row in rows}, {1, 2, 3})
        self.assertEqual(len(rows), 3)
        self.assertEqual(len(client.calls), 4)
        self.assertEqual(status["queries"][0]["returned"], 101)
        self.assertFalse(status["queries"][0]["truncated"])
        self.assertEqual(next(row for row in rows if row["id"] == 3)["evidence"], "reviewed seed")

    def test_checks_readme_when_name_has_jev_but_metadata_lacks_context(self):
        candidate = repository("community/jev", description="A tiny experiment")
        body = base64.b64encode("Jev 模型复现".encode()).decode()
        client = FakeClient(
            searches={("jev model", 1): search_result([candidate])},
            readmes={"community/jev": {"content": body}},
        )
        rows, status = update.collect_github(client, settings())
        self.assertEqual(rows[0]["evidence"], "repository README")
        self.assertEqual(status["readme_checks"], 1)

    def test_reports_configured_search_cap_instead_of_claiming_full_coverage(self):
        items = [repository(ident=n, name=f"community/jev-{n}") for n in range(100)]
        client = FakeClient(searches={("jev model", 1): search_result(items, total=150)})
        rows, status = update.collect_github(client, settings(github_pages_per_query=1))
        self.assertEqual(len(rows), 100)
        self.assertTrue(status["queries"][0]["truncated"])

    def test_incomplete_search_and_failed_seed_are_hard_failures(self):
        good = repository()
        cases = (
            (FakeClient(searches={("jev model", 1): search_result([good], incomplete=True)}), settings()),
            (FakeClient(searches={("jev model", 1): search_result([good])},
                        repositories={"owner/missing": update.FetchError("HTTP 403")}),
             settings(seed_repositories=["owner/missing"])),
        )
        for client, config in cases:
            with self.subTest(config=config):
                with self.assertRaises(update.FetchError):
                    update.collect_github(client, config)

    def test_search_failure_preserves_existing_outputs(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            outputs = {
                "README.md": "Existing Chinese README\n",
                "README.en.md": "Existing English README\n",
                "data/latest.json": '{"existing": true}\n',
                "data/history/2026-09-21.json": '{"date": "2026-09-21"}\n',
            }
            for name, text in outputs.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
            client = FakeClient(searches={("jev model", 1): update.FetchError("HTTP 403")})
            with patch.object(update, "ROOT", root), self.assertRaises(update.FetchError):
                update.collect_github(client, settings())
            actual = {str(path.relative_to(root)): path.read_text(encoding="utf-8")
                      for path in root.rglob("*") if path.is_file()}
            self.assertEqual(actual, outputs)


class HttpClientTests(unittest.TestCase):
    def test_non_rate_limit_403_becomes_fetch_error_without_retry(self):
        error = HTTPError("https://api.github.com/search/repositories", 403,
                          "Forbidden", Message(), None)
        self.addCleanup(error.close)
        with patch.object(update, "urlopen", side_effect=error) as request, \
                patch.object(update.time, "sleep"):
            with self.assertRaisesRegex(update.FetchError, "HTTP 403"):
                update.Client().get("https://api.github.com/search/repositories?q=jev")
        self.assertEqual(request.call_count, 1)

    def test_github_credentials_are_not_sent_to_external_sources(self):
        for url, authenticated in (("https://api.github.com/repos/owner/repo", True),
                                   ("https://news.example.org/", False)):
            with self.subTest(url=url), \
                    patch.object(update, "urlopen", return_value=io.BytesIO(b'{"ok": true}')) as request:
                self.assertEqual(update.Client("secret-test-token").get(url), {"ok": True})
                headers = request.call_args.args[0].headers
                if authenticated:
                    self.assertEqual(headers.get("Authorization"), "Bearer secret-test-token")
                else:
                    self.assertNotIn("Authorization", headers)


class CommunityCollectionTests(unittest.TestCase):
    def test_news_interleaves_languages_deduplicates_and_limits_relevant_results(self):
        def feed(items):
            channel = ET.Element("channel")
            for title, url in items:
                item = ET.SubElement(channel, "item")
                ET.SubElement(item, "title").text = title
                ET.SubElement(item, "link").text = url
                ET.SubElement(item, "source").text = "Fixture publisher"
            rss = ET.Element("rss")
            rss.append(channel)
            return ET.tostring(rss, encoding="unicode")

        english = [(f"Jev AI model article {n}", f"https://example.com/en-{n}") for n in range(1, 9)]
        english.insert(2, ("Jev model shared coverage", "https://example.com/shared"))
        english.insert(0, ("Jevons paradox in AI", "https://example.com/unrelated"))
        chinese = [
            ("Jev 模型中文报道一", "https://example.com/zh-1"),
            ("Jev 模型共同报道", "https://example.com/shared"),
            ("Jev 智能决策报道二", "https://example.com/zh-2"),
            ("Jev 模型中文报道三", "https://example.com/zh-3"),
        ]
        fixtures = {"https://feeds.example.com/en": feed(english),
                    "https://feeds.example.com/zh": feed(chinese)}
        client = Mock()
        client.get.side_effect = lambda url, *, raw: fixtures[url]
        rows = update.collect_news(client, {"news_feeds": list(fixtures), "community_limit": 8})
        self.assertEqual([row["url"] for row in rows], [
            "https://example.com/en-1", "https://example.com/zh-1",
            "https://example.com/en-2", "https://example.com/shared",
            "https://example.com/zh-2", "https://example.com/en-3",
            "https://example.com/zh-3", "https://example.com/en-4",
        ])
        self.assertEqual(len({row["url"] for row in rows}), 8)
        self.assertEqual(rows[3]["title"], "Jev 模型共同报道")
        self.assertTrue(all(call.kwargs == {"raw": True} for call in client.get.call_args_list))

    def test_huggingface_filters_unrelated_names_and_ranks_platform_metrics(self):
        client = Mock()
        client.get.return_value = [
            {"id": "community/nanojev", "likes": 3, "downloads": 50},
            {"id": "community/openjev", "likes": 5, "downloads": 20},
            {"id": "community/jev", "likes": 5, "downloads": 100},
            {"id": "jev/unrelated-model", "likes": 1000, "downloads": 10000},
            {"id": "medical/jev", "tags": ["encephalitis"], "likes": 1000},
            {"id": "economics/jevons", "likes": 1000},
        ]
        rows = update.collect_huggingface(client, {"community_limit": 2})
        self.assertEqual([row["title"] for row in rows], ["community/jev", "community/openjev"])


class RefreshAndCliTests(unittest.TestCase):
    """Use a real temporary workspace and fake transport; no live APIs or repository writes."""

    OPTIONAL = ("hacker_news", "reddit", "huggingface", "news")
    COLLECTORS = ("collect_hn", "collect_reddit", "collect_huggingface", "collect_news")

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.root_patch = patch.object(update, "ROOT", self.root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)
        self.config = settings(curated_resources=[], readme_limit=30)
        self.write_json("config/sources.json", self.config)
        self.write("templates/README.zh.md", "# 中文 JevHub\n\n{{DASHBOARD}}\n")
        self.write("templates/README.en.md", "# English JevHub\n\n{{DASHBOARD}}\n")

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def write_json(self, name, value):
        self.write(name, json.dumps(value, ensure_ascii=False, indent=2) + "\n")

    def files(self):
        return {str(path.relative_to(self.root)): path.read_bytes()
                for path in self.root.rglob("*") if path.is_file()}

    def row(self, ident=1, name="community/jev", stars=10):
        return {"id": ident, "name": name, "stars": stars, "forks": 0,
                "url": "https://github.com/" + name, "language": "Python",
                "category": "research", "description": "Jev 模型复现",
                "description_en": "Jev model replica", "evidence": "reviewed seed",
                "pushed_at": None}

    def snapshot(self):
        data = {"schema_version": 1, "generated_at": "2026-09-22T01:17:00Z",
                "repositories": [self.row()], "curated_resources": [],
                "limits": {"repositories": 30},
                "sources": {"github": {"state": "ok", "queries": []}}}
        for name in self.OPTIONAL:
            data[name] = []
            data["sources"][name] = {"state": "ok", "fetched_at": "2026-09-22T01:17:00Z", "count": 0}
        return data

    def run_main(self, *args):
        with patch.object(sys, "argv", ["update.py", *args]), \
                redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            return update.main()

    def test_live_search_403_preserves_readmes_latest_history_and_creates_nothing(self):
        self.write_json("data/latest.json", self.snapshot())
        self.write_json("data/history/2026-09-21.json", {"date": "2026-09-21", "repositories": []})
        self.write("README.md", "existing Chinese README\n")
        self.write("README.en.md", "existing English README\n")
        before = self.files()
        client = FakeClient(searches={("jev model", 1): update.FetchError("HTTP 403")})
        with patch.object(update, "Client", return_value=client), self.assertRaises(update.FetchError):
            self.run_main()
        self.assertEqual(self.files(), before)

    def test_optional_failures_preserve_prior_items_and_last_success_time(self):
        previous = self.snapshot()
        for name in self.OPTIONAL:
            previous[name] = [{"title": name + " cached item", "url": "https://example.com/"}]
            previous["sources"][name]["fetched_at"] = "2026-09-20T01:17:00Z"
        with ExitStack() as stack:
            stack.enter_context(patch.object(update, "collect_github", return_value=([self.row()], {"queries": []})))
            for collector in self.COLLECTORS:
                stack.enter_context(patch.object(update, collector, side_effect=update.FetchError("HTTP 403")))
            stack.enter_context(redirect_stdout(io.StringIO()))
            data = update.refresh(self.config, previous, FakeClient())
        for name in self.OPTIONAL:
            with self.subTest(source=name):
                self.assertEqual(data[name], previous[name])
                self.assertEqual(data["sources"][name]["state"], "stale")
                self.assertEqual(data["sources"][name]["fetched_at"], "2026-09-20T01:17:00Z")
                self.assertIn("HTTP 403", data["sources"][name]["error"])
                self.assertEqual(data["sources"][name]["count"], 1)

    def test_first_optional_failure_is_unavailable_and_github_stays_star_sorted(self):
        rows = [self.row(1, "owner/z", 10), self.row(2, "owner/B", 20),
                self.row(3, "owner/a", 20), self.row(4, "owner/top", 50)]
        with ExitStack() as stack:
            stack.enter_context(patch.object(update, "collect_github", return_value=(rows, {"queries": []})))
            for collector in self.COLLECTORS:
                stack.enter_context(patch.object(update, collector, side_effect=update.FetchError("HTTP 403")))
            stack.enter_context(redirect_stdout(io.StringIO()))
            data = update.refresh(self.config, {}, FakeClient())
        self.assertEqual([row["id"] for row in data["repositories"]], [4, 3, 2, 1])
        for name in self.OPTIONAL:
            with self.subTest(source=name):
                self.assertEqual(data[name], [])
                self.assertEqual(data["sources"][name]["state"], "unavailable")
                self.assertIsNone(data["sources"][name]["fetched_at"])

    def test_render_check_is_offline_idempotent_and_detects_drift_without_writes(self):
        self.write_json("data/latest.json", self.snapshot())
        with patch.object(update, "Client", side_effect=AssertionError("Offline mode cannot create a client")), \
                patch.object(update, "urlopen", side_effect=AssertionError("Network access is forbidden")):
            self.assertEqual(self.run_main("--render-only"), 0)
            before = self.files()
            self.assertEqual(self.run_main("--render-only", "--check"), 0)
            self.assertEqual(self.files(), before)
            self.write("README.md", "deliberate drift\n")
            drifted = self.files()
            self.assertEqual(self.run_main("--render-only", "--check"), 1)
            self.assertEqual(self.files(), drifted)

    def test_curated_config_edits_render_into_both_languages_without_recollecting(self):
        self.write_json("data/latest.json", self.snapshot())
        self.assertEqual(self.run_main("--render-only"), 0)
        original_snapshot = (self.root / "data/latest.json").read_bytes()
        self.config["curated_resources"] = [{
            "title": "核验过的 Jev 文档", "title_en": "Verified Jev documentation",
            "description": "新的中文阅读入口", "description_en": "A new English starting point",
            "url": "https://example.com/docs", "category": "official", "language": "EN",
        }]
        self.write_json("config/sources.json", self.config)
        with patch.object(update, "Client", side_effect=AssertionError("Unexpected live fetch")):
            self.assertEqual(self.run_main("--render-only", "--check"), 1)
            self.assertEqual(self.run_main("--render-only"), 0)
            self.assertEqual(self.run_main("--render-only", "--check"), 0)
        self.assertIn("核验过的 Jev 文档", (self.root / "README.md").read_text())
        self.assertIn("Verified Jev documentation", (self.root / "README.en.md").read_text())
        self.assertEqual((self.root / "data/latest.json").read_bytes(), original_snapshot)


if __name__ == "__main__":
    unittest.main()
