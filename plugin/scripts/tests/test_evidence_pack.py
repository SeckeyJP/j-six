"""G4: 証跡パッケージ生成のテスト。

証跡は顧客への納品物になり得るため、以下を重点的に検証する。
  - 証跡 / 参考所見 / 承認 の3区分が混ざらないこと
  - 推定値が入らないこと（数値はすべてゲートの結果由来）
  - 実行環境の絶対パスが残らないこと
"""
import json

import pytest

import jsix_evidence_pack as pack

RESULTS = {
    "g1": {
        "status": "passed",
        "checks": {
            "sast": {
                "ok": True, "skipped": False,
                "summary": "sast: error 以上の指摘なし（error 0 / warning 1 / note 0）",
                "metrics": {"error": 0, "warning": 1, "note": 0, "suppressed": 2,
                            "max_severity": "error",
                            "tools": [{"name": "bandit", "version": "1.8.6"}]},
                "findings": [{"tool": "bandit", "rule": "B404", "level": "note",
                              "message": "subprocess", "file": "app/run.py", "line": 3}],
            },
            "scope": {
                "ok": True, "skipped": False,
                "summary": "scope: 変更 2ファイルはすべて許可範囲内",
                "metrics": {"changed_files": 2, "violations": 0,
                            "allow": ["app/**"], "deny": ["tests/acceptance/**"]},
                "findings": [],
            },
        },
    },
    "g2": {
        "status": "passed",
        "checks": {
            "tests": {"ok": True, "skipped": False, "summary": "tests: 全 37件 通過",
                      "metrics": {"tests": 37, "failures": 0, "errors": 0, "skipped": 0},
                      "findings": []},
            "holdout": {"ok": True, "skipped": False, "summary": "holdout: 全 10件 通過",
                        "metrics": {"tests": 10, "failures": 0, "errors": 0, "skipped": 0},
                        "findings": []},
            "coverage": {"ok": True, "skipped": False,
                         "summary": "coverage: 99.0% ≥ 閾値 95.0%",
                         "metrics": {"line_pct": 99.0, "min": 95.0, "format": "cobertura", "files": 4},
                         "findings": [{"file": "app/models.py", "line_pct": 98.0,
                                       "covered": 43, "total": 44}]},
            "mutation": {"ok": True, "skipped": False,
                         "summary": "mutation: 全体 score 60.0%（閾値未設定のため計測のみ）",
                         "metrics": {"score": 60.0, "killed": 3, "survived": 2,
                                     "ignored": 1, "scope": "all"},
                         "findings": [{"file": "app/workflow.py", "line": 20,
                                       "mutator": "EqualityOperator"}]},
            "test_tamper": {"ok": True, "skipped": False,
                            "summary": "test_tamper: 弱体化なし",
                            "metrics": {"baseline_ref": "jsix/red-TASK-001",
                                        "baseline": {"asserts": 39, "tests": 37, "skips": 0},
                                        "current": {"asserts": 41, "tests": 38, "skips": 0},
                                        "delta": {"asserts": 2, "tests": 1, "skips": 0},
                                        "holdout_references": 0, "changed_test_files": 1},
                            "findings": [{"file": "tests/test_a.py",
                                          "before": {"asserts": 39, "tests": 37, "skips": 0},
                                          "after": {"asserts": 41, "tests": 38, "skips": 0},
                                          "content_changed": True}]},
            "traceability": {"ok": True, "skipped": False,
                             "summary": "traceability: 全10件トレース済",
                             "metrics": {"required": 10, "traced": 10, "untraced": 0,
                                         "junit_used": True,
                                         "per_pattern": {r"REQ-\d+": {"required": 10, "traced": 10,
                                                                      "untraced": [], "skipped": False},
                                                         r"PROP-\d+": {"required": 0, "traced": 0,
                                                                       "untraced": [], "skipped": True}}},
                             "findings": []},
        },
    },
    "g3": {
        "status": "passed",
        "checks": {
            "judge": {"ok": True, "skipped": False, "summary": "judge: PASS",
                      "metrics": {"verdict": "PASS", "attempt": 1, "max_auto_fix": 1,
                                  "reason_categories": []},
                      "findings": []},
        },
    },
}


@pytest.fixture
def generated(tmp_path):
    (tmp_path / ".jsix-checks.json").write_text('{"gates":{}}', encoding="utf-8")
    return pack.generate(RESULTS, True, tmp_path, tmp_path / "reports" / "evidence",
                         task_id="TASK-001", config_path=tmp_path / ".jsix-checks.json")


def test_all_files_generated(generated):
    names = sorted(p.name for p in generated.iterdir())
    assert names == [
        "00_summary.md", "01_traceability.md", "02_test_results.md",
        "03_coverage_mutation.md", "04_security.md", "05_scope_and_integrity.md",
        "06_judge_advisory.md", "07_approval.md", "env.json", "evidence.json",
    ]


def test_evidence_json_is_machine_readable(generated):
    doc = json.loads((generated / "evidence.json").read_text(encoding="utf-8"))
    assert doc["task_id"] == "TASK-001"
    assert doc["ok"] is True
    assert doc["gates"]["g2"]["checks"]["coverage"]["metrics"]["line_pct"] == 99.0


class TestThreeCategoriesStaySeparate:
    """証跡 / 参考所見 / 承認 を混ぜない。"""

    def test_judge_file_is_marked_advisory(self, generated):
        text = (generated / "06_judge_advisory.md").read_text(encoding="utf-8")
        assert "AI による参考所見" in text
        assert "単独で品質判定の根拠にしない" in text

    def test_deterministic_files_are_not_marked_advisory(self, generated):
        """証跡（01〜05）に参考所見のバナーを付けない。"""
        for name in ["01_traceability.md", "02_test_results.md",
                     "03_coverage_mutation.md", "04_security.md",
                     "05_scope_and_integrity.md"]:
            text = (generated / name).read_text(encoding="utf-8")
            assert "AI による参考所見" not in text, name
            assert "（証跡）" in text.splitlines()[0], name

    def test_summary_advisory_section_starts_empty(self, generated):
        """要約の LLM 記入欄は空で出力する（スクリプトは推定値を書かない）。"""
        text = (generated / "00_summary.md").read_text(encoding="utf-8")
        assert "_（未記入）_" in text
        assert "AI による参考所見" in text

    def test_approval_is_for_humans(self, generated):
        text = (generated / "07_approval.md").read_text(encoding="utf-8")
        assert "参考所見のみを根拠に承認しないでください" in text
        assert "承認者" in text or "レビュアー" in text


class TestReproducibility:
    """証跡には再現情報を必ず添付する。"""

    def test_env_has_reproduction_info(self, generated):
        env = json.loads((generated / "env.json").read_text(encoding="utf-8"))
        assert env["config_sha256"]
        assert env["generated_at"]
        assert "python" in env and "platform" in env

    def test_tool_versions_come_from_sarif(self, generated):
        env = json.loads((generated / "env.json").read_text(encoding="utf-8"))
        assert env["tools"] == [{"name": "bandit", "version": "1.8.6"}]

    def test_no_absolute_paths_leak(self, generated, tmp_path):
        """納品物に実行環境の絶対パスを残さない。"""
        env = json.loads((generated / "env.json").read_text(encoding="utf-8"))
        assert env["config_file"] == ".jsix-checks.json"
        for path in generated.iterdir():
            assert str(tmp_path) not in path.read_text(encoding="utf-8"), path.name


class TestContent:
    def test_traceability_reports_per_pattern(self, generated):
        text = (generated / "01_traceability.md").read_text(encoding="utf-8")
        assert "REQ-" in text
        assert "Spec に定義なし" in text  # PROP は未定義

    def test_test_results_separate_holdout(self, generated):
        text = (generated / "02_test_results.md").read_text(encoding="utf-8")
        assert "hold-out 受入テスト" in text
        assert "全経路からの不可視性を保証しない" in text
        assert "| 総数 | 37 |" in text and "| 総数 | 10 |" in text

    def test_survivors_are_listed_as_exploration_hints(self, generated):
        text = (generated / "03_coverage_mutation.md").read_text(encoding="utf-8")
        assert "生存したミュータント" in text
        assert "探索的テストの出発点" in text
        assert "app/workflow.py" in text

    def test_security_lists_severity_counts_and_tool(self, generated):
        text = (generated / "04_security.md").read_text(encoding="utf-8")
        assert "bandit 1.8.6" in text
        assert "抑止済み・集計対象外" in text

    def test_scope_and_tamper_show_baseline_comparison(self, generated):
        text = (generated / "05_scope_and_integrity.md").read_text(encoding="utf-8")
        assert "jsix/red-TASK-001" in text
        assert "| アサーション数 | 39 | 41 | +2 |" in text


class TestFailureCase:
    def test_failed_gate_is_recorded(self, tmp_path):
        results = {
            "g1": {"status": "failed", "checks": {
                "scope": {"ok": False, "skipped": False,
                          "summary": "scope: 許可範囲外の変更 1件",
                          "metrics": {"changed_files": 1, "violations": 1,
                                      "allow": ["app/**"], "deny": []},
                          "findings": [{"file": "infra/x.tf", "reason": "not-in-allow", "pattern": None}]}}},
            "g2": {"status": "not-run", "reason": "G1 が未通過のため未実行", "checks": {}},
        }
        target = pack.generate(results, False, tmp_path, tmp_path / "ev", task_id="T")
        summary = (target / "00_summary.md").read_text(encoding="utf-8")
        assert "**未通過のゲートあり**" in summary
        assert "⏭ 未実行" in summary
        scope_md = (target / "05_scope_and_integrity.md").read_text(encoding="utf-8")
        assert "infra/x.tf" in scope_md


def test_task_id_from_env(tmp_path, monkeypatch):
    monkeypatch.setenv("JSIX_TASK_ID", "TASK-042")
    assert pack.resolve_task_id(tmp_path) == "TASK-042"


def test_task_id_falls_back_to_untagged(tmp_path, monkeypatch):
    monkeypatch.delenv("JSIX_TASK_ID", raising=False)
    assert pack.resolve_task_id(tmp_path) == "untagged"


def test_summary_explains_missing_g4_row(generated):
    """G4 は本パッケージ自身なので一覧に出ない。読み手が混乱しないよう明記する。"""
    text = (generated / "00_summary.md").read_text(encoding="utf-8")
    assert "G4（証跡パッケージ生成）は本パッケージそのもの" in text


class TestRegeneration:
    """ゲートは Stop のたびに走るので、証跡も繰り返し生成される。"""

    def _gen(self, tmp_path, results=RESULTS):
        return pack.generate(results, True, tmp_path, tmp_path / "reports" / "evidence",
                             task_id="TASK-001", config_path=tmp_path / ".jsix-checks.json")

    def _fill_approval(self, target):
        path = target / "07_approval.md"
        path.write_text(path.read_text(encoding="utf-8").replace(
            "| レビュアー | | | ☐ |", "| レビュアー | 山田 | 2026-09-20 | ☑ |"), encoding="utf-8")

    def test_unchanged_results_do_not_rewrite(self, generated):
        """生成時刻以外が同じなら書き直さない（時刻を引用する設計書が収束しなくなるため）。"""
        before = {p.name: p.read_text(encoding="utf-8") for p in generated.iterdir()}
        again = self._gen(generated.parent.parent.parent)
        after = {p.name: p.read_text(encoding="utf-8") for p in again.iterdir()}
        assert after == before

    def test_changed_results_are_rewritten(self, generated):
        import copy

        results = copy.deepcopy(RESULTS)
        results["g2"]["checks"]["tests"]["summary"] = "tests: 全 38件 通過"
        target = self._gen(generated.parent.parent.parent, results)
        assert "38件" in (target / "02_test_results.md").read_text(encoding="utf-8")

    def test_changed_results_require_reapproval(self, generated):
        """検査結果が変わった場合は、同じ commit でも旧承認を履歴に退避する。"""
        import copy

        self._fill_approval(generated)
        results = copy.deepcopy(RESULTS)
        results["g2"]["checks"]["tests"]["summary"] = "tests: 全 38件 通過"
        target = self._gen(generated.parent.parent.parent, results)
        assert "山田" not in (target / "07_approval.md").read_text(encoding="utf-8")
        assert "再承認" in (target / "07_approval.md").read_text(encoding="utf-8")
        assert "山田" in next(target.glob("07_approval.*.md")).read_text(encoding="utf-8")

    def test_approval_for_old_commit_is_archived(self, generated, monkeypatch):
        """コードが変わったら承認は失効する。記録は消さず別名で残し、再承認を求める。"""
        self._fill_approval(generated)
        monkeypatch.setattr(pack.git, "head_sha", lambda base=None: "b" * 40)
        target = self._gen(generated.parent.parent.parent)
        current = (target / "07_approval.md").read_text(encoding="utf-8")
        assert "山田" not in current
        assert "再承認" in current
        archived = list(target.glob("07_approval.*.md"))
        assert len(archived) == 1
        assert "山田" in archived[0].read_text(encoding="utf-8")

    def test_same_evidence_preserves_filled_approval(self, generated):
        self._fill_approval(generated)
        target = self._gen(generated.parent.parent.parent)
        assert "山田" in (target / "07_approval.md").read_text(encoding="utf-8")

    def test_uncommitted_code_change_invalidates_approval(self, tmp_path):
        import subprocess

        (tmp_path / ".jsix-checks.json").write_text('{"gates":{}}', encoding="utf-8")
        source = tmp_path / "app.py"
        source.write_text("value = 1\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
        subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.com",
                        "commit", "-qm", "base"], cwd=tmp_path, check=True)
        target = self._gen(tmp_path)
        self._fill_approval(target)
        source.write_text("value = 2\n", encoding="utf-8")
        target = self._gen(tmp_path)
        assert "山田" not in (target / "07_approval.md").read_text(encoding="utf-8")
        assert "山田" in next(target.glob("07_approval.*.md")).read_text(encoding="utf-8")


def test_summary_marks_excluded_and_skipped(tmp_path):
    import copy

    results = copy.deepcopy(RESULTS)
    results["g3"] = {"status": "excluded", "reason": "--gates で対象外", "checks": {}}
    results["g2"]["checks"]["holdout"] = {"ok": True, "skipped": True,
                                               "summary": "未実施", "metrics": {}, "findings": []}
    target = pack.generate(results, True, tmp_path, tmp_path / "ev", task_id="T")
    summary = (target / "00_summary.md").read_text(encoding="utf-8")
    assert "対象外" in summary and "一部は未実施" in summary
    assert "全ゲート通過" not in summary


def test_coverage_section_shows_missing_lines(tmp_path):
    import copy

    results = copy.deepcopy(RESULTS)
    results["g2"]["checks"]["coverage"]["findings"][0]["missing"] = [72, 73, 74, 90]
    target = pack.generate(results, True, tmp_path, tmp_path / "ev", task_id="T")
    text = (target / "03_coverage_mutation.md").read_text(encoding="utf-8")
    assert "72-74, 90" in text


def test_survivor_without_file_is_rendered(tmp_path):
    import copy

    results = copy.deepcopy(RESULTS)
    results["g2"]["checks"]["mutation"]["findings"] = [{"mutator": "app.x.xǁSvcǁrun__mutmut_3"}]
    target = pack.generate(results, True, tmp_path, tmp_path / "ev", task_id="T")
    text = (target / "03_coverage_mutation.md").read_text(encoding="utf-8")
    assert "app.x.xǁSvcǁrun__mutmut_3" in text
    assert "`None`" not in text
