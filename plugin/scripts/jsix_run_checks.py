#!/usr/bin/env python3
"""J-SIX 決定論的チェックのランナー（コマンド型 Hook のエントリポイント）。

カレントディレクトリに設定ファイル `.jsix-checks.json` が存在する場合のみ、
そこに定義された決定論的チェック（トレーサビリティ / カバレッジゲート）を実行する。
設定ファイルが無いプロジェクトでは**何もせず exit 0**（安全な no-op）。

これにより、グローバルに登録された Stop Hook が、オプトインしたプロジェクトでだけ
品質ゲートとして機能する。

`.jsix-checks.json` の例:
    {
      "traceability": { "requirements": "docs/requirement-spec.md", "tests": "tests" },
      "coverage": { "file": "coverage.xml", "min": 95 }
    }

終了コード: 0=全チェック合格 or 未設定 / 2=いずれか失敗（Stop Hook をブロック）
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from jsix_coverage_gate import read_line_rate  # noqa: E402
from jsix_traceability_check import collect_test_ids, extract_ids  # noqa: E402

CONFIG_NAME = ".jsix-checks.json"


def _check_traceability(cfg: dict) -> tuple[bool, str]:
    pattern = cfg.get("pattern", r"REQ-\d+")
    req_path = Path(cfg["requirements"])
    tests_dir = Path(cfg["tests"])
    if not req_path.is_file() or not tests_dir.is_dir():
        return False, f"traceability: 入力が見つかりません（{req_path} / {tests_dir}）"
    required = extract_ids(req_path.read_text(encoding="utf-8", errors="ignore"), pattern)
    tested = collect_test_ids(tests_dir, pattern)
    untraced = sorted(required - tested)
    if untraced:
        return False, f"traceability: 未トレース要件 {len(untraced)}件 → {', '.join(untraced)}"
    return True, f"traceability: 全{len(required)}要件トレース済"


def _check_coverage(cfg: dict) -> tuple[bool, str]:
    xml_path = Path(cfg.get("file", "coverage.xml"))
    minimum = float(cfg.get("min", 95))
    if not xml_path.is_file():
        return False, f"coverage: {xml_path} が見つかりません"
    pct = read_line_rate(xml_path) * 100
    if pct + 1e-9 < minimum:
        return False, f"coverage: {pct:.1f}% < 閾値{minimum:.1f}%"
    return True, f"coverage: {pct:.1f}% ≥ 閾値{minimum:.1f}%"


def main() -> int:
    config = Path.cwd() / CONFIG_NAME
    if not config.is_file():
        return 0  # 未設定プロジェクトでは no-op

    try:
        cfg = json.loads(config.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"J-SIX checks: {CONFIG_NAME} の解析に失敗: {exc}", file=sys.stderr)
        return 2

    checks = []
    if "traceability" in cfg:
        checks.append(_check_traceability(cfg["traceability"]))
    if "coverage" in cfg:
        checks.append(_check_coverage(cfg["coverage"]))

    failed = [msg for ok, msg in checks if not ok]
    passed = [msg for ok, msg in checks if ok]

    stream = sys.stderr if failed else sys.stdout
    for msg in passed:
        print(f"  ✅ {msg}", file=stream)
    for msg in failed:
        print(f"  ❌ {msg}", file=stream)

    if failed:
        print("J-SIX 品質ゲート未達。修正してください。", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
