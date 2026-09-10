#!/usr/bin/env python3
"""green-agent 用の PreToolUse Hook: 監督面（テスト）への接触を機械的に拒否する。

green-agent の本文に「テストを触るな」と書いても、それは助言でしかない。
Hook は決定論的に効くため、以下を確実に止められる。

  - `tests/` 配下への Edit / Write
  - `tests/acceptance/`（hold-out）の Read

hold-out の読み取りまで禁じるのは、実装が hold-out に適合してしまうと監督面としての
意味が消えるためである（SpecBench が示す reward hacking への対処）。

Hook の入出力仕様に従い、標準入力から JSON を読み、拒否する場合は
`{"decision": "block", "reason": "..."}` を標準出力に返す。
判断できない入力（想定外の形）は**通す**（Hook の誤作動で作業を止めないため）。

環境変数:
  JSIX_TESTS_DIRS    書込禁止のディレクトリ（`:` 区切り。既定 "tests")
  JSIX_HOLDOUT_DIRS  読取禁止のディレクトリ（`:` 区切り。既定 "tests/acceptance")
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

WRITE_TOOLS = {"Edit", "Write", "NotebookEdit", "MultiEdit"}
READ_TOOLS = {"Read"}


def _dirs(env_name: str, default: str) -> list:
    return [d.strip().strip("/") for d in os.environ.get(env_name, default).split(":") if d.strip()]


def _relative(path_str: str) -> str:
    """作業ディレクトリからの相対パス（POSIX 区切り）へ正規化する。"""
    try:
        path = Path(path_str).resolve()
    except OSError:
        return path_str.replace("\\", "/")
    try:
        return path.relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _under(rel: str, directory: str) -> bool:
    return rel == directory or rel.startswith(directory + "/")


def decide(payload: dict) -> dict | None:
    """ブロックすべきなら decision を返す。問題なければ None。"""
    tool = payload.get("tool_name") or payload.get("toolName") or ""
    params = payload.get("tool_input") or payload.get("toolInput") or {}
    if not isinstance(params, dict):
        return None

    target = params.get("file_path") or params.get("path") or params.get("notebook_path")
    if not target:
        return None

    rel = _relative(str(target))

    if tool in READ_TOOLS:
        for holdout in _dirs("JSIX_HOLDOUT_DIRS", "tests/acceptance"):
            if _under(rel, holdout):
                return {
                    "decision": "block",
                    "reason": (
                        f"J-SIX G2: hold-out 受入テスト（{holdout}/）は Green Phase から読めません。"
                        "実装が hold-out に適合すると監督面としての意味が消えるためです。"
                        "テストの形ではなく Spec の受入条件を読んで実装してください。"
                    ),
                }
        return None

    if tool in WRITE_TOOLS:
        for tests_dir in _dirs("JSIX_TESTS_DIRS", "tests"):
            if _under(rel, tests_dir):
                return {
                    "decision": "block",
                    "reason": (
                        f"J-SIX G2: テストコード（{tests_dir}/）は Green Phase では変更できません。"
                        "テストは実装の品質を測る監督面であり、書き換えると G2 のテスト改変検出でブロックされます。"
                        "テストの期待値が誤っていると考える場合は、修正せず人間に報告してください。"
                    ),
                }
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # 想定外の入力では止めない
    if not isinstance(payload, dict):
        return 0

    decision = decide(payload)
    if decision:
        print(json.dumps(decision, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
