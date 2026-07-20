#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = [
    "index.html",
    "assets/site.css",
    "assets/site.js",
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


def check_chapter_structure() -> None:
    for chapter in sorted((ROOT / "chapters").glob("*.md")):
        text = read(chapter)
        for section in REQUIRED_SECTIONS:
            if section not in text:
                fail(f"{chapter.relative_to(ROOT)} missing section: {section}")
        if len(re.findall(r"^### Sugya ", text, flags=re.MULTILINE)) != 5:
            fail(f"{chapter.relative_to(ROOT)} must contain exactly five sugyot")
        if len(re.findall(r"^### Verse ", text, flags=re.MULTILINE)) != 5:
            fail(f"{chapter.relative_to(ROOT)} must contain exactly five key verses")
        if re.search(r"\b(TODO|TBD|FIXME)\b", text):
            fail(f"{chapter.relative_to(ROOT)} contains TODO/TBD/FIXME marker")


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


def main() -> None:
    check_required_files()
    check_chapter_structure()
    check_local_links()
    check_source_position()
    print("Validation passed.")


if __name__ == "__main__":
    main()
