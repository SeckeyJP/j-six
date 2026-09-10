#!/usr/bin/env python3
"""J-SIX G2: テストカバレッジの品質ゲート。

Cobertura XML と LCOV（`lcov.info`）の両方を読める。どちらも多くの言語の
カバレッジツールが出力できる標準フォーマットであり、本スクリプトは
**ファイルを読むだけ**でカバレッジツールを起動しない。

  Cobertura: coverage.py (`coverage xml`) / jacoco / cobertura / gocover-cobertura
  LCOV:      istanbul (nyc) / lcov / llvm-cov / jest --coverageReporters=lcov

判定: ライン網羅率が `min` 未満なら不合格。`min` 未指定なら計測のみ（合格扱い）。

使い方:
    python jsix_coverage_gate.py --file coverage.xml --min 95
    python jsix_coverage_gate.py --file coverage/lcov.info --min 80

終了コード: 0=閾値以上 or 計測のみ / 1=閾値未満 / 2=入力エラー
"""
from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from jsix_result import Result, failed, passed  # noqa: E402


class CoverageParseError(ValueError):
    pass


def read_line_rate(xml_path: Path) -> float:
    """Cobertura ルート要素の line-rate（0.0-1.0）を返す。

    v2.0 から公開している関数。後方互換のためシグネチャを変えない。
    """
    root = ET.parse(xml_path).getroot()
    rate = root.get("line-rate")
    if rate is None:
        raise CoverageParseError("coverage.xml に line-rate 属性がありません（Cobertura形式か確認）")
    return float(rate)


def parse_cobertura(path: Path) -> dict:
    """Cobertura XML から全体・ファイル別のライン網羅率を返す。"""
    root = ET.parse(path).getroot()
    if root.get("line-rate") is None:
        raise CoverageParseError("line-rate 属性がありません（Cobertura 形式か確認してください）")

    per_file: dict = {}
    for cls in root.iter("class"):
        filename = cls.get("filename")
        if not filename:
            continue
        lines = [ln for ln in cls.iter("line") if ln.get("number") is not None]
        covered = sum(1 for ln in lines if int(ln.get("hits", "0")) > 0)
        total = len(lines)
        # 同一ファイルが複数 class に分かれることがあるので加算する
        agg = per_file.setdefault(filename, {"covered": 0, "total": 0})
        agg["covered"] += covered
        agg["total"] += total

    return {
        "format": "cobertura",
        "line_rate": float(root.get("line-rate")),
        "per_file": per_file,
    }


def parse_lcov(path: Path) -> dict:
    """LCOV トレースファイルから全体・ファイル別のライン網羅率を返す。

    使うレコードは SF（ファイル名）, DA（行番号,実行回数）, end_of_record。
    LF/LH の集計行があってもそれを信用せず DA から数える（ツール差を避けるため）。
    """
    per_file: dict = {}
    current = None
    total_lines = 0
    covered_lines = 0

    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if line.startswith("SF:"):
            current = line[3:]
            per_file.setdefault(current, {"covered": 0, "total": 0})
        elif line.startswith("DA:") and current is not None:
            body = line[3:].split(",")
            if len(body) < 2:
                continue
            try:
                hits = int(body[1])
            except ValueError:
                continue
            per_file[current]["total"] += 1
            total_lines += 1
            if hits > 0:
                per_file[current]["covered"] += 1
                covered_lines += 1
        elif line == "end_of_record":
            current = None

    if total_lines == 0:
        raise CoverageParseError("LCOV に DA レコードが1件もありません（形式を確認してください）")

    return {
        "format": "lcov",
        "line_rate": covered_lines / total_lines,
        "per_file": per_file,
    }


def parse_coverage(path: Path) -> dict:
    """拡張子と中身から形式を判別して読む。"""
    if not path.is_file():
        raise CoverageParseError(f"カバレッジファイルが見つかりません: {path}")

    head = path.read_text(encoding="utf-8", errors="ignore")[:400].lstrip()
    if head.startswith("<"):
        try:
            return parse_cobertura(path)
        except ET.ParseError as exc:
            raise CoverageParseError(f"XML の解析に失敗: {exc}") from exc
    if "SF:" in head or head.startswith(("TN:", "DA:")):
        return parse_lcov(path)

    # 拡張子でのフォールバック
    if path.suffix.lower() == ".xml":
        return parse_cobertura(path)
    return parse_lcov(path)


def lowest_files(per_file: dict, limit: int = 5) -> list:
    """網羅率の低いファイルを返す（証跡の「リスク箇所」に使う）。"""
    rows = []
    for name, agg in per_file.items():
        if agg["total"] == 0:
            continue
        rows.append({
            "file": name,
            "line_rate": agg["covered"] / agg["total"],
            "covered": agg["covered"],
            "total": agg["total"],
        })
    rows.sort(key=lambda r: (r["line_rate"], -r["total"]))
    return rows[:limit]


def check(cfg: dict, base_dir: Path | None = None) -> Result:
    base = base_dir or Path.cwd()
    target = cfg.get("file", "coverage.xml")
    path = base / target

    try:
        data = parse_coverage(path)
    except CoverageParseError as exc:
        return failed(f"coverage: {exc}")

    pct = data["line_rate"] * 100
    metrics = {
        "line_rate": round(data["line_rate"], 6),
        "line_pct": round(pct, 2),
        "format": data["format"],
        "files": len(data["per_file"]),
    }
    findings = [
        {"file": r["file"], "line_pct": round(r["line_rate"] * 100, 1), "covered": r["covered"], "total": r["total"]}
        for r in lowest_files(data["per_file"])
    ]

    minimum = cfg.get("min")
    if minimum is None:
        return passed(f"coverage: {pct:.1f}%（閾値未設定のため計測のみ）", metrics, findings)

    minimum = float(minimum)
    metrics["min"] = minimum
    if pct + 1e-9 < minimum:
        return failed(f"coverage: {pct:.1f}% < 閾値 {minimum:.1f}%（不足 {minimum - pct:.1f}pt）", metrics, findings)
    return passed(f"coverage: {pct:.1f}% ≥ 閾値 {minimum:.1f}%", metrics, findings)


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="カバレッジ品質ゲート（Cobertura XML / LCOV）")
    parser.add_argument("--file", default="coverage.xml", help="Cobertura XML または LCOV のパス")
    parser.add_argument("--min", type=float, default=None, help="最低カバレッジ率（％）。省略時は計測のみ")
    args = parser.parse_args(argv)

    cfg = {"file": args.file}
    if args.min is not None:
        cfg["min"] = args.min

    result = check(cfg)
    print(("✅ " if result.ok else "❌ ") + result.summary)
    if not result.ok and "見つかりません" in result.summary:
        return 2
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
