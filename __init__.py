"""
skill OVOS Sound Like
Copyright (C) 2026  Andreas Lorensen

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

---

"What does that sound like?" - NOT an animal-sounds skill specifically,
even though the only bundled category so far is animals. See README for
the full rationale, but in short: this is a hybrid of two very
different things under one intent.

1. A BUNDLED, CURATED, FULLY OFFLINE sound library (sounds/<category>/,
   aliased per language in locale/<lang>/sound_aliases.json - same
   category-grouped JSON pattern as ovos-skill-convert's
   unit_aliases.json). No internet, no API key, works instantly.
   Currently just "animals" (10 sounds) - adding a new bundled
   category later is a locale-file + sounds-folder change, no code.

2. An OPTIONAL ONLINE FALLBACK via the freesound.org search API, for
   anything NOT in the bundled set - "how does Big Ben sound", "what
   does a steam boat sound like", etc. This needs a free freesound.org
   API key (see settingsmeta.json) and an internet connection. Search
   results are filtered to CC0 (public domain) license ONLY - never
   CC-BY or anything requiring attribution, since a spoken response
   has no good way to attach one.

This shape - bundled/deterministic first, online fallback second, and
never silently guessing when neither path has an answer - mirrors how
ovos-skill-convert always resolves locally and only ever reports "I
don't understand that unit" rather than guessing.
"""

import json
import re
from pathlib import Path

import requests
from ovos_utils.ocp import MediaEntry, MediaType, PlaybackType
from ovos_workshop.decorators import intent_handler
from ovos_workshop.decorators.ocp import ocp_search
from ovos_workshop.skills.common_play import OVOSCommonPlaybackSkill
from ovos_utils.network_utils import is_connected

SKILL_ROOT = Path(__file__).resolve().parent
LOCALE_DIR = SKILL_ROOT / "locale"
SOUNDS_DIR = SKILL_ROOT / "sounds"

FREESOUND_SEARCH_URL = "https://freesound.org/apiv2/search/text/"
# CC0 only - see module docstring. This is a Freesound API filter
# query string, not a Python dict key.
FREESOUND_LICENSE_FILTER = 'license:"Creative Commons 0"'
FREESOUND_TIMEOUT_SECONDS = 6


def _load_sound_aliases_from_disk():
    """Reads locale/<lang>/sound_aliases.json for every language folder
    present, keeping the category alongside each filename (unlike
    ovos-skill-convert's flattened unit resolver, the category here IS
    needed at runtime - it's the subfolder under sounds/ the bundled
    file lives in).

    Raises at import time if two categories in the same file define
    the same alias with a DIFFERENT target - same collision-guard
    pattern as ovos-skill-convert.
    """
    merged = {}
    if not LOCALE_DIR.is_dir():
        return merged
    for lang_dir in sorted(LOCALE_DIR.iterdir()):
        if not lang_dir.is_dir():
            continue
        alias_file = lang_dir / "sound_aliases.json"
        if not alias_file.exists():
            continue
        with open(alias_file, encoding="utf-8") as f:
            categories = json.load(f)

        lang = lang_dir.name.lower()
        merged.setdefault(lang, {})
        origin = {}
        for category, aliases in categories.items():
            if category.startswith("_"):
                continue
            for alias, filename in aliases.items():
                existing = merged[lang].get(alias)
                candidate = (category, filename)
                if existing is not None and existing != candidate:
                    prev_category, _ = origin[alias]
                    raise ValueError(
                        f"sound_aliases.json collision in {alias_file}: "
                        f"alias {alias!r} maps to both {existing!r} "
                        f"(in {prev_category!r}) and {candidate!r} "
                        f"(in {category!r})"
                    )
                merged[lang][alias] = candidate
                origin[alias] = candidate
    return merged


MERGED_SOUND_ALIASES = _load_sound_aliases_from_disk()

# "play a cat sound" is taken by the OCP pipeline before padatious, so
# the skill also answers OCP's search (issue #1) - for the bundled
# sounds only, so it never claims a phrase it can't play offline. OCP
# only asks skills that support the media type it guessed, so AUDIO,
# MUSIC and GENERIC are accepted and the result echoes the query's type
# (OCP's media-type filter keeps it). The bundled file is a normal audio
# file, so OCP plays it itself (PlaybackType.AUDIO) and handles stop.
OCP_MEDIA = [MediaType.AUDIO, MediaType.MUSIC, MediaType.GENERIC]
OCP_CONFIDENCE = 100


class SoundLike(OVOSCommonPlaybackSkill):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, supported_media=OCP_MEDIA,
                         skill_icon=str(SKILL_ROOT / "icon.png"), **kwargs)

    def _ocp_subject(self, phrase, lang):
        """The animal in "a cat sound" / "the sound of a cow" - only when
        the phrase asks for a sound and names nothing but the animal."""
        words = re.findall(r"\w+", (phrase or "").lower())
        sound_words = {w.lower() for w in self.voc_list("sound", lang)}
        if not sound_words.intersection(words):
            return None
        filler = {w.lower() for w in self.voc_list("filler", lang)}
        subject = " ".join(w for w in words
                           if w not in sound_words and w not in filler)
        return subject or None

    @ocp_search()
    def search_sound(self, phrase, media_type=MediaType.GENERIC):
        subject = self._ocp_subject(phrase, self.lang)
        path = self._bundled_sound_path(subject, self.lang) if subject else None
        if not path:
            return []
        return [MediaEntry(
            uri=f"file://{path}",
            title=subject,
            artist="Sound Like",
            media_type=media_type if media_type in OCP_MEDIA else MediaType.AUDIO,
            playback=PlaybackType.AUDIO,
            match_confidence=OCP_CONFIDENCE,
            skill_icon=self.skill_icon,
            skill_id=self.skill_id,
        )]

    def _aliases_for(self, lang):
        lang = lang.lower()
        return MERGED_SOUND_ALIASES.get(lang) or MERGED_SOUND_ALIASES.get("en-us", {})

    def _bundled_sound_path(self, subject, lang):
        """Exact match only against the bundled alias table - no fuzzy
        matching here (unlike ovos-skill-convert's unit resolver).
        A mismatched animal sound is a much more noticeable, jarring
        wrong answer than a mismatched unit conversion, so a miss
        falls through to the (clearly-labeled) online fallback rather
        than risking a confident wrong guess."""
        aliases = self._aliases_for(lang)
        match = aliases.get(subject.strip().lower())
        if not match:
            return None
        category, filename = match
        path = SOUNDS_DIR / category / f"{filename}.mp3"
        return str(path) if path.exists() else None

    @property
    def api_key(self):
        return (self.settings.get("freesound_api_key") or "").strip()

    def _search_freesound(self, subject):
        """Returns a preview URL for the top CC0-licensed match, or
        None if nothing matched. Raises on network/HTTP errors -
        callers are expected to handle that (see handle_sound_like)."""
        params = {
            "query": subject,
            "token": self.api_key,
            "filter": FREESOUND_LICENSE_FILTER,
            "fields": "id,name,previews,license",
            "page_size": 1,
            "sort": "score",
        }
        r = requests.get(FREESOUND_SEARCH_URL, params=params, timeout=FREESOUND_TIMEOUT_SECONDS)
        r.raise_for_status()
        results = r.json().get("results") or []
        if not results:
            return None
        previews = results[0].get("previews", {})
        return previews.get("preview-hq-mp3") or previews.get("preview-lq-mp3")

    @intent_handler("sound_like.intent")
    def handle_sound_like(self, message):
        subject = (message.data.get("subject") or "").strip()
        if not subject:
            self.speak_dialog("sound_not_found", {"subject": subject})
            return

        bundled = self._bundled_sound_path(subject, self.lang)
        if bundled:
            # instant=True: no preceding speech, so it should play
            # immediately rather than queue
            self.play_audio(bundled, instant=True)
            return

        if not self.api_key:
            self.speak_dialog("no_online_lookup", {"subject": subject})
            return

        if not is_connected():
            self.speak_dialog("offline_no_internet", {"subject": subject})
            return

        # Speak first, so the network round-trip doesn't feel like
        # dead air - then queue (not instant) so playback follows the
        # speech rather than potentially talking over it.
        self.speak_dialog("searching_online", {"subject": subject})
        try:
            url = self._search_freesound(subject)
        except Exception:
            self.log.exception(f"freesound lookup failed for {subject!r}")
            self.speak_dialog("sound_lookup_failed", {"subject": subject})
            return

        if not url:
            self.speak_dialog("sound_not_found", {"subject": subject})
            return

        self.play_audio(url, instant=False)
