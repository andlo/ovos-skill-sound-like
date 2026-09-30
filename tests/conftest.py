"""Shared pytest fixtures for the sound-like skill test suite."""
import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

_INIT_PATH = Path(__file__).resolve().parents[1] / "__init__.py"
_spec = importlib.util.spec_from_file_location("soundlike_skill", _INIT_PATH)
_module = importlib.util.module_from_spec(_spec)
sys.modules["soundlike_skill"] = _module  # so tests can patch("soundlike_skill.x")
_spec.loader.exec_module(_module)

SoundLike = _module.SoundLike


@pytest.fixture
def skill(monkeypatch):
    s = SoundLike.__new__(SoundLike)
    s.log = MagicMock()
    s.skill_id = "ovos-skill-sound-like.test"
    s.status = MagicMock()
    s._bus = MagicMock()
    monkeypatch.setattr(SoundLike, "lang", "en-us", raising=False)
    # OVOSSkill.settings is a property with real locking/persistence
    # internals - replace it wholesale with a plain dict-backed
    # property for tests, rather than fighting that machinery.
    monkeypatch.setattr(
        SoundLike, "settings",
        property(lambda self: self._test_settings), raising=False)
    s._test_settings = {}
    s.res_dir = str(Path(__file__).resolve().parents[1])
    s._lang_resources = {}
    s._voc_cache = {}  # needed by voc_list(), bypassed by __new__()
    s.skill_icon = ""
    return s
