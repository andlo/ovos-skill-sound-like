"""Tests for the online (freesound.org) half of the hybrid
architecture - all requests/network calls are mocked, no real API
calls happen in the test suite."""
from unittest.mock import MagicMock, patch

import pytest


def test_no_api_key_configured_speaks_no_online_lookup(skill):
    skill.play_audio = MagicMock()
    skill.speak_dialog = MagicMock()
    message = MagicMock()
    message.data = {"subject": "steam boat"}
    skill.handle_sound_like(message)
    skill.speak_dialog.assert_called_once_with(
        "no_online_lookup", {"subject": "steam boat"})
    skill.play_audio.assert_not_called()


def test_api_key_but_offline_speaks_offline_dialog(skill):
    skill._test_settings = {"freesound_api_key": "fake-key"}
    skill.play_audio = MagicMock()
    skill.speak_dialog = MagicMock()
    message = MagicMock()
    message.data = {"subject": "steam boat"}
    with patch("soundlike_skill.is_connected", return_value=False):
        skill.handle_sound_like(message)
    skill.speak_dialog.assert_called_once_with(
        "offline_no_internet", {"subject": "steam boat"})
    skill.play_audio.assert_not_called()


def test_successful_online_lookup_speaks_then_plays_queued(skill):
    skill._test_settings = {"freesound_api_key": "fake-key"}
    skill.play_audio = MagicMock()
    skill.speak_dialog = MagicMock()
    message = MagicMock()
    message.data = {"subject": "big ben"}
    with patch("soundlike_skill.is_connected", return_value=True), \
         patch.object(skill, "_search_freesound", return_value="https://example.com/preview.mp3"):
        skill.handle_sound_like(message)
    skill.speak_dialog.assert_called_once_with(
        "searching_online", {"subject": "big ben"})
    skill.play_audio.assert_called_once_with(
        "https://example.com/preview.mp3", instant=False)


def test_online_lookup_returns_nothing_speaks_not_found(skill):
    skill._test_settings = {"freesound_api_key": "fake-key"}
    skill.play_audio = MagicMock()
    skill.speak_dialog = MagicMock()
    message = MagicMock()
    message.data = {"subject": "asdkjhasd"}
    with patch("soundlike_skill.is_connected", return_value=True), \
         patch.object(skill, "_search_freesound", return_value=None):
        skill.handle_sound_like(message)
    assert skill.speak_dialog.call_args_list[-1] == (
        ("sound_not_found", {"subject": "asdkjhasd"}), {})
    skill.play_audio.assert_not_called()


def test_online_lookup_network_error_speaks_lookup_failed(skill):
    skill._test_settings = {"freesound_api_key": "fake-key"}
    skill.play_audio = MagicMock()
    skill.speak_dialog = MagicMock()
    message = MagicMock()
    message.data = {"subject": "big ben"}
    with patch("soundlike_skill.is_connected", return_value=True), \
         patch.object(skill, "_search_freesound", side_effect=ConnectionError("boom")):
        skill.handle_sound_like(message)
    assert skill.speak_dialog.call_args_list[-1] == (
        ("sound_lookup_failed", {"subject": "big ben"}), {})
    skill.play_audio.assert_not_called()


def test_search_freesound_filters_to_cc0_license():
    """Confirms the license filter string is present in every search
    call - this is the mechanism that keeps every online result
    attribution-free, since a spoken response can't attach credit."""
    import importlib.util
    from pathlib import Path
    spec = importlib.util.spec_from_file_location(
        "soundlike_module_check", Path(__file__).resolve().parents[1] / "__init__.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    assert "Creative Commons 0" in m.FREESOUND_LICENSE_FILTER


def test_bundled_sound_always_takes_priority_over_online(skill):
    """Even with an API key configured, a bundled match should never
    trigger a network call."""
    skill._test_settings = {"freesound_api_key": "fake-key"}
    skill.play_audio = MagicMock()
    skill.speak_dialog = MagicMock()
    skill._search_freesound = MagicMock()
    message = MagicMock()
    message.data = {"subject": "cow"}
    skill.handle_sound_like(message)
    skill._search_freesound.assert_not_called()
    skill.play_audio.assert_called_once()
