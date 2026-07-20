# Contributing

All substantive changes should happen through pull requests.

## Required Workflow

1. Create a branch from `main`.
2. Make the change.
3. Run validation:

   ```bash
   python3 scripts/validate_site.py
   ```

4. Open a pull request.
5. Use the pull request checklist.
6. Merge only after the source and methodology review is complete.

## Adding A Chapter

Add the chapter file under `chapters/`, then add one entry to `chapters/index.json`.
The site navigation is generated from that metadata file.

## Editorial Standard

This project is a curated Torah study companion. Most source links currently point to Sefaria, but the project is not a replacement for Sefaria and is not affiliated with Sefaria.

The methodology decides what gets selected. Human review decides whether the selection is strong enough to publish.

## Direct Pushes

Avoid direct pushes to `main` except for urgent repair work. Even small content edits should use a pull request so the editorial trail remains visible.
