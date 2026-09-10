# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added

**v2.1: レビュー前品質ゲートの再設計**

- docs/J-SIX.md 第9章「証跡パッケージ（品質の証明と納品）」— 証跡 / 参考所見 / 承認の3区分、`reports/evidence/<task-id>/` の構成、従来納品物への対応付け
- docs/J-SIX.md 第4章 4.4「内側ループ（Hook）と外側ループ（CI）の二重化」— Stop hook は8回連続ブロックで自動解除されるため CI ゲートを併設する
- docs/J-SIX.md Phase 4: 順序固定の4層品質ゲート（G1 決定論的検証 / G2 テスト品質検証 / G3 意図・スコープ判定 / G4 証跡生成）、テスト改変検出の判定表、hold-out 受入テスト、「G3 は固定装備ではない」節
- docs/J-SIX.md Phase 2: 受入条件 → Property（PROP-nnn）の導出工程 / Phase 3: 変更許可ファイル範囲の事前承認 / Phase 0: CLAUDE.md をコードとして扱う月次ループ
- docs/J-SIX.md 期待効果に mutation score 行を追加（🟡 未実測。閾値はケーススタディ #2 の実測後に決める）
- templates/spec/requirement-spec.md: 3.2 要件ID（REQ-nnn）、3.3 受入条件と Property（PROP-nnn）、3.4 hold-out 受入テストの対象
- templates/spec/design-spec.md: 8. Property の実装方針（PBT ライブラリ・入力生成戦略）、9. 品質ゲートの設定
- docs/REFERENCES_AUDIT.md: 2.7「品質ゲート・検証」（A36-A43）、カテゴリB に B15-B20
- index.html: セクション 04「レビュー前の4層品質ゲート」を追加（既存セクションを繰り下げ）
- README.md: 4層品質ゲートの概要、期待効果に mutation score 行
- plugin/scripts/: G1/G2 の決定論的チェック 7種を追加 — `jsix_config.py`（設定の正規化と v2.0 後方互換）/ `jsix_result.py`（Check 共通インタフェース）/ `jsix_gitutil.py` / `jsix_junit_check.py`（JUnit XML）/ `jsix_sarif_gate.py`（SARIF の severity 集計）/ `jsix_mutation_gate.py`（mutation-testing-elements JSON と最小契約 JSON）/ `jsix_scope_check.py`（変更ファイル ⊆ 許可リスト）/ `jsix_test_tamper_check.py`（テスト弱体化の検出）
- plugin/scripts/tests/: 111 件の単体テストとフィクスチャ（JUnit / Cobertura / LCOV / SARIF / mutation / 新旧 config）
- examples/approval-workflow/: `Makefile`（build/lint/format/sast/test/gate）と `requirements-dev.txt`（ruff / bandit / bandit-sarif-formatter / hypothesis）
- plugin/agents/scope-judge.md: G3 の判定エージェント。正確性・要件未充足・スコープ逸脱の3分類のみを報告し、スタイル指摘を禁止（「gap を探せと言われたレビュアーは健全な作業でも何かを報告する」問題への対処）。判定は `judge.json` に書き出す
- plugin/agents/holdout-test-writer.md: hold-out 受入テストの作成エージェント。実装コードを読まず、Spec の受入条件（UC-nnn）と PROP から `tests/acceptance/` を生成する
- plugin/scripts/jsix_guard_tests.py: green-agent 用の PreToolUse Hook。`tests/` への書き込みと `tests/acceptance/` の読み取りを機械的に拒否する（想定外の入力では止めない fail-open）
- examples/approval-workflow/tests/acceptance/: hold-out 受入テスト 10件（UC-001〜006 を各1件以上）

**実証・テンプレート実例・決定論的チェック（先行実装分）**

- docs/ROADMAP.md: 次フェーズの改善・追加機能ロードマップ（実証・信頼性 / テンプレート充実 / Plugin 実用拡張）
- docs/case-study-01.md: ケーススタディ #1（申請承認ワークフローで J-SIX を一周。実測値と推定値を切り分け）— ROADMAP A1
- examples/approval-workflow/: 動く FastAPI サンプル（37テスト / カバレッジ99%）。記入済みテンプレ実例（CLAUDE.md / Spec×2 / ADR×2 / traceability）を兼ねる — ROADMAP B1/B2/C2
- plugin/scripts/: 決定論的チェックスクリプト3種（traceability_check / coverage_gate / run_checks）— ROADMAP C1
- plugin Stop Hook に command 型を追加（`.jsix-checks.json` 同梱時のみ動く品質ゲート、no-op 既定）— ROADMAP C1
- index.html: J-SIX の全体像を1枚に集約した自己完結型 HTML（外部依存なし。GitHub Pages のルートとしても機能）

### Changed

**v2.1: レビュー前品質ゲートの再設計**

- docs/J-SIX.md: Version 2.0 → 2.1。自律度モデル L4 の条件を「自動テスト通過」から「G1〜G4 全層通過」へ変更（reward hacking 対策。根拠は SpecBench [26]）。Phase 5 を「機械が原理的に見られないものを人間が見る工程」として再定義し、集計メトリクス（mutation score / judge 却下率 / ゲート失敗理由分布 / 人間レビュー指摘数）を追加。第4章 4.2 マッピング表に `/goal`・`/verify`・`/code-review`・auto mode 分類器・dynamic workflows・`/batch` を追加。用語集に G1-G4 / PROP / PBT / mutation score / hold-out / reward hacking / 証跡パッケージ等を追加。参考文献 [26]-[31] を追加
- docs/REFERENCES_AUDIT.md: 監査日に 2026-09-10 を追記（四半期鮮度レビュー第2回）。7.1 に「DORA の verification tax は一次情報で確認できず不採用」を記録
- docs/ROADMAP.md: A2/A3 を実績反映、A4（ケーススタディ #2）・A5（1.3 能力データ更新）・C4/C5/C6（品質ゲート実装・証跡パック・CI 例）を追加
- plugin/scripts/jsix_run_checks.py: ゲートを G1→G2→G3→G4 の順に実行する基盤へ。前段のゲートが落ちたら後段は実行しない。既定は**レポート駆動**（宣言された成果物を読むだけ。`cmd` は `--run-commands` 指定時のみ実行）。G3 は判定ファイルを介した2段構成
- plugin/scripts/jsix_coverage_gate.py: LCOV に対応（Cobertura と自動判別）。`min` 未指定時は計測のみ。低カバレッジのファイル上位5件を証跡に出す
- plugin/scripts/jsix_traceability_check.py: ID パターンを複数指定可能に（REQ と PROP を同時検証）。JUnit XML のテスト名も走査対象に
- examples/approval-workflow/: `.jsix-checks.json` を v2.1 の gates 形式へ。ruff format による整形に伴い行数が変化（app 354→368 / tests 290→299。テスト件数・カバレッジ・トレーサビリティは変化なし）
- docs/case-study-01.md / examples/approval-workflow/README.md: 上記の再計測値を反映し、変化の理由を注記
- .gitignore: `**/reports/`（ゲートの生成物）を除外
- plugin/agents/green-agent.md: subagent スコープの `hooks` で `tests/` への書込と hold-out の読取を拒否。テストの期待値が誤っていると考えた場合は修正せず人間へ報告する手順を追加（subagent frontmatter に `permissions` フィールドは無いため `hooks` で実現）
- plugin/agents/red-agent.md: PROP から property-based test を生成する手順と、完了時に `git tag jsix/red-<タスクID>` を打つ手順を追加（G2 テスト改変検出の基準点）
- plugin/agents/refactor-agent.md: テストのリファクタリングで越えてはいけない線（アサーション・テスト関数の総数を減らさない / 無効化マーカーを増やさない）を明記
- plugin/agents/qa-reviewer.md: 役割を「証跡パックの人間向け要約と探索的テスト観点の提示」へ再定義。合否判定は G1-G3 に委譲し、出力は「参考所見」と明記する
- plugin/skills/tdd-cycle/SKILL.md: Hold-out → Red → Green → Refactor → G1〜G4 の流れへ改訂。RED タグ、G3 の2段構成、`/goal` の併用、エスカレーション条件を追加
- examples/approval-workflow/.jsix-checks.json: hold-out / G3 / G4 を有効化

**実証・テンプレート実例・決定論的チェック（先行実装分）**

- README.md: 参考資料テーブルに ROADMAP を追加、「実証（動くサンプル）」セクション追加、期待効果に検証ステータス（実測/推定）を明示、「今後の展開」に次フェーズ計画への誘導を追記 — ROADMAP A2
- templates/README.md: 「テンプレ → 記入済み実例 → 該当 Skill」の導線表を追加 — ROADMAP B3
- docs/J-SIX.md: 期待効果テーブルに「検証ステータス」列を追加（実測/推定の切り分け）— ROADMAP A2 / 付録B（展開予定）の鮮度更新、ROADMAP への誘導を追記
- docs/REFERENCES_AUDIT.md: 監査日に 2026-06-14 鮮度レビューを追記（変更なし）/ 7.3「鮮度レビューの運用（四半期）」を追加 — ROADMAP Q2/A3
- plugin/README.md: Hooks テーブルに型列・command 型 Hook を追記、「決定論的チェック」節を追加 — ROADMAP C1
- plugin/.claude-plugin/plugin.json: version 1.1.0 → 2.0.0（hooks.json 変更に整合, ROADMAP Q1）→ 2.1.0（決定論的チェック追加, ROADMAP C1）
- .gitignore: example アプリの生成物（.venv, __pycache__, .pytest_cache, coverage.xml 等）を除外

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
