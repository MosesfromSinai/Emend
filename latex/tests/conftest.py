import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.schemas import MasterResume, TailoredResume  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def master() -> MasterResume:
    return MasterResume(**json.loads((FIXTURES / "sample_master.json").read_text()))


@pytest.fixture
def tailored() -> TailoredResume:
    return TailoredResume(**json.loads((FIXTURES / "sample_tailored.json").read_text()))
