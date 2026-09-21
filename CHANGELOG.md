# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added

- docs/control-plane/: J-SIX Hub（旧称 J-SIX Control Plane）の構想を置くディレクトリを新設。J-SIX を大規模・複数チーム・複数ベンダーの案件に広げるための構想で、現時点では仮説であり実装・実証はしていない。`README.md`（一文定義・3層構成・決定事項 D1〜D9 と記録先の対応）と、決定事項の ADR 5本（`adr/0001`〜`0005`：正本は Git／差別化軸はプロセス適合性／依存方向とプロセス定義のデータ化／リプレイ型サンプル環境／中央実行とローカル退避路）。ADR はいずれも「提案中」
- docs/ROADMAP.md: H「J-SIX Hub（構想）」を追加（H0 決定事項の記録を完了、H1〜H5 は未着手）。項目番号は構想の決定事項 D1〜D9 と区別するため H とした
- README.md「今後の展開」、docs/J-SIX.md 付録B: J-SIX Hub を「構想中（仮説であり未実装）」として追加

### Fixed

- plugin/README.md, plugin/scripts/jsix_coverage_gate.py: JaCoCo を Cobertura XML の生成ツールとして挙げていたが、JaCoCo の XML レポートは独自形式で `line-rate` 属性を持たず、カバレッジゲートはそのままでは読めない（「line-rate 属性がありません」で失敗する）。Cobertura 形式への変換が必要である旨に訂正

### Changed

- README.md / docs/article-plan.md / index.html: 番外編記事「カバレッジ 99% のテストに mutation testing をかけたら、監査ログの穴が見つかった」（j-six-mutation-testing）の公開を反映（番外編 10本・全16本）
- README.md / docs/article-plan.md / index.html: 番外編記事「AI の「テストは通りました」を鵜呑みにしない — 人間レビューの前に置く4層品質ゲート」（j-six-quality-gates）の公開を反映（番外編 11本・全17本）
- README.md / docs/article-plan.md / index.html: 番外編記事2本（j-six-ipa-deliverables / j-six-plugin-field-test）の公開を反映（番外編 13本・全19本）

### Fixed

- examples/monthly-billing/README.md: 「mutation testing が見つけたテストの穴」の表が、本文の「本物の穴が8種」に対して6行しかなかった。実装時のコミット（`3b14aaf`）に残っていた内訳から、抜けていた2種（明細への数量の転記、reset 後の採番リセット）を追加。いずれも対応するテストは既にある
- examples/monthly-billing/tests/test_billing.py: コメントの誤字（「경路」→「経路」）
- docs/J-SIX.md 1.3: 連続自律アクション数を一次情報 [3] に合わせて「約10→約20（6ヶ月で2倍）」から「約10→約21（6ヶ月で116%増）」に訂正。[3] のデータ時点を「2025」から「2025.12」に
- docs/REFERENCES_AUDIT.md: 参考文献一覧の [4] Sonnet 4.5 の日付が 2026.02 のまま残っていた（J-SIX.md 側は v2.0 で 2025.09 に訂正済み）。[3] の公開日を 2025.12 に。7.1 に訂正経緯を記録
- docs/J-SIX.md 付録B: 「導入事例・ROI レポート」が「計画中（ROADMAP A1）」のままだった。A1 は完了済み、ROI の根拠となる A1'（工数の実測比較）は見送りのため、状態を「見送り」に更新

## [2.1.0] - 2026-09-19

### Added

**工程成果物27点（IPA 機能要件の合意形成ガイド準拠）**

- templates/deliverables/: 工程成果物27点の空テンプレート — システム振舞い4 / 画面6 / データモデル4 / 外部インタフェース4 / バッチ4 / 帳票5。各テンプレートは冒頭に**由来**（コードから逆生成 / 受入テストから逆生成 / コード＋Spec / 人手更新）と逆生成元を持ち、末尾に「記入ガイド（記入後は削除する）」として逆生成の手順・書き落としやすい点・記入済み実例へのリンクを備える
- templates/deliverables/README.md: 27点の索引、由来の内訳（逆生成19点／人手5点／併用3点）、作る順序（人手で書く成果物が逆生成の前提になる）、27点すべてを作る必要はないこと、顧客様式への束ね方
- templates/deliverables/assembly/: 工程成果物を顧客様式の設計書に束ねる組立定義 — `GUIDE.md`（正は工程成果物で設計書はビュー / 由来・ID を束ねた後も保つ / 事前提出と納品の2時期 / 顧客目次への組み替え手順と対応しない章の3分類 / 組立後の検査）、`kihon-sekkei.md`（基本設計書に27点すべてを収める目次、章ごとの事前提出可否と代替物、項目レベルを詳細設計書に回す変種）、`shousai-sekkei.md`（IPA 27点の範囲外である内部設計を J-SIX の方針として定義。実装前には書かず Phase 3 のタスク一覧を代替とする）。いずれも monthly-billing での組立結果を併記
- docs/J-SIX.md 4.3・6.5 から組立定義への参照を追加
- docs/J-SIX.md Phase 1「合意成熟度による判定」: IPA 合意形成ガイドの3レベル（仕掛／充実／完成）を Phase 1・2・6 の品質ゲートの到達基準にした。成熟度は合意対象ごとに判定し、Phase 2 では人手の成果物に完成レベル、逆生成する成果物には代替物による充実レベルを求める（逆生成版は Phase 6 に完成レベルになる）
- templates/spec/requirement-spec.md 3.5: 非機能要件を IPA 非機能要求グレードの**6大項目**（可用性 / 性能・拡張性 / 運用・保守性 / 移行性 / セキュリティ / システム環境・エコロジー）で分類。モデルシステムの選択（3.5.1）、合意した重要項目だけを書く要求レベル表（3.5.2）、グレードの対象外である品質ゲート閾値の別表（3.5.3）を新設。承認欄に合意成熟度のチェックリスト
- templates/spec/design-spec.md 7: 非機能設計の節を6大項目に揃えた（7.1 可用性〜7.5 システム環境・エコロジー）。承認欄に Phase 2 の合意成熟度チェックリスト
- .github/workflows/jsix-gate.yml: ゲートジョブを matrix 化し、monthly-billing も CI の対象にした（fail-fast 無効、証跡アーティファクトと SARIF カテゴリをサンプルごとに分離）
- docs/REFERENCES_AUDIT.md: A47 非機能要求グレードの体系（6大項目・238メトリクス・重要項目92）/ A48 3つのモデルシステム、参考文献 [34]。グレードの使用条件（PDF は改変不可、Excel は著作権表示付きで改変可）を踏まえ、テンプレートには大項目の区分だけを載せた旨を注記
- examples/monthly-billing/: 第2サンプル「月次請求書発行」。画面・帳票・バッチ・外部IF を持ち、`approval-workflow`（API のみ）では作れない画面6・帳票5・バッチ4 の実例を提供する。Spec / ADR / hold-out 受入テスト / TDD 実装 / 品質ゲート G1〜G4 通過（テスト101件＋hold-out 19件、カバレッジ 98.8%、mutation score 91.88%。2026-09-19 のリリース時点の値）
- examples/monthly-billing/docs/deliverables/: 工程成果物27点の**記入済み実例**。品質ゲート（mutation testing / G3 judge / hold-out）が検出した事項を設計書側にも根拠として記載している
- docs/REFERENCES_AUDIT.md: 2.8「工程成果物・合意形成」（A44 工程成果物と設計書は1対1でない / A45 合意成熟度の3段階 / A46 適格請求書の端数処理）、参考文献に [32] IPA ガイド・[33] 国税庁 Q&A を追加（[26]-[31] は J-SIX.md 側で使用済みのため）

**Plugin の評価ケース（ROADMAP C13）**

- plugin/evals/: `claude plugin eval` の評価ケース2本（spec-create / doc-reverse-gen）。Plugin を実際に読み込ませて Skill を動かし、同梱テンプレートの参照・出力のファイル名と内容を無料の決定論的な採点（ツール呼び出し・ファイルの有無・正規表現）で確かめる。実動検証 #1 の不具合（Plugin が読み込まれない、テンプレートを読めない）の再発を検知する。各3回で6回とも満点、合計 $3.79。LLM 判定は、条件を満たした Spec を3票とも不合格にし安定しなかったため使っていない。CI では実行しない
- plugin/skills/doc-reverse-gen: 同梱テンプレートへのリンク一覧を置き、Glob / Grep で探さず Read で読むよう明記。**テンプレートを読めない場合は、テンプレートなしで逆生成せず止めて報告する**（権限が足りない環境で、独自のファイル名・形式の成果物を黙って書いていた）

**Plugin 実動検証 #1 の改善（ROADMAP C8〜C10）**

- plugin/scripts/jsix_run_checks.py: ゲート失敗の履歴を `reports/gate-history.jsonl` に残す（C9。失敗はすべて、成功は回復時だけ）。quality-metrics Skill の「ゲート失敗理由の分布」の入力にし、Phase 0 の月次ループへ還元できるようにした
- plugin/scripts/jsix_run_checks.py: `g3.fingerprint_paths` で G3 の判定を紐づける差分の対象パスを指定可能にした（C8。既定はプロジェクト全体）
- plugin/skills/tdd-cycle, plugin/agents/scope-judge.md: タスク定義を `docs/tasks/<タスクID>.md` に保存して Hold-out より前にコミットし、scope-judge はそれを判定基準にする（C10）。無ければ推測せず REJECT

**Plugin 実動検証 #1（ROADMAP C2）**

- docs/plugin-field-test-01.md: Plugin の Skill 7本を `claude -p --plugin-dir` でヘッドレス実行した記録（合計 406 ターン・$37.22・64.5分）。Plugin の不具合8件の発見と修正、未解決の課題（ROADMAP C7〜C11・C13・C14）、所見
- examples/approval-workflow: Skill 実行の成果物。設計レビュー（`docs/reviews/`）、Spec 改訂と ADR-0003、TASK-AW-002（エラーを不在 404 / ルール違反 409 / 入力不正 422 に分類、全状態遷移でコメントを記録）の TDD 実装、品質メトリクス、工程成果物12点（`docs/deliverables/`）、基本／詳細設計書と品質系納品物（`docs/design-docs/`）

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
- plugin/scripts/jsix_evidence_pack.py: G4 の証跡パッケージ生成。`evidence.json` ＋ `00_summary.md`〜`07_approval.md` ＋ `env.json` を出力。証跡 / 参考所見 / 承認 の3区分を混ぜず、スクリプトは推定値を一切書かない（LLM 要約欄は空で出力する）。納品物に実行環境の絶対パスを残さない
- plugin/skills/evidence-pack/SKILL.md: 証跡に LLM 要約（変更概要・リスク箇所・計画からの逸脱）を「参考所見」として付加する手順。数値は証跡から引用し推定しないこと、納品前チェックリストを規定
- plugin/scripts/jsix_format_hook.py: PreToolUse の決定論的 format / lint。`.jsix-checks.json` の `hook_cmd` に宣言されたコマンドのみ実行（未宣言なら no-op）。言語別ツール名を plugin に持ち込まない
- .github/workflows/jsix-gate.yml: 外側ループ（CI）。内側ループと同じ判定スクリプト・同じ設定で `--run-commands` 実行し、trivy の SARIF（secret / 依存脆弱性）を G1 に投入、証跡をアーティファクトとして保存する。plugin/scripts の単体テストを先行ジョブとして実行する
- `.jsix-checks.json` に `optional` オプション: 成果物が無い場合にスキップする（CI でのみ生成する SARIF 等）。**既定は不合格**（検証していないものを検証済みとして扱わないため）
- docs/case-study-02.md: 「カバレッジ 99%」の mutation score を実測。**91.8%**（183 ミュータント中 15 生存）。生存のうち **3件が本物のテストの穴**（境界値 1件・監査ログの操作者と理由 2件）。性質テスト（PBT）8件を追加して **93.4%** に改善し、狙った3件を正確に殺した
- examples/approval-workflow/tests/test_properties.py: PROP-001〜006 の property-based test（Hypothesis）
- examples/approval-workflow/scripts/mutmut_to_json.py: mutmut → 最小契約 JSON のアダプタ。**plugin ではなく利用者側**に置く（特定ツールへの依存を plugin に持ち込まないため）
- examples/approval-workflow/docs/requirement-spec.md: 3.3 受入条件と Property（PROP-001〜006）、3.4 hold-out 受入テストの対象

**実証・テンプレート実例・決定論的チェック（先行実装分）**

- docs/ROADMAP.md: 次フェーズの改善・追加機能ロードマップ（実証・信頼性 / テンプレート充実 / Plugin 実用拡張）
- docs/case-study-01.md: ケーススタディ #1（申請承認ワークフローで J-SIX を一周。実測値と推定値を切り分け）— ROADMAP A1
- examples/approval-workflow/: 動く FastAPI サンプル（37テスト / カバレッジ99%）。記入済みテンプレ実例（CLAUDE.md / Spec×2 / ADR×2 / traceability）を兼ねる — ROADMAP B1/B2/C2
- plugin/scripts/: 決定論的チェックスクリプト3種（traceability_check / coverage_gate / run_checks）— ROADMAP C1
- plugin Stop Hook に command 型を追加（`.jsix-checks.json` 同梱時のみ動く品質ゲート、no-op 既定）— ROADMAP C1
- index.html: J-SIX の全体像を1枚に集約した自己完結型 HTML（外部依存なし。GitHub Pages のルートとしても機能）

### Changed

**リリース時の整合**

- index.html: v2.1 で追加した工程成果物27点・組立定義・合意成熟度（セクション 05）、第2サンプル monthly-billing と Plugin 実動検証（セクション 08・10）を反映。リポジトリ構成表に case-study-02 / plugin-field-test-01 / ROADMAP / templates/deliverables / monthly-billing を追加し、J-SIX.md の章数を「全8章」から「全9章」に訂正。基準日を 2026-09-19 に
- examples/monthly-billing: 計測結果を 2026-09-19 の再計測値に更新（テスト 93→101 件、339 ステートメント、mutation score 92.95% → 91.88%〔505 ミュータント中 464 killed〕）。ADR-0004 と CSV 列数の修正でコードとミュータントが増えたため。閾値 90% は満たす。traceability.md の計測日も同様
- examples/approval-workflow/README.md, README.md: ケーススタディ時点の値に加え、実動検証 #1（TASK-AW-002）後の現在値（テスト 81 件＋hold-out 72 件、カバレッジ 99.0%、mutation 92.42%、トレーサビリティ 21/21）を併記。README の実証表に monthly-billing と実動検証 #1 を追加

**計画**

- docs/ROADMAP.md: A1'（人手のみ実装との工数 A/B 比較）を見送りに変更。同一題材を人手のみで実装する工数と協力者を確保できないため。実装工数の削減率は 🟡 推定（未実測）のまま据え置き、実測値に基づく表示へは上げない。ケーススタディ #1 の次アクションと index.html の記述もあわせて更新

**工程成果物・設計書**

- plugin/skills/doc-reverse-gen: 種別を工程成果物の領域単位（`behavior` / `screen` / `data` / `external-if` / `batch` / `report` / `deliverables`）と `assemble <組立定義>` に再編。「基本設計書」を直接生成せず、工程成果物を逆生成してから組立定義に従って束ねる。由来ごとにしてよいことを分けた（人手由来の5点は生成せず存在確認のみ、③ は通っている受入テストだけを根拠にする）。v2.0 の種別 `basic` / `detail` / `if` / `db` は読み替えて受け付ける。Excel / Word の出力先を `docs/design-docs/export/` に変更（`docs/deliverables/` との混同を避ける）
- plugin/agents/doc-generator.md: 工程成果物 → 組立 → 品質系納品物の順に生成。組立定義が無い場合は「顧客と目次を合意していない」ことを報告する
- plugin/skills/spec-create, design-review: 非機能要求グレード（モデルシステム・6大項目）と合意成熟度のチェック項目を追加
- templates/deliverables/README.md, examples/monthly-billing/docs/deliverables/README.md: 合意成熟度を成果物ごとの到達基準として書き直した（従来の「Phase 2 ゲート通過＝完成レベル」は組立ガイドの記述と矛盾していた）。記入済み実例は顧客確認を経ていないため完成レベルとは書かない
- examples/monthly-billing/docs: 要求 Spec 3.5・Design Spec 7 を非機能要求グレード形式へ（モデルシステム: 社会的影響が限定されるシステム）。approval-workflow も同形式へ（モデルシステム: 社会的影響がほとんど無いシステム）。Design Spec は v2.0 構成のまま、5.3 に6大項目との対応表を追加。Spec 文書のみの変更でケーススタディの計測値は変わらない（ゲート再実行で mutation 93.4% を確認）

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
- plugin/skills/quality-metrics/SKILL.md: 役割を「個別タスクの合否判定」から「タスク横断のプロセス健全性の集計」へ。mutation score / G3 judge 却下率と理由分布 / ゲート失敗理由の分布 / 人間レビュー指摘数 を追加。judge を外す判断の材料として却下率を使う運用を明記
- plugin/skills/doc-reverse-gen/SKILL.md: 種別 `quality` を追加。証跡パッケージから従来の品質・テスト系納品物（テスト結果報告書 / 品質報告書 / セキュリティ診断結果 / トレーサビリティマトリクス / レビュー記録）へ変換する対応表と、3区分を保つ変換ルールを規定
- plugin/scripts/jsix_junit_check.py: 出力ラベルを引数化し、通常テストと hold-out を区別して表示
- plugin/hooks/hooks.json: PreToolUse の規約チェックを **prompt 型から command 型（決定論的 lint/format）へ置換**。prompt 型は助言用途に限定。Stop に「G3 未実施なら scope-judge を起動する」prompt hook を追加。StopFailure に Stop hook の8回上限を踏まえた判断基準を追記
- plugin/README.md: 4層ゲート、設計原則（ツールを呼ばず契約を決める）、scripts 一覧（11本）、`.jsix-checks.json` の新旧形式、内側/外側ループの二重化を反映。Skills 6→7 件 / Agents 5→7 件
- plugin/.claude-plugin/plugin.json: description を v2.1 の内容へ更新、`keywords` を追加（version は 2.1.0 のまま）
- docs/J-SIX.md 4.3: Plugin 構成を実装済みの構成（scripts 12本を含む）へ更新
- docs/walkthrough-phase4-tdd.md: v2.1 の全体像（Hold-out → Red → Green → Refactor → G1〜G4）を冒頭に追記し、Step 6 として品質ゲートの実行例を追加
- examples/approval-workflow/README.md: `make` ターゲット、品質ゲートの出力例、テスト弱体化がブロックされることの確認手順、Plugin デモ表に holdout-test-writer / scope-judge / evidence-pack を追加
- index.html / README.md: Plugin セクションを Skills 7 件 / Agents 7 件 / 決定論的チェック 11 本に更新
- docs/J-SIX.md: mutation score 行の検証ステータスを 🟡 未実測 → **🟢 実測例あり**（ケーススタディ #2 の実測に基づく。閾値 90% も実測由来であり、Plugin の既定値としては引き続き置かない）
- README.md / index.html: ケーススタディ #2 の実測値を反映。付録の展開予定を完了状態へ
- examples/approval-workflow/: `make mutation` / `make setup-mutation` を追加。`.jsix-checks.json` に mutation ゲート（`min_score: 90`）を有効化。トレーサビリティを REQ 10 + PROP 6 = 16 件に拡張
- examples/approval-workflow/docs/traceability.md: PROP ⇔ テスト、hold-out ⇔ ユースケースの対応表を追加
- docs/ROADMAP.md: A4 / C3 / C4 / C5 / C6 を完了に更新。v2.1 完了後の残タスクを整理
- .gitignore: mutation testing の生成物（`.hypothesis/`, `mutants/`, `.venv-mut/`）を除外

### Fixed

- plugin/scripts/jsix_evidence_pack.py: **証跡の再生成で人間の承認欄（07_approval.md）を空のテンプレートで上書きしていた**。ゲートは Stop のたびに走るため、承認を記入した後にゲートが走ると承認記録が消えた。記入済みの承認欄は上書きせず、対象 commit が変わった場合は `07_approval.<sha>.md` に記録を残して再承認を求める。あわせて、生成時刻以外が前回と同じなら証跡を書き直さない（ROADMAP C7。証跡の時刻を引用する設計書が収束しなかった）
- plugin/scripts: RED タグを自プロジェクトのディレクトリを変更したコミットのものから探す（ROADMAP C14）。1つのリポジトリに複数プロジェクトがあると、別プロジェクトのタスクのタグを比較元に拾っていた
- plugin/scripts: 証跡の 03 に生存ミュータントと未到達行を出す（ROADMAP C11）。mutation の最小契約 JSON で任意項目 `survivors` を受け付け、カバレッジはファイル別に未到達の行番号を保持する
- plugin/scripts/jsix_format_hook.py, plugin/hooks/hooks.json: format / lint Hook が (1) 拡張子を見ずに `ruff format` を実行し、`reports/evidence/judge.json` を Python として整形して（末尾カンマ）**JSON を壊していた**、(2) 編集の**前**（PreToolUse）に既存ファイルを整形していたため、直後の Write / Edit が「読んだ後に変更された」で失敗していた。quality-metrics のヘッドレス実行で発覚。Hook を PostToolUse に移し、対象ファイルを `.jsix-checks.json` の `hook_files`（glob）で宣言させる形にした（宣言が無ければ実行しない。`hook_cmd` 自体が未リリースの v2.1 機能のため互換性の影響なし）。両サンプルの設定に `"hook_files": ["*.py"]` を追加。テスト5件を追加
- plugin/scripts/jsix_run_checks.py: **品質ゲートがフェーズごとのコミットで空振りしていた**。変更ファイルを未コミットの差分だけで数えていたため、tdd-cycle の手順どおりコミットすると Stop の時点で差分が空になり、G1 スコープ検査は「0 ファイル」で何も検査せず、G3 は「変更なし」でスキップされていた（CI のスコープ検査も同様に 0 ファイルだった）。また `judge.json` がどの差分への判定かを照合しないため、前のタスクの PASS が残っていても通った。tdd-cycle のヘッドレス実行で、子セッション自身が報告して発覚。G3 と変更有無の判定は既定ブランチとの分岐点（または `scope.base`）からの差分で行い、スコープ検査は RED タグ以降の差分で行う（hold-out はタスク前半で正当にコミットされるため、deny は実装フェーズの規則として扱う）。G3 の判定は差分の指紋（`target`）に紐づけ、一致しない判定は「古い」として無効にする（判定ファイルと証跡の出力先は指紋から除外）。scope-judge エージェントに `target` の記録手順を追加。テスト5件を追加
- plugin/scripts/jsix_run_checks.py: Stop hook として呼ばれたとき（`--stop-hook`）、**失敗内容が変わらないブロックが3回続いたら停止を許可する**ようにした。Spec に REQ を追加した直後など、その工程では満たせない失敗で Stop のたびにブロックし続け、セッションが終わらなかった（spec-create のヘッドレス実行で15回。Claude Code 自身の8回上限も効かなかった）。判定は緩めずゲートは未達のまま残り、CI では止まる。上限は `stop_hook.max_identical_blocks` で変更可。状態はセッションごとに一時領域へ置きプロジェクトを汚さない。テスト8件を追加
- plugin/skills: テンプレートをリポジトリルートの `templates/` から読んでいたため、**インストールされた Plugin では Skill が動かなかった**（マーケットプレイスからのインストールでは Plugin ディレクトリだけがコピーされる）。`spec-create` は `` !`cat templates/spec/...` `` が失敗して起動直後に止まっていた。テンプレートを各 Skill に同梱し `${CLAUDE_SKILL_DIR}/templates/...` で参照する形に変更。正は `templates/` のままで、同梱分は `tools/sync_plugin_templates.py` が生成する（Plugin の外を指す相対リンクは GitHub の URL に書き換える）。CI に `--check` を追加し、CLAUDE.md の更新チェックリストにも追記
- plugin/hooks/hooks.json: prompt 型 Hook を「〜の場合は…してください。該当しなければ何も出力しない」という**指示文の形**で書いていた。prompt 型 Hook は判定役のモデルが `{ok, reason}` を返す評価器で「何も出力しない」選択肢が無いため、**Stop が毎回ブロックされセッションが止まらなくなっていた**（Skill をヘッドレス実行した design-review で同じやり取りが10回以上繰り返された）。ADR 提案の Hook を「ok を false にする条件」を明示する評価器の形に書き直し（迷う場合と `stop_hook_active` が true の場合は ok）、G3 起動の Hook は command 型ゲートの案内と重複していたため削除。判定すべき条件の無い PostToolUse（テスト結果確認）・StopFailure・PermissionDenied の prompt 型 Hook も削除した
- plugin/scripts/jsix_run_checks.py: git 管理下で変更ファイルが無いセッションでは G3（scope-judge の判定）を求めないようにした。レビューや調査だけの作業でも毎回 scope-judge の起動を強いていた。テスト2件を追加
- plugin/.claude-plugin/plugin.json: `repository` をオブジェクト（`{type, url}`）で書いていたため、Claude Code がマニフェストを不正と判定し **Plugin 全体が読み込まれていなかった**（Skill / Agent / Hook のいずれも動かない）。文字列に修正し、`claude plugin validate` の通過と、`--plugin-dir` で Skill 7 / Agent 7 が登録されることを確認。Skill をヘッドレス実行して実行ログを取ろうとした際（ROADMAP C2）に発覚した。CI に `plugin validate` のジョブを追加し、ワークフローの対象パスを `plugin/**` に広げた
- examples/monthly-billing: 依存から python-multipart を外した。CI の G1 deps（trivy）が 0.0.20 に HIGH 3件を検出してゲートが止まったが、修正版は Python 3.10 以上を要求しサンプルの前提（3.9+）と両立しない。form の解析は1項目（`actor`）だけなので標準ライブラリ `urllib.parse` で読み、multipart/form-data は既定値で黙って確定させず 415 で拒否する（ADR-0004）。回帰テスト1件を追加し、python-multipart をアンインストールした環境で全テスト通過を確認
- examples/monthly-billing/app/importer.py: 列数がヘッダと合わない CSV 行の扱い。不足列は `csv.DictReader` が None で埋めるため変換時に `TypeError` となり、**1行の不備で日次取込全体が止まっていた**（「1行の不備で取込全体を止めない」という仕様に反する）。過多の行は黙って取り込まれていた。どちらもエラー行として記録して継続するよう修正し、回帰テスト2件を追加。テストデータが常に正しい列数だったため、カバレッジ 98.8% / mutation 92.3% でも検出できず、PR 前のコードレビューで見つかった。外部 IF 処理説明と外部 IF 一覧（記入済み実例）、外部 IF 処理説明テンプレートの「書き落としやすい点」にも反映
- templates/deliverables/README.md ほか: 由来の内訳が実ファイルと食い違っていた（「逆生成16＋受入テスト1／人手7」と記載していたが、各成果物の冒頭の由来を数えるとコード逆生成18・受入テスト逆生成1・併用3・人手5）。「27点中17点が実物から起こせる」は19点に訂正。monthly-billing README の領域別表も合計が行の和（19）と合っていなかった
- CHANGELOG.md: IPA ガイド・国税庁 Q&A の参考文献番号を実際の [32][33] に訂正

- plugin/scripts/jsix_run_checks.py: `--gates` オプションを追加。J-SIX.md 4.4 と CI の例は「G3 は CI では必須にしない」と規定していたが、それを実現する手段が無く、CI でゲートを実行すると必ず G3 未実施で止まっていた（設計意図と実装の食い違い）。除外したゲートは「未実行」として結果に残す
- plugin/scripts/jsix_run_checks.py: G3 未実施の案内に実行環境の絶対パスが出ていたため、プロジェクト基準の相対パスに変更
- plugin/scripts/jsix_run_checks.py: コマンド失敗時に stderr が出力から落ちていた（findings の `text` キーを render が拾っていなかった）。「失敗した」とだけ出て理由が分からない状態だったため、CI ログから原因を判断できなかった
- examples/approval-workflow: hold-out 受入テストと性質テストに `ruff format` が未適用だった。内側ループ（レポート駆動）は `format` を実行しないため、CI（外側ループ）で初めて検出された
- plugin/scripts/jsix_config.py: v2.0 のフラット形式でトレーサビリティの ID パターンが未指定の場合、v2.1 の既定（`REQ-\d+` と `PROP-\d+` の両方）ではなく **v2.0 の既定（`REQ-\d+` のみ）に固定**するようにした。そうしないと、Spec に `PROP-nnn` を書いた既存利用者のゲートが Plugin 更新だけで突然落ちる

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
