#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = [
    "index.html",
    "llms.txt",
    "assets/site.css",
    "assets/site.js",
    "chapters/index.json",
    "media/collections.json",
    "media/README.md",
    "chapters/devarim.md",
    "chapters/vaetchanan.md",
    "methodology/selection-criteria.md",
    "methodology/chapter-template.md",
    "sources/source-register.md",
    "reviews/chapter-review-checklist.md",
]
REQUIRED_SECTIONS = [
    "## 1. Opening Reflection",
    "## 2. Narrative Overview",
    "## 3. Five Principal Sugyot",
    "## 4. Five Key Verses",
    "## 5. Advanced Interpretation",
    "## 6. Personal Application",
    "## 7. Parenting Reflection",
    "## 8. Dialectical Analysis",
    "## 9. Cross-Disciplinary Connection",
    "## 10. Calendar Integration",
    "## Source Baseline Checked",
]


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def check_required_files() -> None:
    for rel in REQUIRED_FILES:
        if not (ROOT / rel).is_file():
            fail(f"missing required file: {rel}")


def load_chapter_index() -> list[dict[str, str]]:
    try:
        chapters = json.loads(read(ROOT / "chapters/index.json"))
    except json.JSONDecodeError as exc:
        fail(f"chapters/index.json is not valid JSON: {exc}")

    if not isinstance(chapters, list) or not chapters:
        fail("chapters/index.json must contain a non-empty list")

    slugs: set[str] = set()
    for index, chapter in enumerate(chapters):
        if not isinstance(chapter, dict):
            fail(f"chapters/index.json entry {index} must be an object")
        for key in ("slug", "title", "path"):
            if not isinstance(chapter.get(key), str) or not chapter[key].strip():
                fail(f"chapters/index.json entry {index} missing string field: {key}")
        if chapter["slug"] in slugs:
            fail(f"chapters/index.json has duplicate slug: {chapter['slug']}")
        slugs.add(chapter["slug"])
        if not re.fullmatch(r"[a-z0-9-]+", chapter["slug"]):
            fail(f"invalid chapter slug: {chapter['slug']}")
        if not chapter["path"].startswith("chapters/") or not chapter["path"].endswith(".md"):
            fail(f"invalid chapter path for {chapter['slug']}: {chapter['path']}")
        if not (ROOT / chapter["path"]).is_file():
            fail(f"chapter metadata points to missing file: {chapter['path']}")

    return chapters


def check_chapter_structure() -> None:
    chapters = load_chapter_index()
    indexed_paths = {ROOT / chapter["path"] for chapter in chapters}
    all_chapter_paths = set((ROOT / "chapters").glob("*.md"))
    missing_from_index = sorted(all_chapter_paths - indexed_paths)
    if missing_from_index:
        rels = ", ".join(str(path.relative_to(ROOT)) for path in missing_from_index)
        fail(f"chapter files missing from chapters/index.json: {rels}")

    for chapter in chapters:
        chapter_path = ROOT / chapter["path"]
        text = read(chapter_path)
        for section in REQUIRED_SECTIONS:
            if section not in text:
                fail(f"{chapter_path.relative_to(ROOT)} missing section: {section}")
        if len(re.findall(r"^### Sugya ", text, flags=re.MULTILINE)) != 5:
            fail(f"{chapter_path.relative_to(ROOT)} must contain exactly five sugyot")
        if len(re.findall(r"^### Verse ", text, flags=re.MULTILINE)) != 5:
            fail(f"{chapter_path.relative_to(ROOT)} must contain exactly five key verses")
        if re.search(r"\b(TODO|TBD|FIXME)\b", text):
            fail(f"{chapter_path.relative_to(ROOT)} contains TODO/TBD/FIXME marker")


def check_media_collections() -> None:
    try:
        data = json.loads(read(ROOT / "media/collections.json"))
    except json.JSONDecodeError as exc:
        fail(f"media/collections.json is not valid JSON: {exc}")

    collections = data.get("collections") if isinstance(data, dict) else None
    if not isinstance(collections, list) or not collections:
        fail("media/collections.json must contain a non-empty collections list")

    collection_slugs: set[str] = set()
    required_collections = {"lech-lecha", "noach"}
    required_video_fields = {
        "youtubeId",
        "title",
        "channel",
        "channelUrl",
        "language",
        "format",
        "relation",
    }

    for collection in collections:
        if not isinstance(collection, dict):
            fail("each media collection must be an object")
        slug = collection.get("slug")
        if not isinstance(slug, str) or not re.fullmatch(r"[a-z0-9-]+", slug):
            fail(f"invalid media collection slug: {slug}")
        if slug in collection_slugs:
            fail(f"duplicate media collection slug: {slug}")
        collection_slugs.add(slug)
        compare_with = collection.get("compareWith")
        if not isinstance(compare_with, str) or not re.fullmatch(r"[a-z0-9-]+", compare_with):
            fail(f"media collection {slug} must declare a valid compareWith slug")

        videos = collection.get("videos")
        if not isinstance(videos, list) or len(videos) != 6:
            fail(f"media collection {slug} must contain exactly six videos")
        languages = [video.get("language") for video in videos if isinstance(video, dict)]
        if languages.count("fr") != 3 or languages.count("en") != 3:
            fail(f"media collection {slug} must contain three French and three English videos")

        video_ids: set[str] = set()
        for index, video in enumerate(videos):
            if not isinstance(video, dict):
                fail(f"media collection {slug} video {index} must be an object")
            for field in required_video_fields:
                if not isinstance(video.get(field), str) or not video[field].strip():
                    fail(f"media collection {slug} video {index} missing string field: {field}")
            video_id = video["youtubeId"]
            if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
                fail(f"media collection {slug} has invalid YouTube ID: {video_id}")
            if video_id in video_ids:
                fail(f"media collection {slug} has duplicate YouTube ID: {video_id}")
            video_ids.add(video_id)
            if not video["channelUrl"].startswith("https://www.youtube.com/"):
                fail(f"media collection {slug} has invalid channel URL: {video['channelUrl']}")

    missing = required_collections - collection_slugs
    if missing:
        fail(f"media collections missing comparison set: {', '.join(sorted(missing))}")
    for collection in collections:
        if collection["compareWith"] not in collection_slugs:
            fail(
                f"media collection {collection['slug']} compares with missing collection: "
                f"{collection['compareWith']}"
            )


def local_asset_from_url(url: str, base_dir: Path) -> Path | None:
    if re.match(r"^[a-z]+://", url):
        return None
    if url.startswith("#") or url.startswith("mailto:"):
        return None
    clean_url = url.split("#", 1)[0].split("?", 1)[0]
    return base_dir / clean_url


def check_local_links() -> None:
    markdown_pattern = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
    html_asset_pattern = re.compile(r"""(?:href|src)=["']([^"']+)["']""")
    css_url_pattern = re.compile(r"""url\(["']?([^"')]+)["']?\)""")

    files = list((ROOT / "chapters").glob("*.md")) + [
        ROOT / "index.html",
        ROOT / "assets/site.css",
        ROOT / "chapters/index.json",
        ROOT / "media/collections.json",
    ]

    for path in files:
        text = read(path)
        base_dir = path.parent if path.suffix == ".css" else ROOT
        urls = markdown_pattern.findall(text)
        urls += html_asset_pattern.findall(text)
        urls += css_url_pattern.findall(text)
        for url in urls:
            asset = local_asset_from_url(url, base_dir)
            if asset is not None and not asset.exists():
                fail(f"{path.relative_to(ROOT)} references missing local asset: {url}")


def check_source_position() -> None:
    index = read(ROOT / "index.html")
    register = read(ROOT / "sources/source-register.md")
    selection = read(ROOT / "methodology/selection-criteria.md")
    for label, text in {
        "index.html": index,
        "sources/source-register.md": register,
        "methodology/selection-criteria.md": selection,
    }.items():
        if "Sefaria" not in text:
            fail(f"{label} must state the Sefaria/source curation position")


def check_llms_txt() -> None:
    text = read(ROOT / "llms.txt")
    if not text.startswith("# Torah Skills\n"):
        fail("llms.txt must start with the project H1")
    if "\n> " not in text:
        fail("llms.txt must include a blockquote summary")

    required_urls = [
        "https://jeremybboy.github.io/torah-skills/",
        "https://jeremybboy.github.io/torah-skills/plugins/torah-skills/skills/torah-study/SKILL.md",
        "https://jeremybboy.github.io/torah-skills/methodology/chapter-template.md",
        "https://jeremybboy.github.io/torah-skills/methodology/selection-criteria.md",
        "https://jeremybboy.github.io/torah-skills/sources/source-register.md",
        "https://jeremybboy.github.io/torah-skills/chapters/devarim.md",
        "https://jeremybboy.github.io/torah-skills/chapters/vaetchanan.md",
    ]
    for url in required_urls:
        if url not in text:
            fail(f"llms.txt missing curated URL: {url}")


def main() -> None:
    check_required_files()
    check_chapter_structure()
    check_media_collections()
    check_local_links()
    check_source_position()
    check_llms_txt()
    print("Validation passed.")


if __name__ == "__main__":
    main()
