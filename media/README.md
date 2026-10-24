# Media Curation

`collections.json` is the reviewed data source for the website's in-page media explorer. It is deliberately static: discovery happens in the weekly automation, the proposed list is reviewed in a pull request, and the published page renders only merged selections.

## Test Rule

- Six videos per parashah: three French and three English.
- Prefer recurring approved channels before open YouTube search.
- Keep one current Rabbi Dovid Kaplan / Ohr Somayach teaching when available.
- Use the same recurring channels across adjacent weeks when they remain relevant; this makes editorial drift visible.
- Label overview, philosophical, family, thematic, and mystical material rather than presenting every video as the same kind of Torah source.
- Treat videos as learning companions, not as primary or classical source evidence.
- Verify the exact title, channel, video ID, and oEmbed availability before proposing a change.
- Keep an external YouTube link as a fallback because uploaders can disable embedding later.

## Approved Seed Channels

- [SHOFAR / Rav Oury Cherki](https://www.youtube.com/@SHOFAR_officiel)
- [Torah-Box](https://www.youtube.com/@torahbox)
- [HEVRATPINTO](https://www.youtube.com/@HEVRATPINTO)
- [Ohr Somayach](https://www.youtube.com/@OhrSomayach)
- [The Rabbi Sacks Legacy](https://www.youtube.com/@rabbisacks)
- [Rabbi Yosef Shusterman](https://www.youtube.com/@bhchabad)

The seed list is a priority list, not a blanket endorsement. Videos outside it require an explicit editorial reason in the pull request.

## Weekly Refresh

1. Search each approved channel for the upcoming parashah, including common English and French spellings.
2. Prefer a current weekly upload where one exists; retain a strong archive item only when it contributes a distinct layer.
3. Compare the proposed set with the prior parashah for language balance, channel continuity, topical relevance, and format diversity.
4. Update `media/collections.json`, run `python3 scripts/validate_site.py`, and include the media changes in the weekly chapter PR.
5. Recheck on Friday for late weekly uploads and replace weaker candidates in the existing PR rather than creating a competing PR.
