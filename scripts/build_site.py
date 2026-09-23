#!/usr/bin/env python3
"""Package the website and retain links from the former /site/ deployment."""
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def build(destination):
    destination = Path(destination)
    shutil.copytree(ROOT / "site", destination, dirs_exist_ok=True)
    shutil.copytree(ROOT / "data", destination / "data", dirs_exist_ok=True)
    for path, target, language in (
        ("site/index.html", "../", "zh-CN"),
        ("site/en/index.html", "../../en/", "en"),
    ):
        page = destination / path
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text(f"""<!doctype html>
<html lang="{language}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="0; url={target}">
  <title>JevHub</title>
  <script>location.replace("{target}" + location.search + location.hash);</script>
</head>
<body><a href="{target}">JevHub</a></body>
</html>
""", encoding="utf-8")
    (destination / ".nojekyll").touch()


if __name__ == "__main__":
    build(ROOT / "_site")
