"""G2: mutation score の算出と判定のテスト。"""
import pytest

import jsix_mutation_gate as mut


def test_elements_score(fixtures):
    """Timeout は killed、NoCoverage は survived、CompileError は分母から除外。"""
    data = mut.parse_mutation_report(fixtures / "mutation-elements.json")
    assert data["killed"] == 3      # Killed x2 + Timeout x1
    assert data["survived"] == 2    # Survived x1 + NoCoverage x1
    assert data["ignored"] == 1     # CompileError
    assert data["score"] == pytest.approx(60.0)


def test_minimal_contract(fixtures):
    """未対応ツールは {"score": N} の最小契約で受ける。"""
    data = mut.parse_mutation_report(fixtures / "mutation-minimal.json")
    assert data["format"] == "minimal"
    assert data["score"] == pytest.approx(64.5)


def test_no_threshold_measures_only(fixtures):
    """閾値の既定値は置かない。min_score 未指定なら計測のみ。"""
    r = mut.check({"report": "mutation-elements.json"}, fixtures)
    assert r.ok and "計測のみ" in r.summary
    assert r.metrics["score"] == pytest.approx(60.0)


def test_threshold(fixtures):
    assert mut.check({"report": "mutation-elements.json", "min_score": 60}, fixtures).ok
    r = mut.check({"report": "mutation-elements.json", "min_score": 70}, fixtures)
    assert not r.ok


def test_survivors_reported(fixtures):
    """生存ミュータントは証跡に載せる（追加テストの手がかりになる）。"""
    r = mut.check({"report": "mutation-elements.json", "min_score": 70}, fixtures)
    files = {s["file"] for s in r.findings}
    assert files == {"app/workflow.py", "app/main.py"}


def test_scope_changed(fixtures):
    """scope=changed は変更ファイルだけで再計算する。"""
    r = mut.check(
        {"report": "mutation-elements.json", "scope": "changed", "min_score": 50},
        fixtures,
        changed_files=["app/workflow.py"],
    )
    assert r.ok
    assert r.metrics["scoped_score"] == pytest.approx(75.0)  # killed 3 / (3+1)
    assert r.metrics["scoped_files"] == ["app/workflow.py"]


def test_scope_changed_rejects_minimal(fixtures):
    """最小契約 JSON にはファイル別内訳が無いので scope=changed は使えない。"""
    r = mut.check(
        {"report": "mutation-minimal.json", "scope": "changed"},
        fixtures,
        changed_files=["app/workflow.py"],
    )
    assert not r.ok and "最小契約" in r.summary


def test_unknown_format(fixtures):
    r = mut.check({"report": "sast-clean.sarif"}, fixtures)
    assert not r.ok
