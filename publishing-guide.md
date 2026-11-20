# Publishing Guide

Use the contents of this folder as the repository root.

## Minimal GitHub Pages Path

1. Create a new GitHub repository.
2. Upload or push all files from this folder.
3. Open repository Settings.
4. Open Pages.
5. Set Source to "Deploy from a branch."
6. Select the default branch and the root folder.
7. Save.

GitHub Pages should publish the site at the repository Pages URL.

## Working Method

Use one pull request per chapter or major methodology change.

Recommended review labels:

- `draft`
- `source-check`
- `selection-criteria`
- `ready-for-reading`
- `publishable`

## Chapter Workflow

1. Draft chapter in `chapters/<parashah>.md`.
2. Add the chapter to `chapters/index.json`.
3. Check the five key verses against `methodology/selection-criteria.md`.
4. Check source claims against `sources/source-register.md`.
5. Run `python3 scripts/validate_site.py`.
6. Review with `reviews/chapter-review-checklist.md`.
7. Merge only after source and selection review.

## Weekly Media Workflow

1. Follow `media/README.md` and propose six videos: three French and three English.
2. Search approved channels first and compare the current parashah with the prior week's collection.
3. Verify each exact YouTube ID, title, channel, and oEmbed response; do not depend on mutable or private playlists.
4. Update `media/collections.json` in the same weekly chapter pull request.
5. Recheck current uploads on Friday and revise the existing pull request when a stronger weekly teaching appears.
6. Treat every video as a reviewed learning companion, not as evidence for the chapter's primary-source claims.

## Weekly Audio Preview

1. After the audio workflow is merged, use **Actions → Weekly Gradium Audio → Run workflow** on `main`. The smoke test uses the repository secret `GRADIUM_API_KEY`, verifies a short MP3, and publishes nothing. The optional repository variable `GRADIUM_VOICE_ID` overrides the default voice.
2. After a successful smoke test, set the Actions variable `WEEKLY_GRADIUM_AUDIO_ENABLED` to `true` and update the Monday draft and catch-up instructions to include `media/audio/<slug>-narration.txt` on the weekly branch. Write a plain-text, source-checked adaptation of the opening three sections, up to 6,000 characters. Do not include unpublished private notes.
3. Once the existing workflow validates and opens the study PR, the audio workflow reads that branch's script as text, without running its code. It splits the narration into segments within [Gradium's 1,500-character free-plan limit](https://docs.gradium.ai/guides/limits), verifies each segment contains audio, and combines them into one MP3. It commits only the MP3 and player metadata to the same open review branch. The expected commit guard prevents overwriting a newer edit. Audio is public on the branch; Pages only publishes after Jeremy merges.
4. If audio fails or there is no narration, the study PR stays open without audio. Check the audio run in Actions and listen for pronunciation and source interpretation before merging. Leave the enable variable unset or set it to `false` to pause automatic synthesis without disabling the study workflow.
5. The audio commit uses the built-in GitHub token, so it does not trigger ordinary push/PR Actions checks. Treat the audio run as evidence for the MP3 only. If branch protection requires a new site check, update the PR from your account to trigger it; do not bypass required checks.
