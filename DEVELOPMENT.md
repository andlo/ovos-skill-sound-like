# Development

## Setup
```bash
git clone https://github.com/andlo/ovos-skill-sound-like.git
cd ovos-skill-sound-like
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
pip install -r requirements-test.txt
```

## Running tests
```bash
pytest tests/ -v
```
`tests/test_bundled_sounds.py` covers the offline half (alias
resolution, no fuzzy matching, that every bundled animal actually has
a real audio file). `tests/test_online_fallback.py` covers the online
half - all `requests`/network calls are mocked, no real freesound.org
API calls happen in the test suite.

## Adding a new bundled sound

1. Find a genuinely CC0-licensed source. [bigsoundbank.com](https://bigsoundbank.com/)
   is what the current 10 animal sounds came from - every sound there
   is CC0 sitewide, no per-file license-checking needed, and the
   direct-download URL pattern (`/UPLOAD/mp3/<4-digit-id>.mp3`) needs
   no auth. `freesound.org` also works but license varies per upload -
   check it says CC0 specifically, not CC-BY, on that sound's own page.
2. Download it, and check its actual duration - a good "instant
   answer" sound is a few seconds, not the multi-minute ambient
   recordings some of these libraries also host. Trim with `ffmpeg` if
   needed (permitted under CC0 - editing/redistributing is explicitly
   allowed):
   ```bash
   ffmpeg -i original.mp3 -t 6 -c copy trimmed.mp3
   ```
3. Add it to `sounds/<category>/<name>.mp3` - `<category>` is `animals`
   for now, but a new category (e.g. `landmarks`) is just a new
   subfolder, no code change needed.
4. Add the alias to `locale/en-us/sound_aliases.json` under that
   category, then the Danish equivalent in
   `locale/da-dk/sound_aliases.json` - **as a structural translation,
   not a literal one**, same caution as `ovos-skill-convert`'s unit
   aliases: does the Danish word actually mean the same thing, or is
   there a regional/dialect wrinkle worth checking first?
5. Add the source URL to `CREDITS.md`, even for CC0 where attribution
   isn't legally required - it's good practice and makes future
   license audits trivial.
6. Add a `test_bundled_sound_found_*` case per language in
   `tests/test_bundled_sounds.py`. Confirm `pytest tests/ -v` passes.

## Testing the online fallback locally

The test suite mocks every network call, so it never needs a real API
key. To manually test the real freesound.org path:
```bash
export FREESOUND_TEST_KEY="your-key-here"
python3 -c "
import sys; sys.path.insert(0, '.')
from __init__ import SoundLike
# construct a bare instance and call _search_freesound directly,
# or just install the skill on a live OVOS device and set
# freesound_api_key in its settings
"
```
Simplest in practice: install on the live test device
(`ovos@192.168.65.43`) and set `freesound_api_key` via the skill's
settings, then say something NOT in the bundled list.

## Live bus testing

Same discipline as the rest of the OVOS projects here:
- One utterance per script run.
- `time.sleep(6-10)` after sending, to give the skill time to respond
  and be captured.
- `time.sleep(30-60)` between separate test runs, to avoid queue
  contamination on the live device.
- Test device: `ovos@192.168.65.43` (systemd/venv install).
- The online-fallback path adds real network latency - give it a bit
  longer than a bundled-sound test run before assuming it failed.

## Versioning

`version.py` follows `VERSION_MAJOR.VERSION_MINOR.VERSION_BUILD[aVERSION_ALPHA]`.

This project stays on **0.0.x** until the bundled animal set is
stable and the online fallback has been exercised against the real
freesound.org API at least once (not just the mocked test suite) -
at that point we bump to **0.1.0**.

## Releasing

Releases are tag-triggered (`v*`):
```bash
git add version.py
git commit -m "chore: bump version to 0.0.X"
git tag vX.Y.Z
git push && git push --tags
```

This triggers `.github/workflows/test.yml` first, then
`.github/workflows/publish.yml` (PyPI, via trusted publishing/OIDC -
see `ovos-skill-convert`'s DEVELOPMENT.md for the one-time PyPI setup
this needs before the first tagged release).

## Style / conventions

- License: GPL-3.0-or-later (matches the other `andlo` skill repos).
- `locale/<lang-code>/` layout, `skill.json` inside each locale folder.
- Category-grouped alias JSON (`sound_aliases.json`), same pattern as
  `ovos-skill-convert`'s `unit_aliases.json` - see that project's
  DEVELOPMENT.md for the general philosophy (verify before trusting,
  structural not literal translation, present changes for review).
