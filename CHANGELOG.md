# Changelog

All notable changes to this project will be documented in this file.

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
