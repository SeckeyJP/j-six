#!/usr/bin/env python3
"""J-SIX 決定論的チェック: 要件 ⇔ テストのトレーサビリティ検証。

要求 Spec に定義された要件ID（既定: REQ-\\d+）が、テストコードのどこかで参照されて
いるかを機械的に確認する。未トレースの要件があれば exit code 1 で終了する。

prompt 型 Hook と異なり LLM を介さず決定論的に判定するため、CI / Hook の
ゲートとして使える。言語非依存（テキスト走査）。

使い方:
    python jsix_traceability_check.py --requirements docs/requirement-spec.md --tests tests
    python jsix_traceability_check.py --pattern 'REQ-\\d+' --requirements ... --tests ...

終了コード: 0=全要件トレース済 / 1=未トレースあり / 2=入力エラー
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def extract_ids(text: str, pattern: str) -> set[str]:
    return set(re.findall(pattern, text))


def collect_test_ids(tests_dir: Path, pattern: str) -> set[str]:
    ids: set[str] = set()
    for path in tests_dir.rglob("*"):
        if path.is_file() and path.suffix in {".py", ".ts", ".js", ".java", ".go", ".rb"}:
            ids |= extract_ids(path.read_text(encoding="utf-8", errors="ignore"), pattern)
    return ids


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="要件⇔テストのトレーサビリティ検証")
    parser.add_argument("--requirements", required=True, help="要件IDを定義したファイル")
    parser.add_argument("--tests", required=True, help="テストコードのディレクトリ")
    parser.add_argument("--pattern", default=r"REQ-\d+", help="要件IDの正規表現（既定: REQ-\\d+）")
    args = parser.parse_args(argv)

    req_path = Path(args.requirements)
    tests_dir = Path(args.tests)
    if not req_path.is_file():
        print(f"ERROR: 要件ファイルが見つかりません: {req_path}", file=sys.stderr)
        return 2
    if not tests_dir.is_dir():
        print(f"ERROR: テストディレクトリが見つかりません: {tests_dir}", file=sys.stderr)
        return 2

    required = extract_ids(req_path.read_text(encoding="utf-8", errors="ignore"), args.pattern)
    tested = collect_test_ids(tests_dir, args.pattern)

    if not required:
        print(f"ERROR: 要件IDが1件も見つかりません（pattern={args.pattern}）", file=sys.stderr)
        return 2

    untraced = sorted(required - tested)
    traced = sorted(required & tested)

    print(f"要件総数: {len(required)} / トレース済: {len(traced)} / 未トレース: {len(untraced)}")
    if untraced:
        print("未トレースの要件:")
        for rid in untraced:
            print(f"  - {rid}")
        return 1
    print("✅ 全要件にテストが存在します")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
