# Changelog

All notable changes to this project will be documented in this file.

## [2.0.0] - 2026-04-18

### Fixed
- IPA 参考文献リンク修正（/sec/ → /digital/architecture/）
- README.md 文言修正（「Plugin で補強予定」→ 完成済みの表現に）

### Changed
- J-SIX_v1.0.md → v2.0 に改訂
  - 第1章: データ精度改善（「初回成功率33%」→「人間介入33%減少」に訂正、出典と数値を正確化）
  - 第1章: Sonnet 4.5 発表日を 2026.02 → 2025.09 に訂正
  - 第4章: CC ネイティブ機能に LSP, Monitors, Remote Control, Push Notifications を追加
  - 第4章: Phase 別マッピングに新 Hook イベント（TaskCreated, PermissionDenied, StopFailure）、/ultrareview、/effort を追加
  - 第4章: Plugin 構成を実装済みの構成に更新
- REFERENCES_AUDIT.md: A1（33%出典）・A6（Sonnet 4.5日付）を訂正、7.1 に訂正経緯を記録
- article-plan.md: 「初回成功率33%」の表現を修正
- Plugin hooks.json: StopFailure, PermissionDenied Hook を追加

## [1.1.0] - 2026-03-30

### Added
- J-SIX Plugin for Claude Code（plugin/）
  - Skills 6 件: spec-create, design-review, tdd-cycle, doc-reverse-gen, quality-metrics, traceability
  - Agents 5 件: red-agent, green-agent, refactor-agent, qa-reviewer, doc-generator
  - Hooks: コーディング規約チェック、テスト結果監視、ADR 検出

### Changed
- README.md: Plugin セクション追加、「今後の展開」状態更新
- J-SIX_v1.0.md: 付録B の展開予定を更新

### Removed
- docs/HANDOFF_TO_CLAUDE_CODE.md（内部引き継ぎ資料を除去）

### Fixed
- LICENSE を CC BY 4.0 正規リーガルコードに置換（GitHub が正しく認識するように）
- .gitignore 追加（.DS_Store, .claude/, memory/）

## [1.0.0] - 2026-03-29

### Added
- J-SIX プロセス完成版 v1.0（docs/J-SIX_v1.0.md）
- Phase 4 TDD ワークスルー（docs/walkthrough-phase4-tdd.md）
- レガシーコード適用ガイド（docs/guide-legacy-code.md）
- 設計議論ドキュメント 5 本（docs/discussions/）
  - 01a: Phase 0-6 の初期提案
  - 02: SDD vs 独自設計
  - 03: 設計書逆生成の限界と対策
  - 04: CC 自律実行の範囲
  - 05: 段階的移行パス
- 出典・参考文献 監査レポート（docs/REFERENCES_AUDIT.md）
- テンプレート一式（templates/）
  - CLAUDE.md テンプレート（base / web-app / api-service）+ ガイド
  - Spec テンプレート（要求Spec / Design Spec）
  - ADR テンプレート
- README.md、LICENSE（CC BY 4.0）
