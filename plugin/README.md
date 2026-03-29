# J-SIX Plugin for Claude Code

**J-SIX (Japanese SI Transformation)** の日本品質レイヤーを Claude Code Plugin として提供します。

## 概要

J-SIX プロセスの Phase 0-6 を Claude Code のネイティブ機能（Skills / Agents / Hooks）で実装した Plugin です。

## 構成

### Skills（6件）

| Skill | Phase | 概要 |
|---|---|---|
| `j-six:spec-create` | P1-P2 | 要求Spec / Design Spec の対話的策定 |
| `j-six:design-review` | P2 | 設計レビュー（Spec・ADR・コード整合性検証） |
| `j-six:tdd-cycle` | P4 | TDD Red→Green→Refactor サイクル管理 |
| `j-six:doc-reverse-gen` | P6 | 設計書逆生成（基本/詳細/IF/DB設計書） |
| `j-six:quality-metrics` | P5 | 品質メトリクス計測・品質ゲート判定 |
| `j-six:traceability` | P1-P6 | 要件→テスト→コード→設計書の追跡マトリクス |

### Agents（5件）

| Agent | Phase | 概要 |
|---|---|---|
| `red-agent` | P4 | TDD Red Phase（テスト作成のみ） |
| `green-agent` | P4 | TDD Green Phase（最小実装のみ） |
| `refactor-agent` | P4 | TDD Refactor Phase（品質改善のみ） |
| `qa-reviewer` | P4-P5 | 品質レビュー（読み取り専用） |
| `doc-generator` | P6 | 設計書一式の自動生成 |

### Hooks

| イベント | 対象 | 内容 |
|---|---|---|
| PreToolUse | Edit/Write | CLAUDE.md コーディング規約準拠チェック |
| PostToolUse | Bash | テスト実行結果の自動確認 |
| Stop | 全体 | ADR 記録すべき技術判断の検出 |

## 使い方

### インストール

```bash
# Claude Code の Plugin として追加
claude plugin add ./plugin
```

### Skills の実行例

```bash
# Spec 策定
/j-six:spec-create

# TDD サイクル開始
/j-six:tdd-cycle

# 設計書逆生成（全種別）
/j-six:doc-reverse-gen all

# 基本設計書のみ逆生成
/j-six:doc-reverse-gen basic src/

# 品質メトリクス計測
/j-six:quality-metrics

# トレーサビリティマトリクス生成
/j-six:traceability
```

### TDD サイクルでの Agent 活用

Phase 4 では、Red/Green/Refactor を分離した Agent として実行できます。Claude Code が tdd-cycle Skill の実行中に自動的にこれらの Agent を呼び出します。

## 前提条件

- Claude Code がインストールされていること
- プロジェクトに CLAUDE.md が設定されていること（テンプレート: `templates/claude-md/`）
- J-SIX プロセスの Phase に沿って運用すること

## テンプレート

Plugin と併用するテンプレートはリポジトリルートの `templates/` を参照:
- `templates/claude-md/` — CLAUDE.md テンプレート
- `templates/spec/` — Spec テンプレート
- `templates/adr/` — ADR テンプレート

## ライセンス

CC BY 4.0
