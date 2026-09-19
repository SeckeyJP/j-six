#!/usr/bin/env python3
"""J-SIX G4: 証跡パッケージの生成。

G1〜G3 の結果を、人間レビュー用・顧客納品用に構造化して出力する。

## 設計原則: 3つの区分を混ぜない

| 区分 | 内容 | 扱い |
|---|---|---|
| 証跡（Evidence） | 決定論的検証の生出力と集計 | 納品可。再現情報を必ず添付 |
| 参考所見（Advisory） | LLM judge の判定・LLM 要約 | 「AI による参考所見」と明記。単独で品質判定の根拠にしない |
| 承認（Approval） | 人間レビュアーの確認欄・指摘・是正記録 | 人間が記入する |

参考所見を証跡と分けるのは、LLM の判定が再実行で同じ結果になるとは限らず、
第三者が同じ手順で確かめられないためである。証跡は誰が何度実行しても同じ値になる。

## 出力

    reports/evidence/<task-id>/
      evidence.json             機械可読の全結果
      00_summary.md             1ページ要約
      01_traceability.md        REQ / PROP ⇔ テスト
      02_test_results.md        テスト結果 ＋ hold-out
      03_coverage_mutation.md   カバレッジと mutation score
      04_security.md            SARIF 集計
      05_scope_and_integrity.md スコープ検査・テスト改変検出
      06_judge_advisory.md      G3 judge の判定（参考所見）
      07_approval.md            人間レビュー記録（承認欄）
      env.json                  commit SHA / ツール版 / 実行日時 / 設定ハッシュ

`00_summary.md` の「参考所見」節は LLM が後から追記する場所として空で出力する
（`evidence-pack` Skill が担当）。本スクリプトは推定値を一切書かない。

使い方（通常は jsix_run_checks.py から呼ばれる）:
    python jsix_evidence_pack.py --results reports/gate.json --out reports/evidence/

終了コード: 0
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import jsix_config as config  # noqa: E402
import jsix_gitutil as git  # noqa: E402
from jsix_result import Result, passed  # noqa: E402

ADVISORY_BANNER = (
    "> ⚠ **AI による参考所見**。決定論的な検証結果（証跡）ではありません。\n"
    "> 単独で品質判定の根拠にしないでください。数値は必ず証跡側（01〜05）を参照してください。\n"
)


# --------------------------------------------------------------------------
# 収集
# --------------------------------------------------------------------------

def resolve_task_id(base: Path) -> str:
    """タスクIDを決める: $JSIX_TASK_ID → 最新の jsix/red-* タグ → 'untagged'。"""
    task_id = os.environ.get("JSIX_TASK_ID")
    if task_id:
        return task_id
    tag = git.latest_tag("jsix/red-*", cwd=base)
    if tag:
        return tag.split("jsix/red-", 1)[-1]
    return "untagged"


def _tool_versions(results: dict) -> list:
    """証跡に載せるツール名と版。SARIF から取れたものを使う（自称ではなく出力由来）。"""
    tools: list = []
    for gate in results.values():
        for res in (gate.get("checks") or {}).values():
            for tool in (res.get("metrics") or {}).get("tools") or []:
                if tool not in tools:
                    tools.append(tool)
    return tools


def _relative_to_base(path: Path | None, base: Path) -> str | None:
    """証跡に載せるパスをプロジェクト基準の相対パスにする。

    証跡は顧客への納品物になり得るため、実行環境の絶対パス（ホームディレクトリ名や
    社内のディレクトリ構成）を残さない。
    """
    if path is None:
        return None
    try:
        return Path(path).resolve().relative_to(Path(base).resolve()).as_posix()
    except ValueError:
        return Path(path).name


def build_env(base: Path, results: dict, config_path: Path | None) -> dict:
    """再現情報。第三者が同じ結果を得るために必要なものだけを入れる。"""
    config_hash = None
    if config_path and Path(config_path).is_file():
        config_hash = hashlib.sha256(Path(config_path).read_bytes()).hexdigest()

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "commit_sha": git.head_sha(base),
        "baseline_ref": _baseline_ref(results),
        "config_file": _relative_to_base(config_path, base),
        "config_sha256": config_hash,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "tools": _tool_versions(results),
    }


def _baseline_ref(results: dict):
    tamper = ((results.get("g2") or {}).get("checks") or {}).get("test_tamper") or {}
    return (tamper.get("metrics") or {}).get("baseline_ref")


def _check(results: dict, gate: str, name: str) -> dict | None:
    return ((results.get(gate) or {}).get("checks") or {}).get(name)


# --------------------------------------------------------------------------
# Markdown 生成
# --------------------------------------------------------------------------

def _status_mark(res: dict | None) -> str:
    if res is None:
        return "—"
    if res.get("skipped"):
        return "⏭ 未実施"
    return "✅ 合格" if res.get("ok") else "❌ 不合格"


def _gate_rows(results: dict) -> list:
    rows = []
    for gate in config.GATE_ORDER:
        info = results.get(gate)
        if not info:
            continue
        if info.get("status") == "not-run":
            rows.append((gate.upper(), "—", "⏭ 未実行", info.get("reason", "")))
            continue
        for name, res in (info.get("checks") or {}).items():
            rows.append((gate.upper(), name, _status_mark(res), res.get("summary", "")))
    return rows


def render_summary(task_id: str, results: dict, env: dict, overall_ok: bool) -> str:
    rows = "\n".join(f"| {g} | `{n}` | {m} | {s} |" for g, n, m, s in _gate_rows(results))
    verdict = "全ゲート通過" if overall_ok else "**未通過のゲートあり**"

    return f"""# 00. 要約 — {task_id}

**判定**: {verdict}
**commit**: `{env.get('commit_sha') or '不明'}`
**生成日時**: {env.get('generated_at')}
**基準点（RED タグ）**: `{env.get('baseline_ref') or '未設定'}`

## ゲート結果一覧（証跡）

| ゲート | チェック | 判定 | 内容 |
|---|---|---|---|
{rows}

各項目の詳細は 01〜05（証跡）と 06（参考所見）を参照。再現情報は `env.json`。

> G4（証跡パッケージ生成）は本パッケージそのものであるため、上表には現れない。

## 変更概要・リスク箇所・計画からの逸脱（参考所見）

{ADVISORY_BANNER}
<!-- evidence-pack Skill がここに LLM 要約を追記する。
     未記入のまま納品しないこと。記入する場合も、数値は 01〜05 から引用し、
     推定値を書かないこと。 -->

_（未記入）_

## 区分の説明

| 区分 | 該当ファイル | 納品時の扱い |
|---|---|---|
| 証跡（Evidence） | 01〜05, `evidence.json`, `env.json` | 納品可。再現情報を添付済み |
| 参考所見（Advisory） | 06, 本ファイルの要約節 | 「AI による参考所見」と明記。単独で判定根拠にしない |
| 承認（Approval） | 07 | 人間が記入する。承認者と日付が必須 |
"""


def render_traceability(res: dict | None) -> str:
    body = ["# 01. トレーサビリティ（証跡）", ""]
    if res is None:
        body.append("トレーサビリティ検証は設定されていません。")
        return "\n".join(body) + "\n"

    m = res.get("metrics") or {}
    body += [
        f"**判定**: {_status_mark(res)} — {res.get('summary','')}",
        "",
        "| 項目 | 値 |",
        "|---|---|",
        f"| 要件・性質の総数 | {m.get('required', '—')} |",
        f"| テストが存在するもの | {m.get('traced', '—')} |",
        f"| 未トレース | {m.get('untraced', '—')} |",
        f"| JUnit のテスト名も走査 | {'はい' if m.get('junit_used') else 'いいえ'} |",
        "",
        "## ID パターン別",
        "",
        "| パターン | 定義数 | トレース済 | 未トレース |",
        "|---|---|---|---|",
    ]
    for pattern, info in (m.get("per_pattern") or {}).items():
        if info.get("skipped"):
            body.append(f"| `{pattern}` | 0 | — | — （Spec に定義なし） |")
        else:
            untraced = ", ".join(info.get("untraced") or []) or "なし"
            body.append(f"| `{pattern}` | {info.get('required')} | {info.get('traced')} | {untraced} |")

    findings = res.get("findings") or []
    if findings:
        body += ["", "## 未トレースの要件・性質", ""]
        body += [f"- `{f.get('id')}`" for f in findings]
    return "\n".join(body) + "\n"


def render_test_results(tests: dict | None, holdout: dict | None) -> str:
    body = ["# 02. テスト結果（証跡）", ""]

    for label, res, note in (
        ("通常テスト", tests, "RED Phase で作成したテスト。Green Phase から可視。"),
        ("hold-out 受入テスト", holdout,
         "実装を書くエージェントが読めない受入テスト。可視テストへの過剰適合を検出する。"),
    ):
        body += [f"## {label}", "", f"_{note}_", ""]
        if res is None:
            body += ["設定されていません。", ""]
            continue
        m = res.get("metrics") or {}
        body += [
            f"**判定**: {_status_mark(res)} — {res.get('summary','')}",
            "",
            "| 項目 | 件数 |",
            "|---|---|",
            f"| 総数 | {m.get('tests', '—')} |",
            f"| 失敗 | {m.get('failures', '—')} |",
            f"| エラー | {m.get('errors', '—')} |",
            f"| スキップ | {m.get('skipped', '—')} |",
            "",
        ]
        failed_list = [f for f in (res.get("findings") or []) if f.get("kind") == "failure"]
        if failed_list:
            body += ["### 失敗したテスト", ""] + [f"- `{f['test']}`" for f in failed_list] + [""]
        skipped_list = [f for f in (res.get("findings") or []) if f.get("kind") == "skipped"]
        if skipped_list:
            body += ["### スキップされたテスト", ""] + [f"- `{f['test']}`" for f in skipped_list] + [""]
    return "\n".join(body) + "\n"


def render_coverage_mutation(coverage: dict | None, mutation: dict | None) -> str:
    body = ["# 03. カバレッジと mutation score（証跡）", ""]

    body += ["## カバレッジ", ""]
    if coverage is None:
        body += ["設定されていません。", ""]
    else:
        m = coverage.get("metrics") or {}
        body += [
            f"**判定**: {_status_mark(coverage)} — {coverage.get('summary','')}",
            "",
            "| 項目 | 値 |",
            "|---|---|",
            f"| ライン網羅率 | {m.get('line_pct', '—')}% |",
            f"| 閾値 | {m.get('min', '未設定')} |",
            f"| 形式 | {m.get('format', '—')} |",
            f"| 対象ファイル数 | {m.get('files', '—')} |",
            "",
        ]
        low = coverage.get("findings") or []
        if low:
            body += ["### 網羅率の低いファイル", "",
                     "| ファイル | 網羅率 | 到達行 / 全行 |", "|---|---|---|"]
            body += [f"| `{f['file']}` | {f['line_pct']}% | {f['covered']} / {f['total']} |" for f in low]
            body.append("")

    body += ["## mutation score", "",
             "_カバレッジは「テストが実行した行」を測るが、mutation score は"
             "「テストが誤りを検出できるか」を測る。_", ""]
    if mutation is None:
        body += ["設定されていません（mutation testing 未導入）。", ""]
    else:
        m = mutation.get("metrics") or {}
        body += [
            f"**判定**: {_status_mark(mutation)} — {mutation.get('summary','')}",
            "",
            "| 項目 | 値 |",
            "|---|---|",
            f"| score | {m.get('score', '—')}% |",
            f"| 閾値 | {m.get('min_score', '未設定（計測のみ）')} |",
            f"| 殺したミュータント | {m.get('killed', '—')} |",
            f"| 生存したミュータント | {m.get('survived', '—')} |",
            f"| 判定対象外 | {m.get('ignored', '—')} |",
            f"| 対象範囲 | {m.get('scope', '—')} |",
            "",
        ]
        survivors = mutation.get("findings") or []
        if survivors:
            body += [
                "### 生存したミュータント",
                "",
                "_テストが通っているのに振る舞いが固定されていない箇所。"
                "探索的テストの出発点として質が高い。_",
                "",
                "| ファイル | 行 | 変異 |", "|---|---|---|",
            ]
            body += [f"| `{s.get('file')}` | {s.get('line', '—')} | {s.get('mutator', '—')} |"
                     for s in survivors]
            body.append("")
    return "\n".join(body) + "\n"


def render_security(results: dict) -> str:
    body = ["# 04. セキュリティ（証跡）", "",
            "_SARIF（OASIS 標準）の集計。解析ツールは利用者側が選ぶ。_", ""]
    found = False
    for name, title in (("sast", "静的解析（SAST）"), ("secrets", "秘密情報スキャン"), ("deps", "依存脆弱性")):
        res = _check(results, "g1", name)
        if res is None:
            continue
        found = True
        m = res.get("metrics") or {}
        tools = ", ".join(f"{t.get('name')} {t.get('version') or ''}".strip()
                          for t in (m.get("tools") or [])) or "—"
        body += [
            f"## {title}",
            "",
            f"**判定**: {_status_mark(res)} — {res.get('summary','')}",
            f"**ツール**: {tools}",
            "",
            "| severity | 件数 |",
            "|---|---|",
            f"| error | {m.get('error', 0)} |",
            f"| warning | {m.get('warning', 0)} |",
            f"| note | {m.get('note', 0)} |",
            f"| （抑止済み・集計対象外） | {m.get('suppressed', 0)} |",
            "",
            f"**閾値**: {m.get('max_severity', '未設定（集計のみ）')}",
            "",
        ]
        findings = res.get("findings") or []
        if findings:
            body += ["### 指摘一覧", "", "| severity | 箇所 | ルール | 内容 |", "|---|---|---|---|"]
            body += [
                f"| {f.get('level')} | `{f.get('file','?')}:{f.get('line','?')}` | "
                f"`{f.get('rule','')}` | {f.get('message','')} |"
                for f in findings
            ]
            body.append("")
    if not found:
        body += ["セキュリティ検査は設定されていません。", ""]
    return "\n".join(body) + "\n"


def render_scope_integrity(scope: dict | None, tamper: dict | None) -> str:
    body = ["# 05. スコープと監督面の健全性（証跡）", ""]

    body += ["## スコープ検査", "",
             "_変更ファイルがタスクの許可リストに収まっているか。許可リストは"
             "Phase 3 で人間が承認したもの。_", ""]
    if scope is None:
        body += ["設定されていません。", ""]
    else:
        m = scope.get("metrics") or {}
        body += [
            f"**判定**: {_status_mark(scope)} — {scope.get('summary','')}",
            "",
            "| 項目 | 値 |",
            "|---|---|",
            f"| 変更ファイル数 | {m.get('changed_files', '—')} |",
            f"| 違反 | {m.get('violations', '—')} |",
            f"| allow | {', '.join(f'`{p}`' for p in (m.get('allow') or [])) or '—'} |",
            f"| deny | {', '.join(f'`{p}`' for p in (m.get('deny') or [])) or '—'} |",
            "",
        ]
        violations = scope.get("findings") or []
        if violations:
            body += ["### 許可範囲外の変更", "", "| ファイル | 理由 | 一致したパターン |", "|---|---|---|"]
            body += [f"| `{v['file']}` | {v['reason']} | `{v.get('pattern') or '—'}` |" for v in violations]
            body.append("")

    body += ["## テスト改変検出", "",
             "_RED タグ以降にテストが弱められていないか。検出するのは差分そのものではなく"
             "弱体化（アサーション・テスト関数の減少、無効化マーカーの増加、hold-out 参照）。_", ""]
    if tamper is None:
        body += ["設定されていません。", ""]
    else:
        m = tamper.get("metrics") or {}
        before, after = m.get("baseline") or {}, m.get("current") or {}
        delta = m.get("delta") or {}
        body += [f"**判定**: {_status_mark(tamper)} — {tamper.get('summary','')}", ""]
        if before or after:
            body += [
                f"**基準点**: `{m.get('baseline_ref') or '未設定'}`",
                "",
                "| 指標 | 基準点 | 現在 | 増減 |",
                "|---|---|---|---|",
                f"| アサーション数 | {before.get('asserts','—')} | {after.get('asserts','—')} | {delta.get('asserts','—'):+} |"
                if isinstance(delta.get("asserts"), int) else
                f"| アサーション数 | {before.get('asserts','—')} | {after.get('asserts','—')} | — |",
                f"| テスト関数数 | {before.get('tests','—')} | {after.get('tests','—')} | {delta.get('tests','—'):+} |"
                if isinstance(delta.get("tests"), int) else
                f"| テスト関数数 | {before.get('tests','—')} | {after.get('tests','—')} | — |",
                f"| 無効化マーカー数 | {before.get('skips','—')} | {after.get('skips','—')} | {delta.get('skips','—'):+} |"
                if isinstance(delta.get("skips"), int) else
                f"| 無効化マーカー数 | {before.get('skips','—')} | {after.get('skips','—')} | — |",
                "",
                f"実装から hold-out への参照: {m.get('holdout_references', 0)} 件",
                f"／ 差分のあったテストファイル: {m.get('changed_test_files', 0)} 件",
                "",
            ]
        findings = tamper.get("findings") or []
        blocking = [f for f in findings if f.get("kind")]
        if blocking:
            body += ["### 検出された弱体化", ""] + [
                f"- **{f['kind']}**: {f.get('detail') or f.get('file')}" for f in blocking
            ] + [""]
        changed = [f for f in findings if not f.get("kind") and f.get("file")]
        if changed:
            body += ["### 差分のあったテストファイル（弱体化なし）", "",
                     "| ファイル | 基準点 (assert/test/skip) | 現在 | 内容変更 |", "|---|---|---|---|"]
            for f in changed:
                b, a = f.get("before", {}), f.get("after", {})
                body.append(
                    f"| `{f['file']}` | {b.get('asserts')}/{b.get('tests')}/{b.get('skips')} | "
                    f"{a.get('asserts')}/{a.get('tests')}/{a.get('skips')} | "
                    f"{'あり' if f.get('content_changed') else 'なし'} |"
                )
            body.append("")
    return "\n".join(body) + "\n"


def render_judge(res: dict | None) -> str:
    body = ["# 06. 意図・スコープ判定（参考所見）", "", ADVISORY_BANNER, ""]
    if res is None:
        body += ["G3（意図・スコープ判定）は設定されていません。", ""]
        return "\n".join(body) + "\n"

    m = res.get("metrics") or {}
    body += [
        f"**判定**: {m.get('verdict', '—')}",
        f"**試行回数**: {m.get('attempt', '—')} / 自動修正の上限 {m.get('max_auto_fix', '—')}",
        f"**人間へのエスカレーション**: {'必要' if m.get('escalate_to_human') else '不要'}",
        "",
        f"{res.get('summary','')}",
        "",
    ]
    reasons = res.get("findings") or []
    if reasons:
        body += ["## 却下理由", "", "| 分類 | 内容 | 箇所 |", "|---|---|---|"]
        for r in reasons:
            loc = f"`{r.get('file')}:{r.get('line')}`" if r.get("file") else "—"
            body.append(f"| {r.get('category','—')} | {r.get('detail','')} | {loc} |")
        body.append("")
    body += [
        "## この判定の限界",
        "",
        "- LLM の判定は再実行で同じ結果になるとは限らない（証跡と異なり再現性がない）",
        "- 判定対象は「正確性・要件未充足・スコープ逸脱」の3点のみ。網羅的なレビューではない",
        "- スタイル・命名・拡張性の指摘は意図的に禁止している",
        "",
    ]
    return "\n".join(body) + "\n"


def render_approval(task_id: str, env: dict) -> str:
    return f"""# 07. 人間レビュー記録（承認）

**対象タスク**: {task_id}
**対象 commit**: `{env.get('commit_sha') or '不明'}`

証跡（01〜05）と参考所見（06）を確認した上で記入してください。
**参考所見のみを根拠に承認しないでください。**

## 確認項目

| # | 確認事項 | 確認者 | 日付 | 結果 |
|---|---|---|---|---|
| 1 | 証跡の各ゲートが通過していることを確認した | | | ☐ |
| 2 | 業務ロジックの妥当性を確認した（機械では判定できない領域） | | | ☐ |
| 3 | 設計判断が ADR に記録されていることを確認した | | | ☐ |
| 4 | 探索的テストを実施した | | | ☐ |

## 指摘事項

| # | 指摘内容 | 重要度 | 対応 | 是正確認日 |
|---|---|---|---|---|
| 1 | | | | |

## 承認

| 役割 | 氏名 | 日付 | 承認 |
|---|---|---|---|
| レビュアー | | | ☐ |
| 責任者 | | | ☐ |
"""


# --------------------------------------------------------------------------
# 生成
# --------------------------------------------------------------------------

def _without_timestamp(evidence: dict) -> dict:
    env = dict(evidence.get("env") or {})
    env.pop("generated_at", None)
    return {**evidence, "env": env}


def _unchanged(target: Path, evidence: dict) -> bool:
    """前回の証跡と、生成時刻以外が同じか。"""
    try:
        previous = json.loads((target / "evidence.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return _without_timestamp(previous) == _without_timestamp(evidence)


_APPROVAL_COMMIT = re.compile(r"\*\*対象 commit\*\*: `([^`]*)`")


def _preserve_approval(target: Path, task_id: str, env: dict) -> str | None:
    """人間が記入した承認欄を守る。書くべき 07 の内容を返す（None なら既存を残す）。

    承認は人間だけが書く区分であり、ゲートの再実行で消してはならない。
    - 未記入（テンプレートのまま）なら、新しいテンプレートで置き換える
    - 記入済みで対象 commit が同じなら、そのまま残す
    - 記入済みで commit が変わったなら、承認は失効する。記録は別名で残し、
      再承認を求めるテンプレートを置く
    """
    path = target / "07_approval.md"
    fresh = render_approval(task_id, env)
    if not path.is_file():
        return fresh
    existing = path.read_text(encoding="utf-8")
    m = _APPROVAL_COMMIT.search(existing)
    old_commit = m.group(1) if m else None
    blank_for_old = render_approval(task_id, {"commit_sha": old_commit if old_commit != "不明" else None})
    if existing in (blank_for_old, fresh) or _strip_reapproval(existing) == blank_for_old:
        return fresh  # 未記入
    new_commit = env.get("commit_sha") or "不明"
    if old_commit == new_commit:
        return None  # 記入済み・同じ commit
    archive = target / f"07_approval.{(old_commit or 'unknown')[:12]}.md"
    archive.write_text(existing, encoding="utf-8")
    return fresh.replace(
        "証跡（01〜05）と参考所見（06）を確認した上で記入してください。",
        f"> **再承認が必要です。**前回の承認（commit `{old_commit}`）の後にコードが変わりました。"
        f"前回の記録は `{archive.name}` に保存しています。\n\n"
        "証跡（01〜05）と参考所見（06）を確認した上で記入してください。",
        1,
    )


def _strip_reapproval(text: str) -> str:
    """再承認の注記を除いた本文（未記入の再承認テンプレートを未記入と判定するため）。"""
    return re.sub(r"> \*\*再承認が必要です。\*\*.*?\n\n", "", text, count=1, flags=re.S)


def generate(results: dict, overall_ok: bool, base: Path, out_dir: Path,
             task_id: str | None = None, config_path: Path | None = None) -> Path:
    """証跡パッケージを生成し、出力ディレクトリを返す。

    ゲートは Stop のたびに走るため、生成時刻以外が前回と同じなら書き直さない。
    書き直すと、証跡の時刻を引用する設計書がいつまでも収束しない。
    人間が記入した承認欄（07）は上書きしない（_preserve_approval）。
    """
    task_id = task_id or resolve_task_id(base)
    target = Path(out_dir) / task_id
    target.mkdir(parents=True, exist_ok=True)

    env = build_env(base, results, config_path)
    evidence = {"task_id": task_id, "ok": overall_ok, "env": env, "gates": results}
    if _unchanged(target, evidence):
        return target

    files = {
        "00_summary.md": render_summary(task_id, results, env, overall_ok),
        "01_traceability.md": render_traceability(_check(results, "g2", "traceability")),
        "02_test_results.md": render_test_results(_check(results, "g2", "tests"),
                                                  _check(results, "g2", "holdout")),
        "03_coverage_mutation.md": render_coverage_mutation(_check(results, "g2", "coverage"),
                                                            _check(results, "g2", "mutation")),
        "04_security.md": render_security(results),
        "05_scope_and_integrity.md": render_scope_integrity(_check(results, "g1", "scope"),
                                                            _check(results, "g2", "test_tamper")),
        "06_judge_advisory.md": render_judge(_check(results, "g3", "judge")),
    }
    approval = _preserve_approval(target, task_id, env)
    if approval is not None:
        files["07_approval.md"] = approval
    for name, text in files.items():
        (target / name).write_text(text, encoding="utf-8")

    (target / "env.json").write_text(
        json.dumps(env, ensure_ascii=False, indent=2), encoding="utf-8")
    (target / "evidence.json").write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def check(cfg: dict, base: Path, results: dict, overall_ok: bool,
          config_path: Path | None = None) -> Result:
    """ランナーから呼ばれる G4 のチェック。"""
    out_dir = base / cfg.get("out", "reports/evidence/")
    target = generate(results, overall_ok, base, out_dir, config_path=config_path)
    rel = _relative_to_base(target, base) or str(target)
    return passed(f"evidence: 証跡パッケージを生成しました → {rel}/", {"out": rel})


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="証跡パッケージの生成")
    parser.add_argument("--results", required=True, help="jsix_run_checks.py --json の出力")
    parser.add_argument("--out", default="reports/evidence/", help="出力先ディレクトリ")
    parser.add_argument("--task-id", default=None, help="タスクID（既定: $JSIX_TASK_ID → 最新 RED タグ）")
    parser.add_argument("--dir", default=None, help="対象プロジェクト（既定: カレント）")
    args = parser.parse_args(argv)

    base = Path(args.dir) if args.dir else Path.cwd()
    doc = json.loads(Path(args.results).read_text(encoding="utf-8"))
    target = generate(doc.get("gates", {}), doc.get("ok", False), base,
                      base / args.out, args.task_id, base / config.CONFIG_NAME)
    print(f"証跡パッケージを生成しました: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
