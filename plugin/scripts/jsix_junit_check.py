#!/usr/bin/env python3
"""J-SIX G2: JUnit XML の判定。

言語に依存しない。pytest / jest / gradle / go-junit-report など、多くのテスト
ランナーが JUnit XML を出力できる（または変換できる）。本スクリプトは
**XML を読むだけ**で、テストランナーを起動しない。

判定:
  - 失敗（failure）・エラー（error）が1件でもあれば不合格
  - `max_skipped` を指定した場合、スキップ数がそれを超えたら不合格
    （テストを skip で黙らせる操作を検出するため。既定は無制限）
  - `min_tests` を指定した場合、テスト総数がそれ未満なら不合格

使い方:
    python jsix_junit_check.py --file reports/junit.xml [--max-skipped 0] [--min-tests 10]

終了コード: 0=合格 / 1=不合格 / 2=入力エラー
"""
from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from jsix_result import Result, failed, passed  # noqa: E402


def _iter_suites(root: ET.Element):
    """<testsuites> でも <testsuite> 単体でも走査できるようにする。"""
    if root.tag == "testsuite":
        yield root
    for suite in root.iter("testsuite"):
        if suite is not root:
            yield suite


def parse_junit(xml_path: Path) -> dict:
    """JUnit XML から件数とテスト名を集計する。

    testsuites 要素に集計属性があってもそれを信用せず、testsuite を走査して
    合計する（ランナーによって集計属性の有無・意味が違うため）。
    """
    root = ET.parse(xml_path).getroot()

    totals = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    failed_tests: list = []
    skipped_tests: list = []
    test_names: list = []

    for suite in _iter_suites(root):
        for case in suite.findall("testcase"):
            totals["tests"] += 1
            classname = case.get("classname") or ""
            name = case.get("name") or ""
            full = f"{classname}.{name}" if classname else name
            test_names.append(full)

            if case.find("failure") is not None:
                totals["failures"] += 1
                failed_tests.append(full)
            elif case.find("error") is not None:
                totals["errors"] += 1
                failed_tests.append(full)
            elif case.find("skipped") is not None:
                totals["skipped"] += 1
                skipped_tests.append(full)

    return {
        **totals,
        "failed_tests": failed_tests,
        "skipped_tests": skipped_tests,
        "test_names": test_names,
    }


def check(cfg: dict, base_dir: Path | None = None, label: str = "tests") -> Result:
    """JUnit XML を判定する。

    label は出力の見出し（`tests` / `holdout` 等）。同じ判定ロジックを通常テストと
    hold-out 受入テストの両方で使うため、どちらの結果かが読んで分かるようにする。
    """
    base = base_dir or Path.cwd()
    junit = cfg.get("junit") or cfg.get("file")
    if not junit:
        return failed(f"{label}: 設定に junit（JUnit XML のパス）がありません")

    path = base / junit
    if not path.is_file():
        return failed(f"{label}: {junit} が見つかりません（テストを実行して JUnit XML を出力してください）")

    try:
        data = parse_junit(path)
    except ET.ParseError as exc:
        return failed(f"{label}: {junit} の解析に失敗: {exc}")

    metrics = {k: data[k] for k in ("tests", "failures", "errors", "skipped")}
    broken = data["failures"] + data["errors"]

    if broken:
        return failed(
            f"{label}: 失敗 {data['failures']}件 / エラー {data['errors']}件（全 {data['tests']}件）",
            metrics,
            [{"test": t, "kind": "failure"} for t in data["failed_tests"][:20]],
        )

    max_skipped = cfg.get("max_skipped")
    if max_skipped is not None and data["skipped"] > int(max_skipped):
        return failed(
            f"{label}: スキップ {data['skipped']}件 > 上限 {max_skipped}件",
            metrics,
            [{"test": t, "kind": "skipped"} for t in data["skipped_tests"][:20]],
        )

    min_tests = cfg.get("min_tests")
    if min_tests is not None and data["tests"] < int(min_tests):
        return failed(f"{label}: テスト総数 {data['tests']}件 < 下限 {min_tests}件", metrics)

    skip_note = f"（スキップ {data['skipped']}件）" if data["skipped"] else ""
    return passed(f"{label}: 全 {data['tests']}件 通過{skip_note}", metrics)


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="JUnit XML の品質ゲート")
    parser.add_argument("--file", required=True, help="JUnit XML のパス")
    parser.add_argument("--max-skipped", type=int, default=None, help="許容するスキップ数の上限")
    parser.add_argument("--min-tests", type=int, default=None, help="必要なテスト総数の下限")
    args = parser.parse_args(argv)

    cfg = {"junit": args.file}
    if args.max_skipped is not None:
        cfg["max_skipped"] = args.max_skipped
    if args.min_tests is not None:
        cfg["min_tests"] = args.min_tests

    result = check(cfg)
    print(("✅ " if result.ok else "❌ ") + result.summary)
    for f in result.findings:
        print(f"  - {f}")
    if not result.ok and "見つかりません" in result.summary:
        return 2
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
