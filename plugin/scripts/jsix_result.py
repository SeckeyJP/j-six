#!/usr/bin/env python3
"""チェックの共通インタフェース。

各ゲートのチェックは `run(cfg, ctx) -> Result` を実装する。Result は
「合格したか」「証跡に載せる数値」「人間が読む指摘」の3つを持つ。
証跡パッケージ（G4）はこの Result をそのまま JSON 化する。
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Result:
    """1チェックの結果。

    ok:       合格なら True。ゲートの通過判定に使う
    summary:  1行の要約（人間が読む）
    metrics:  数値・件数（証跡パッケージの機械可読部に入る）
    findings: 個別の指摘（ファイル・行・内容）
    skipped:  実行しなかった場合 True（設定不足・前段打切り等）。ok の判定には含めない
    """

    ok: bool
    summary: str
    metrics: dict = field(default_factory=dict)
    findings: list = field(default_factory=list)
    skipped: bool = False

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "skipped": self.skipped,
            "summary": self.summary,
            "metrics": self.metrics,
            "findings": self.findings,
        }


def skipped(reason: str) -> Result:
    """設定が無い等の理由で実行しなかったことを表す Result。合格扱いにする。"""
    return Result(ok=True, summary=reason, skipped=True)


def failed(summary: str, metrics: dict | None = None, findings: list | None = None) -> Result:
    return Result(ok=False, summary=summary, metrics=metrics or {}, findings=findings or [])


def passed(summary: str, metrics: dict | None = None, findings: list | None = None) -> Result:
    return Result(ok=True, summary=summary, metrics=metrics or {}, findings=findings or [])


def missing_artifact(label: str, path, cfg: dict, hint: str = "") -> Result:
    """宣言された成果物が見つからない場合の Result。

    既定は**不合格**。成果物が無いのに合格にすると、検証していないものを
    検証済みとして扱うことになるため。

    ただし `optional: true` が明示されている場合はスキップ扱いにする。
    CI でのみ生成する成果物（secret スキャンや依存脆弱性の SARIF など）を、
    ローカルの内側ループでは要求しないための逃げ道である。
    """
    if cfg.get("optional"):
        return Result(
            ok=True,
            summary=f"{label}: {path} が無いためスキップ（optional 指定。CI で生成される想定）",
            skipped=True,
        )
    suffix = f"（{hint}）" if hint else ""
    return failed(f"{label}: {path} が見つかりません{suffix}")
