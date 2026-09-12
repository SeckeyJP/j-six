#!/usr/bin/env python3
"""J-SIX G2: 要件・性質 ⇔ テストのトレーサビリティ検証。

Spec に定義された ID（既定: `REQ-\\d+` と `PROP-\\d+`）が、テストコードのどこかで
参照されているかを機械的に確認する。未トレースがあれば不合格。

v2.1 の変更:
  - ID パターンを複数指定できる（REQ と PROP を同時に検証）
  - JUnit XML のテスト名も走査対象にできる（テスト名に ID を含める運用に対応）
  - パターンごとに件数を集計し、証跡に載せる

prompt 型 Hook と異なり LLM を介さず決定論的に判定するため、CI / Hook の
ゲートとして使える。言語非依存（テキスト走査）。

使い方:
    python jsix_traceability_check.py --requirements docs/requirement-spec.md --tests tests
    python jsix_traceability_check.py --requirements docs/spec.md --tests tests \\
        --ids 'REQ-\\d+' --ids 'PROP-\\d+' --junit reports/junit.xml

終了コード: 0=全トレース済 / 1=未トレースあり / 2=入力エラー
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from jsix_result import Result, failed, passed  # noqa: E402

DEFAULT_IDS = [r"REQ-\d+", r"PROP-\d+"]
SOURCE_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".jsx", ".java", ".kt", ".go", ".rb", ".cs", ".rs", ".php", ".scala", ".swift", ".feature"}


def extract_ids(text: str, pattern: str) -> set:
    """テキストから ID を抽出する。

    v2.0 から公開している関数。後方互換のためシグネチャを変えない。
    """
    return set(re.findall(pattern, text))


def collect_test_ids(tests_dir: Path, pattern: str) -> set:
    """テストディレクトリ配下のソースから ID を抽出する。

    v2.0 から公開している関数。後方互換のためシグネチャを変えない。
    """
    ids: set = set()
    for path in tests_dir.rglob("*"):
        if path.is_file() and path.suffix in SOURCE_SUFFIXES:
            ids |= extract_ids(path.read_text(encoding="utf-8", errors="ignore"), pattern)
    return ids


def collect_junit_ids(junit_path: Path, pattern: str) -> set:
    """JUnit XML のテスト名（classname.name）から ID を抽出する。"""
    import xml.etree.ElementTree as ET

    try:
        root = ET.parse(junit_path).getroot()
    except (ET.ParseError, OSError):
        return set()

    ids: set = set()
    for case in root.iter("testcase"):
        for value in (case.get("classname"), case.get("name")):
            if value:
                ids |= extract_ids(value, pattern)
    return ids


def _patterns_from(cfg: dict) -> list:
    ids = cfg.get("ids")
    if ids:
        return list(ids) if isinstance(ids, (list, tuple)) else [ids]
    if cfg.get("pattern"):  # v2.0 のキー名
        return [cfg["pattern"]]
    return list(DEFAULT_IDS)


def check(cfg: dict, base_dir: Path | None = None) -> Result:
    base = base_dir or Path.cwd()
    req_path = base / cfg.get("requirements", "docs/requirement-spec.md")
    tests_dir = base / cfg.get("tests", "tests")

    if not req_path.is_file():
        return failed(f"traceability: 要件ファイルが見つかりません（{cfg.get('requirements')}）")
    if not tests_dir.is_dir():
        return failed(f"traceability: テストディレクトリが見つかりません（{cfg.get('tests')}）")

    spec_text = req_path.read_text(encoding="utf-8", errors="ignore")
    junit = cfg.get("junit")
    junit_path = base / junit if junit else None

    per_pattern: dict = {}
    all_untraced: list = []
    total_required = 0
    total_traced = 0

    for pattern in _patterns_from(cfg):
        required = extract_ids(spec_text, pattern)
        if not required:
            # Spec に該当 ID が1件も無いパターンはスキップ（PROP 未導入のプロジェクト向け）
            per_pattern[pattern] = {"required": 0, "traced": 0, "untraced": [], "skipped": True}
            continue

        tested = collect_test_ids(tests_dir, pattern)
        if junit_path and junit_path.is_file():
            tested |= collect_junit_ids(junit_path, pattern)

        untraced = sorted(required - tested)
        per_pattern[pattern] = {
            "required": len(required),
            "traced": len(required & tested),
            "untraced": untraced,
            "skipped": False,
        }
        total_required += len(required)
        total_traced += len(required & tested)
        all_untraced.extend(untraced)

    if total_required == 0:
        patterns = ", ".join(_patterns_from(cfg))
        return failed(f"traceability: 要件IDが1件も見つかりません（pattern: {patterns}）")

    metrics = {
        "required": total_required,
        "traced": total_traced,
        "untraced": len(all_untraced),
        "per_pattern": per_pattern,
        "junit_used": bool(junit_path and junit_path.is_file()),
    }

    if all_untraced:
        return failed(
            f"traceability: 未トレース {len(all_untraced)}件 / 全{total_required}件 → {', '.join(all_untraced[:10])}",
            metrics,
            [{"id": i, "kind": "untraced"} for i in all_untraced],
        )

    detail = " / ".join(
        f"{pat}: {info['traced']}件" for pat, info in per_pattern.items() if not info["skipped"]
    )
    return passed(f"traceability: 全{total_required}件トレース済（{detail}）", metrics)


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="要件・性質 ⇔ テストのトレーサビリティ検証")
    parser.add_argument("--requirements", required=True, help="要件IDを定義したファイル")
    parser.add_argument("--tests", required=True, help="テストコードのディレクトリ")
    parser.add_argument("--ids", action="append", default=None,
                        help=r"IDの正規表現（複数指定可。既定: REQ-\d+ と PROP-\d+）")
    parser.add_argument("--pattern", default=None, help="[非推奨] --ids を使ってください")
    parser.add_argument("--junit", default=None, help="JUnit XML（テスト名も走査対象にする）")
    args = parser.parse_args(argv)

    cfg = {"requirements": args.requirements, "tests": args.tests}
    if args.ids:
        cfg["ids"] = args.ids
    elif args.pattern:
        cfg["ids"] = [args.pattern]
    if args.junit:
        cfg["junit"] = args.junit

    result = check(cfg)
    print(("✅ " if result.ok else "❌ ") + result.summary)
    for f in result.findings[:30]:
        print(f"  - 未トレース: {f['id']}")
    if not result.ok and "見つかりません" in result.summary:
        return 2
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
