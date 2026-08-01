"""Shared fixtures for core's test suite.

core owns its fixtures independently -- it must run in plain pytest with no
import on another workflow's directory (latex/tests/fixtures used to be
reached into directly, which coupled core's tests to latex's layout).
"""

import json
from pathlib import Path

import pytest

from core.schemas import MasterResume, TailoredResume

FIXTURES = Path(__file__).parent / "fixtures"


def _load(filename: str, schema):
    data = json.loads((FIXTURES / filename).read_text())
    return schema(**data)


@pytest.fixture()
def sample_master() -> MasterResume:
    return _load("sample_master.json", MasterResume)


@pytest.fixture()
def sample_tailored() -> TailoredResume:
    return _load("sample_tailored.json", TailoredResume)
