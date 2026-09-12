#!/usr/bin/env python3
"""J-SIX G1: SARIF の severity 集計と閾値判定。

SARIF (Static Analysis Results Interchange Format, OASIS 標準) は semgrep /
bandit / gitleaks / trivy / CodeQL などが共通して出力できる。本スクリプトは
**SARIF を読むだけ**で、解析ツールを起動しない。

severity の決め方（SARIF 仕様に沿った優先順）:
  1. result.level（error / warning / note / none）
  2. 無い場合は rule.defaultConfiguration.level
  3. それも無い場合は "warning"（SARIF の既定）
`suppressions` が付いた result は集計から除外する（ツール側で握りつぶされたもの）。

判定: `max_severity` 以上の重大度の result が1件でもあれば不合格。
      `max_severity: "none"` は「どんな指摘も許さない」を意味する。
      未指定なら集計のみ（合格扱い）。

使い方:
    python jsix_sarif_gate.py --file reports/sast.sarif --max-severity warning

終了コード: 0=合格 or 集計のみ / 1=閾値超過 / 2=入力エラー
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from jsix_result import Result, failed, missing_artifact, passed  # noqa: E402

#: 重大度の順序（大きいほど深刻）
LEVEL_RANK = {"none": 0, "note": 1, "warning": 2, "error": 3}
DEFAULT_LEVEL = "warning"


class SarifParseError(ValueError):
    pass


def _rule_levels(run: dict) -> dict:
    """run 内のルールID → defaultConfiguration.level の対応を作る。"""
    levels: dict = {}
    driver = (run.get("tool") or {}).get("driver") or {}
    extensions = (run.get("tool") or {}).get("extensions") or []
    for component in [driver] + list(extensions):
        for rule in component.get("rules") or []:
            rid = rule.get("id")
            level = ((rule.get("defaultConfiguration") or {}).get("level"))
            if rid and level:
                levels[rid] = level
    return levels


def _location_of(result: dict) -> dict:
    for loc in result.get("locations") or []:
        phys = loc.get("physicalLocation") or {}
        art = phys.get("artifactLocation") or {}
        region = phys.get("region") or {}
        if art.get("uri"):
            return {"file": art["uri"], "line": region.get("startLine")}
    return {}


def parse_sarif(path: Path) -> dict:
    """SARIF から severity 別件数と指摘一覧を返す。"""
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SarifParseError(f"JSON の解析に失敗: {exc}") from exc

    if not isinstance(doc, dict) or "runs" not in doc:
        raise SarifParseError("SARIF ではありません（runs 要素がありません）")

    counts = {level: 0 for level in LEVEL_RANK}
    findings: list = []
    suppressed = 0
    tools: list = []

    for run in doc.get("runs") or []:
        driver = (run.get("tool") or {}).get("driver") or {}
        tool_name = driver.get("name") or "unknown"
        tool_version = driver.get("version") or driver.get("semanticVersion")
        tools.append({"name": tool_name, "version": tool_version})
        rule_levels = _rule_levels(run)

        for result in run.get("results") or []:
            if result.get("suppressions"):
                suppressed += 1
                continue
            rule_id = result.get("ruleId") or ""
            level = result.get("level") or rule_levels.get(rule_id) or DEFAULT_LEVEL
            if level not in LEVEL_RANK:
                level = DEFAULT_LEVEL
            counts[level] += 1
            message = ((result.get("message") or {}).get("text") or "").strip()
            findings.append({
                "tool": tool_name,
                "rule": rule_id,
                "level": level,
                "message": message[:200],
                **_location_of(result),
            })

    return {"counts": counts, "findings": findings, "suppressed": suppressed, "tools": tools}


def check(cfg: dict, base_dir: Path | None = None, label: str = "sast") -> Result:
    base = base_dir or Path.cwd()
    target = cfg.get("sarif") or cfg.get("file")
    if not target:
        return failed(f"{label}: 設定に sarif（SARIF ファイルのパス）がありません")

    path = base / target
    if not path.is_file():
        return missing_artifact(label, target, cfg, "解析ツールを実行して SARIF を出力してください")

    try:
        data = parse_sarif(path)
    except SarifParseError as exc:
        return failed(f"{label}: {target} — {exc}")

    counts = data["counts"]
    metrics = {
        "error": counts["error"],
        "warning": counts["warning"],
        "note": counts["note"],
        "none": counts["none"],
        "suppressed": data["suppressed"],
        "tools": data["tools"],
    }
    breakdown = f"error {counts['error']} / warning {counts['warning']} / note {counts['note']}"

    max_severity = cfg.get("max_severity")
    if max_severity is None:
        return passed(f"{label}: {breakdown}（閾値未設定のため集計のみ）", metrics, data["findings"][:20])

    max_severity = str(max_severity).lower()
    if max_severity not in LEVEL_RANK:
        return failed(f"{label}: max_severity が不正です（{max_severity}）。有効: {', '.join(LEVEL_RANK)}")

    threshold = LEVEL_RANK[max_severity]
    metrics["max_severity"] = max_severity
    over = [f for f in data["findings"] if LEVEL_RANK[f["level"]] >= threshold]

    if over:
        return failed(
            f"{label}: {max_severity} 以上の指摘 {len(over)}件（{breakdown}）",
            metrics,
            over[:20],
        )
    return passed(f"{label}: {max_severity} 以上の指摘なし（{breakdown}）", metrics, data["findings"][:20])


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="SARIF の severity 閾値判定")
    parser.add_argument("--file", required=True, help="SARIF ファイルのパス")
    parser.add_argument("--max-severity", default=None, choices=sorted(LEVEL_RANK),
                        help="この重大度以上を不合格とする。省略時は集計のみ")
    parser.add_argument("--label", default="sast", help="出力ラベル（sast / secrets / deps 等）")
    args = parser.parse_args(argv)

    cfg = {"sarif": args.file}
    if args.max_severity:
        cfg["max_severity"] = args.max_severity

    result = check(cfg, label=args.label)
    print(("✅ " if result.ok else "❌ ") + result.summary)
    for f in result.findings[:10]:
        loc = f"{f.get('file', '?')}:{f.get('line', '?')}"
        print(f"  - [{f['level']}] {loc} {f['rule']} {f['message']}")
    if not result.ok and "見つかりません" in result.summary:
        return 2
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
