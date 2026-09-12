"""plugin/scripts のテスト共通設定。"""
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import pytest  # noqa: E402


@pytest.fixture
def fixtures() -> Path:
    return Path(__file__).parent / "fixtures"
