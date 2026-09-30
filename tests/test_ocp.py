"""OCP: "play a cat sound" is taken by the OCP pipeline before padatious,
so the skill answers OCP's search for its bundled sounds (#1)."""
import pytest
from ovos_utils.ocp import MediaType, PlaybackType

import soundlike_skill as sl


@pytest.fixture(autouse=True)
def _no_entity_autoregister(monkeypatch):
    # ovos-workshop >= 9.8 auto-registers entity files on load_lang(),
    # needing attributes __new__() bypasses; there are no entity files here
    monkeypatch.setattr(sl.SoundLike, "_auto_register_entity_files",
                        lambda *a, **k: None, raising=False)


@pytest.mark.parametrize("phrase,file", [
    ("a cat sound", "cat.mp3"),
    ("the sound of a cow", "cow.mp3"),
    ("dog sounds", "dog.mp3"),
    ("the sound a rooster makes", "rooster.mp3"),
])
def test_search_answers_bundled_sounds(skill, phrase, file):
    [r] = skill.search_sound(phrase, MediaType.MUSIC)
    assert r.uri.startswith("file://") and r.uri.endswith(file)
    assert r.match_confidence == 100
    assert r.playback == PlaybackType.AUDIO  # OCP plays the file itself
    assert r.media_type == MediaType.MUSIC  # echoed, so OCP's filter keeps it


@pytest.mark.parametrize("phrase", [
    "stray cat strut",           # no "sound" asked for
    "the sound of silence",      # not a bundled sound
    "a unicorn sound",           # not bundled (online fallback is not offered via OCP)
    "cat sound by the band",     # something else is asked for
    "",
])
def test_search_ignores_other_phrases(skill, phrase):
    assert skill.search_sound(phrase, MediaType.MUSIC) == []


def test_search_danish(skill, monkeypatch):
    monkeypatch.setattr(sl.SoundLike, "lang", "da-dk", raising=False)
    [r] = skill.search_sound("lyden af en ko", MediaType.AUDIO)
    assert r.uri.endswith("cow.mp3")
