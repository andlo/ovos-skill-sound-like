"""Tests for the bundled (offline) half of the hybrid architecture."""
from pathlib import Path
from unittest.mock import MagicMock

import pytest


def test_bundled_sound_found_en(skill):
    path = skill._bundled_sound_path("cow", "en-us")
    assert path is not None
    assert path.endswith("sounds/animals/cow.mp3")
    assert Path(path).exists()


def test_bundled_sound_found_da(skill):
    path = skill._bundled_sound_path("ko", "da-dk")
    assert path is not None
    assert Path(path).exists()


def test_bundled_sound_plural_alias(skill):
    assert skill._bundled_sound_path("cows", "en-us") is not None


def test_bundled_sound_unknown_returns_none(skill):
    assert skill._bundled_sound_path("steam boat", "en-us") is None


def test_bundled_sound_not_fuzzy_matched(skill):
    """Unlike ovos-skill-convert's unit resolver, there's no fuzzy
    matching here - a near-miss should NOT resolve to something else,
    since a wrong animal sound is a much more jarring wrong answer
    than a wrong unit conversion."""
    assert skill._bundled_sound_path("cowe", "en-us") is None


def test_all_ten_bundled_animals_have_real_files(skill):
    for word in ["cow", "dog", "cat", "horse", "sheep", "pig",
                 "rooster", "duck", "owl", "frog"]:
        path = skill._bundled_sound_path(word, "en-us")
        assert path is not None, f"{word} not resolvable"
        assert Path(path).stat().st_size > 1000, f"{word} file suspiciously small"


def test_handle_sound_like_plays_bundled_instantly(skill):
    skill.play_audio = MagicMock()
    skill.speak_dialog = MagicMock()
    message = MagicMock()
    message.data = {"subject": "cow"}
    skill.handle_sound_like(message)
    skill.play_audio.assert_called_once()
    args, kwargs = skill.play_audio.call_args
    assert kwargs.get("instant") is True
    skill.speak_dialog.assert_not_called()
