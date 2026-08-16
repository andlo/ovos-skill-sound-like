# <img src='icon.png' card_color='#40B4DB' width='50' height='50' style='vertical-align:bottom'/> Sound Like

"How does a cow sound?" A hybrid offline/online sound-lookup skill for
OVOS - **not** an animal-sounds skill specifically, even though the
bundled library happens to be animals today. See "Why not just
'animal sounds'" below.

[![Tests](https://github.com/andlo/ovos-skill-sound-like/actions/workflows/test.yml/badge.svg)](https://github.com/andlo/ovos-skill-sound-like/actions/workflows/test.yml)
[![PyPI version](https://img.shields.io/pypi/v/ovos-skill-sound-like.svg)](https://pypi.org/project/ovos-skill-sound-like/)

> **Early 0.0.x release.** 10 bundled animal sounds, en-us + da-dk.
> Not on the OVOS Skill Store yet.

## Usage
```
"how does a cow sound"
"what does a dog sound like"
"play a cat sound"
"hvordan lyder en ko"          (Danish)
"hvilken lyd laver en hund"    (Danish)
```

If the sound isn't bundled and an online fallback is configured:
```
"how does big ben sound"
"what does a steam boat sound like"
```

## Why not just "animal sounds"?

The first design for this skill *was* animal-specific, sourced
entirely from a fixed, curated, offline sound library. But the
person requesting it also wanted "how does Big Ben sound" and "what
does a boiling egg sound like" to work - genuinely open-ended queries
that no fixed offline list can cover.

Those are two different problems with different tradeoffs:
- A fixed bundled list is instant, offline, and fully quality-
  controlled (every sound was picked and verified by hand).
- An open "search the internet for a sound of X" is unbounded but
  depends on a network connection, an API key, and someone else's
  (uncurated) upload.

Rather than pick one, this skill does both: **bundled sounds always
answer instantly offline; anything else optionally falls back to an
online search.** The skill's identity had to change to match - it was
never really "the animal sounds skill", it's "the how-does-that-sound
skill", and animals just happen to be the first (and so far only)
bundled category.

## Architecture

1. **Bundled, offline, curated.** `sounds/<category>/*.mp3`, aliased
   per language in `locale/<lang>/sound_aliases.json` (same category-
   grouped JSON pattern as `ovos-skill-convert`'s `unit_aliases.json`).
   No internet, no API key, instant playback. Only "animals" (10
   sounds) exists today - adding a new bundled category is a locale-
   file + sounds-folder change, no code.
2. **Online fallback via freesound.org**, only for words NOT in the
   bundled table. Requires a free freesound.org API key (see
   `settingsmeta.json` / Settings). Results are filtered to **CC0
   (public domain) license only** - never anything requiring
   attribution, since a spoken response has no good way to credit a
   source.

Unlike `ovos-skill-convert`'s unit resolver, there is **no fuzzy
matching** on the bundled table - a near-miss animal name falls
through to the (clearly-announced) online fallback rather than
risking a confidently wrong sound. A wrong unit conversion is a
number being slightly off; a wrong animal sound is jarring and
obviously wrong in a completely different way, so the bar for
guessing is higher here.

## What happens when

| Situation | Behavior |
|---|---|
| Word is in the bundled table | Plays instantly, no speech first |
| Word isn't bundled, no API key configured | Says so, doesn't guess |
| Word isn't bundled, API key set, no internet | Says so, doesn't guess |
| Word isn't bundled, API key set, online | Speaks "checking online...", then plays the result |
| Online search finds nothing | Says so |
| Online search fails (network error, bad key, etc) | Says so, doesn't crash |

## Install
```bash
pip install ovos-skill-sound-like
```

## Getting a freesound.org API key (optional)

The bundled sounds work with zero configuration. For the online
fallback:
1. Create a free account at [freesound.org](https://freesound.org).
2. Apply for an API key at
   [freesound.org/apiv2/apply](https://freesound.org/apiv2/apply/).
3. Paste it into this skill's settings (`freesound_api_key`).

## Sound credits

See [CREDITS.md](CREDITS.md) - all bundled sounds are CC0
(public domain) from [bigsoundbank.com](https://bigsoundbank.com/).

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md).

## Category
**Entertainment**

## Tags
#sounds #animals #fun #kids #entertainment
