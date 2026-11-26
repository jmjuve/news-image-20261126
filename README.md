# news-image-20261126

[![make.fun · news-image-20261126](https://make.fun/badge/news-image-20261126.svg)](https://make.fun/bounty/news-image-20261126?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261126)
[![rank](https://make.fun/badge/news-image-20261126/jmjuve/news-image-20261126/rank.svg)](https://make.fun/bounty/news-image-20261126/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261126)
[![reward](https://make.fun/badge/news-image-20261126/jmjuve/news-image-20261126/reward.svg)](https://make.fun/bounty/news-image-20261126?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261126)

A program that draws one front-page image summing up the world news of
Thursday 26 November 2026, for the
[make.fun bounty](https://make.fun/bounty/news-image-20261126).

## The day's news in the image

- **Hero — Brussels:** EU leaders meet for a special European Council
  (26–27 Nov). 27 leaders gather to decide the long-term budget and a
  €45bn loan for Kyiv in 2027; ECB leadership to be renewed. The summit
  opens today, so the image states no outcome.
- **USA — Thanksgiving:** the 100th Macy's Thanksgiving Day Parade
  marches in New York; NFL tripleheader today.
- **India — Constitution Day:** adopted 26 November 1949.
- **Geneva — World Chess Championship:** Game 3 today,
  Gukesh–Sindarov level 1–1 after two draws.

## Run it

Pure Python 3 standard library — no network, no third-party packages,
no external fonts. The picture is drawn with code (flat vector shapes
and a hand-built 5×7 bitmap capital font) and written as a
deterministic PNG, so every run writes identical bytes.

```sh
python3 main.py            # writes out/entry.png
MAKEFUN_OUTPUT_DIR=/output python3 main.py   # grader mode
```

Output: a 1024×1024 PNG, well under 1 MiB.

## License

MIT — see [LICENSE](LICENSE).
