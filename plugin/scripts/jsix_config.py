#!/usr/bin/env python3
"""J-SIX 品質ゲート設定（`.jsix-checks.json`）の読み込みと正規化。

J-SIX v2.1 で設定形式が `gates.g1..g4` の入れ子に変わったが、v2.0 のフラット形式
（`{"traceability": {...}, "coverage": {...}}`）を使っているプロジェクトを壊さない。
旧形式は G2 相当のチェックへマップし、以降のコードは新形式だけを見ればよくする。

正規化後の構造（すべてのキーは省略可能）:
    {
      "gates": {
        "g1": {"build": {...}, "lint": {...}, "sast": {...}, "scope": {...}},
        "g2": {"tests": {...}, "coverage": {...}, "mutation": {...},
               "test_tamper": {...}, "holdout": {...}, "traceability": {...}},
        "g3": {"agent": "scope-judge", "inputs": [...], "max_auto_fix": 1},
        "g4": {"out": "reports/evidence/", "formats": ["md", "json"]}
      }
    }
"""
from __future__ import annotations

import json
from pathlib import Path

CONFIG_NAME = ".jsix-checks.json"

#: v2.0 のトレーサビリティ既定パターン。旧形式の設定はこの挙動を維持する。
LEGACY_DEFAULT_ID = r"REQ-\d+"

GATE_ORDER = ("g1", "g2", "g3", "g4")

#: 各ゲートで実行するチェックの順序。設定に無いものは飛ばす。
CHECK_ORDER = {
    "g1": ("build", "typecheck", "lint", "format", "sast", "secrets", "deps", "scope"),
    "g2": ("tests", "holdout", "coverage", "mutation", "test_tamper", "traceability"),
    "g3": ("judge",),
    "g4": ("evidence",),
}


class ConfigError(ValueError):
    """設定ファイルが読めない・構造が不正な場合。"""


def is_legacy(raw: dict) -> bool:
    """v2.0 のフラット形式か判定する。"""
    return "gates" not in raw and any(k in raw for k in ("traceability", "coverage"))


def _migrate_legacy(raw: dict) -> dict:
    """v2.0 のフラット形式を v2.1 の `gates` 形式へマップする。

    旧形式で判定できたものは新形式でも同じ判定になること（＝終了コードが変わらないこと）
    を保証する。旧形式に無いチェック（mutation, scope 等）は追加しない。
    """
    g2: dict = {}

    if "traceability" in raw:
        tr = dict(raw["traceability"])
        # 旧: pattern（単一の正規表現文字列） → 新: ids（正規表現のリスト）
        pattern = tr.pop("pattern", None)
        # v2.0 の既定は REQ-\d+ のみだった。v2.1 の既定（REQ と PROP の両方）を
        # 旧形式に適用すると、Spec に PROP-nnn を書いた既存利用者が突然落ちる。
        # 旧形式では v2.0 の既定を明示的に固定する。
        tr["ids"] = [pattern] if pattern is not None else [LEGACY_DEFAULT_ID]
        g2["traceability"] = tr

    if "coverage" in raw:
        g2["coverage"] = dict(raw["coverage"])

    return {"gates": {"g2": g2}, "_legacy": True}


def normalize(raw: dict) -> dict:
    """生の設定辞書を正規化した設定へ変換する。"""
    if not isinstance(raw, dict):
        raise ConfigError(f"{CONFIG_NAME} のトップレベルはオブジェクトである必要があります")

    if is_legacy(raw):
        return _migrate_legacy(raw)

    gates = raw.get("gates", {})
    if not isinstance(gates, dict):
        raise ConfigError("gates はオブジェクトである必要があります")

    unknown = [k for k in gates if k not in GATE_ORDER]
    if unknown:
        raise ConfigError(f"未知のゲート: {', '.join(sorted(unknown))}（有効: {', '.join(GATE_ORDER)}）")

    normalized = {"gates": {}}
    for gate in GATE_ORDER:
        cfg = gates.get(gate)
        if cfg is None:
            continue
        if not isinstance(cfg, dict):
            raise ConfigError(f"gates.{gate} はオブジェクトである必要があります")
        normalized["gates"][gate] = dict(cfg)
    stop_hook = raw.get("stop_hook", {})
    if not isinstance(stop_hook, dict):
        raise ConfigError("stop_hook はオブジェクトである必要があります")
    normalized["stop_hook"] = dict(stop_hook)
    if raw.get("history"):
        normalized["history"] = str(raw["history"])
    normalized["_legacy"] = False
    return normalized


def load(directory: Path | None = None) -> dict | None:
    """カレント（または指定）ディレクトリの設定を読む。無ければ None。"""
    base = Path.cwd() if directory is None else Path(directory)
    path = base / CONFIG_NAME
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"{CONFIG_NAME} の解析に失敗: {exc}") from exc
    cfg = normalize(raw)
    cfg["_path"] = str(path)
    return cfg


#: ゲート全体の設定が1チェックの設定そのものになるゲート。
#: g3 は `{"agent": "scope-judge", "verdict": "..."}`、g4 は `{"out": "...", "formats": [...]}`
#: のように「チェック名で入れ子にしない」形で書くため、ゲート設定をそのまま渡す。
SINGLE_CHECK_GATES = {"g3": "judge", "g4": "evidence"}


def iter_checks(cfg: dict):
    """(gate, check_name, check_cfg) を実行順に列挙する。"""
    gates = cfg.get("gates", {})
    for gate in GATE_ORDER:
        gcfg = gates.get(gate)
        if not gcfg:
            continue

        single = SINGLE_CHECK_GATES.get(gate)
        if single:
            # 明示的に入れ子にしている場合はそちらを優先する
            if single in gcfg and isinstance(gcfg[single], dict):
                yield gate, single, gcfg[single]
            else:
                yield gate, single, gcfg
            continue

        known = CHECK_ORDER[gate]
        # 既知のチェックを定義順に、その後に未知のキーを名前順に（前方互換）
        for name in known:
            if name in gcfg:
                yield gate, name, gcfg[name]
        for name in sorted(k for k in gcfg if k not in known):
            yield gate, name, gcfg[name]
