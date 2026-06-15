#!/usr/bin/env python3
"""J-SIX 決定論的チェック: テストカバレッジの品質ゲート。

Cobertura 形式の coverage.xml（`coverage xml` / `pytest --cov-report=xml` /
多くの言語のカバレッジツールが出力可能）を読み、ライン網羅率が閾値未満なら
exit code 1 で終了する。`j-six:quality-metrics` Skill の品質ゲート判定を
決定論的に実行するためのバックエンド。

使い方:
    python jsix_coverage_gate.py --file coverage.xml --min 95

終了コード: 0=閾値以上 / 1=閾値未満 / 2=入力エラー
"""
from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def read_line_rate(xml_path: Path) -> float:
    """Cobertura ルート要素の line-rate（0.0-1.0）を返す。"""
    root = ET.parse(xml_path).getroot()
    rate = root.get("line-rate")
    if rate is None:
        raise ValueError("coverage.xml に line-rate 属性がありません（Cobertura形式か確認）")
    return float(rate)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="カバレッジ品質ゲート")
    parser.add_argument("--file", default="coverage.xml", help="Cobertura 形式の coverage.xml")
    parser.add_argument("--min", type=float, default=95.0, help="最低カバレッジ率（％）")
    args = parser.parse_args(argv)

    xml_path = Path(args.file)
    if not xml_path.is_file():
        print(f"ERROR: カバレッジファイルが見つかりません: {xml_path}", file=sys.stderr)
        return 2
    try:
        pct = read_line_rate(xml_path) * 100
    except (ET.ParseError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(f"カバレッジ: {pct:.1f}% / 閾値: {args.min:.1f}%")
    if pct + 1e-9 < args.min:
        print(f"❌ 品質ゲート未達（不足: {args.min - pct:.1f}pt）")
        return 1
    print("✅ 品質ゲート充足")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
