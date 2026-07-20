# Torah Study Companion

GitHub Pages-ready preview for a Torah study companion built chapter by chapter.

## Editorial Position

This is an independent curation and study-companion project. Most source links currently point to Sefaria, and chapter drafts should be understood as curated learning pathways shaped by the project methodology, not as a substitute for the original source texts.

The editorial standard is: source-first, methodology-driven, and human-reviewed before publication.

## Structure

- `index.html` - static reader for the published site.
- `assets/` - CSS, JavaScript, and image assets.
- `chapters/` - Markdown chapter drafts plus `index.json` chapter metadata.
- `methodology/` - editorial rules, chapter template, and selection rubric.
- `sources/` - source register and verification notes.
- `reviews/` - chapter review checklist.

## Local Preview

From this folder:

```bash
python3 -m http.server 8080
```

Then open:

```text
http://localhost:8080
```

## GitHub Pages

Create a new GitHub repository from the contents of this folder. In repository settings, enable GitHub Pages and publish from the root of the default branch.

Use pull requests for chapter changes. Do not treat AI-generated drafts as final until a human review confirms verse selection, source quality, and commentary accuracy.

## Validation

Run this before opening or merging a pull request:

```bash
python3 scripts/validate_site.py
```

GitHub Actions also runs the same validation on pull requests and pushes to `main`.

## Add A Chapter

1. Add the chapter Markdown file under `chapters/`.
2. Add one metadata entry to `chapters/index.json`.
3. Run `python3 scripts/validate_site.py`.

Do not edit `index.html` or `assets/site.js` just to add a chapter.
