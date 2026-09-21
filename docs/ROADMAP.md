# J-SIX 改善ロードマップ

**Author**: H.Sekita | **対象バージョン**: v2.1 → v2.5 想定

J-SIX は v2.0・全15記事公開で一区切りついた。本ロードマップは次フェーズの改善・追加機能を、
**実証・信頼性 / テンプレート充実 / Plugin 実用拡張** の3領域で整理したものである。
大規模・複数チーム向けの構想（J-SIX Hub）は、この3領域とは独立した H として末尾の表に置く。

> **基本方針**: A1 のケーススタディ題材を1つ決め、それを B（テンプレ実例）と C（デモ）で
> 使い回す。3領域をバラバラに進めず、**1本の実証ストーリー**に束ねることで信頼性を最大化する。

---

## クイックウィン（即着手可・各30分以内）

| # | 内容 | 対象 | 状態 |
|---|---|---|---|
| Q1 | plugin.json version を 2.0.0 へ整合 + CHANGELOG 追記（v2.0.0 で hooks.json を変更したが version が 1.1.0 のまま） | `plugin/.claude-plugin/plugin.json` | ✅ 2026-06-14 |
| Q2 | REFERENCES_AUDIT の監査日更新＋鮮度チェック | `docs/REFERENCES_AUDIT.md` | ✅ 2026-06-14 |

---

## A. 実証・信頼性

**狙い**: 「すべて著者推定」という最大の弱点を埋める。

| # | タスク | 成果物 | 規模 | 状態 |
|---|---|---|---|---|
| A1 | **ミニ実証ケーススタディ**（小規模題材で J-SIX を一周：Spec→TDD→逆生成→メトリクス）。実測値と推定値を切り分け | `docs/case-study-01.md` ＋ `examples/approval-workflow/` | 中〜大 | ✅ 2026-06-14（題材: 申請承認WF / FastAPI） |
| A2 | 期待効果の数値に「検証ステータス」列を追加（推定/実測/外部出典を明示） | `docs/J-SIX.md` 第1章, `README.md` | 小 | ✅ 2026-06-14 |
| A3 | 出典鮮度の定期レビュー運用（四半期）。`/schedule` 化も検討 | `docs/REFERENCES_AUDIT.md` に運用節追加 | 小 | ✅ 2026-06-14（7.3 に運用節。2026-09-10 に第2回を実施） |
| A1' | 同一題材で「人手のみ実装」との工数 A/B 比較（工数削減の初の実測） | case-study に追記 | 中 | ⏹ **見送り**（2026-09-19）。同一題材を人手のみで実装する工数と協力者を確保できないため。実装工数の削減率は 🟡 推定（未実測）のまま据え置き、実測値に基づく表示へは上げない。人手実装の協力者と題材が得られた場合に再開する |
| A4 | **ケーススタディ #2**: カバレッジ 99% のコードの mutation score を実測。生存ミュータントから導出した PBT で何が見つかったかを記録 | `docs/case-study-02.md` ＋ `examples/approval-workflow/` | 中 | ✅ 2026-09-10（91.8% → PBT 追加で 93.4%。本物のテストの穴3件を検出） |
| A5 | 第1章 1.3「CC の現実的な能力水準」のデータ更新（Sonnet 4.5 世代のまま。最新モデル・最新調査へ差し替え） | `docs/J-SIX.md` 第1章 | 小 | ☐（v2.1 の範囲外。次回の鮮度レビューで実施） |

## B. テンプレート充実

**狙い**: プレースホルダーのみ → 「動く実例」を併置し初心者の導入障壁を下げる。

| # | タスク | 成果物 | 規模 | 状態 |
|---|---|---|---|---|
| B1 | **記入済みサンプル**（FastAPI api-service の CLAUDE.md 実例） | `examples/approval-workflow/CLAUDE.md` | 中 | ✅ 2026-06-14 |
| B2 | Spec / ADR の記入済み実例（A1 題材と連動） | `examples/approval-workflow/docs/`（spec×2, adr×2, traceability） | 中 | ✅ 2026-06-14 |
| B3 | templates/README に「テンプレ → 実例 → 該当 Skill」の導線表を追加 | `templates/README.md` | 小 | ✅ 2026-06-14 |
| B1' | 別スタック（Next.js / Spring Boot）の記入済み CLAUDE.md 実例 | `examples/` | 中 | ☐（FastAPI 版を先行） |
| B4 | **工程成果物テンプレート（IPA 27点）と記入済み実例**。画面・帳票・バッチを持つ第2サンプルを新設し、実例から逆算してテンプレートを作る | `templates/deliverables/`, `examples/monthly-billing/` | 大 | ✅ 2026-09-19 |
| B5 | 顧客様式への組立定義（基本設計書・詳細設計書）、`doc-reverse-gen` の工程成果物単位への再編 | `templates/deliverables/assembly/`, `plugin/skills/doc-reverse-gen/` | 中 | ✅ 2026-09-19 |
| B6 | Spec テンプレートの非機能要件を IPA 非機能要求グレードの6大項目へ、合意成熟度を Phase Gate の判定基準へ | `templates/spec/`, `docs/J-SIX.md` | 小 | ✅ 2026-09-19 |
| B6' | approval-workflow の Spec を非機能要求グレード形式へ移行 | `examples/approval-workflow/docs/` | 小 | ✅ 2026-09-19（Spec 文書のみの変更でコード・計測値は不変。ゲート再実行で mutation 93.4% を確認） |

## C. Plugin 実用拡張

**狙い**: 「説明はあるが prompt 型 Hook のみ」→ **決定論的に動く**ガードレールへ。

| # | タスク | 成果物 | 規模 | 状態 |
|---|---|---|---|---|
| C1 | **コマンド型 Hook 追加**（カバレッジ閾値ゲート、要件⇔テストのトレーサビリティ自動チェック）。番外編 Hooks 記事の知見を本体還元 | `plugin/scripts/` ×3 + Stop command Hook（オプトイン） | 中 | ✅ 2026-06-14 |
| C2 | **end-to-end デモ**（B1/A1 と同一題材で Skills 6 / Agents 5 を実際に動かした証跡） | `examples/approval-workflow/README.md`（Phase別 Skill 対応表） | 大 | ✅ 2026-09-19（7 Skill を Plugin 経由でヘッドレス実行。[Plugin 実動検証 #1](plugin-field-test-01.md)。Plugin の不具合8件を発見・修正） |
| C3 | plugin.json に `keywords` 等メタ補強、インストール手順の検証 | `plugin/.claude-plugin/plugin.json` | 小 | ✅ 2026-09-10 → **2026-09-19 訂正**: `repository` の形式がマニフェスト仕様に反し、Plugin が読み込まれていなかった。インストール手順の検証は実際には不十分だった。修正し、CI に `claude plugin validate` を追加 |
| C4 | **4層品質ゲート（G1-G4）の実装**。標準フォーマット（JUnit XML / Cobertura・LCOV / SARIF / mutation-testing-elements JSON）のパースと閾値判定に限定し、言語依存のツール呼び出しを持ち込まない | `plugin/scripts/` ×13, `plugin/agents/` ×7, `plugin/skills/` ×7 | 大 | ✅ 2026-09-10（単体テスト 155 件） |
| C5 | **証跡パッケージ**（顧客納品対応）。証跡 / 参考所見 / 承認の3区分で出力 | `jsix_evidence_pack.py` + `evidence-pack` Skill | 中 | ✅ 2026-09-10 |
| C6 | **CI 例（外側ループ）**。Hook が解除されても止まる二重化 | `.github/workflows/jsix-gate.yml` | 小 | ✅ 2026-09-11（実際に実行して緑を確認） |
| C7 | 証跡パッケージをゲート実行のたびに新しい時刻で再生成しない（内容が同じなら保持）。証跡の時刻を引用する設計書が収束しない | `jsix_evidence_pack.py` | 小 | ✅ 2026-09-19（あわせて、再生成で人間の承認欄 07 を上書きしていた不具合を修正） |
| C8 | ドキュメントだけの変更で G3 を再判定させない選択肢（指紋の対象パスを設定可能に） | `jsix_run_checks.py` | 小 | ✅ 2026-09-19（`g3.fingerprint_paths`。既定はプロジェクト全体） |
| C9 | ゲート失敗の履歴を残し、Phase 0 の月次ループ（失敗理由の還元）の入力にする | `jsix_run_checks.py`, `quality-metrics` | 中 | ✅ 2026-09-19（`reports/gate-history.jsonl`） |
| C10 | tdd-cycle がタスク定義（受入条件・許可範囲）をファイルに保存し、scope-judge が参照する | `tdd-cycle`, `scope-judge` | 小 | ✅ 2026-09-19（`docs/tasks/<タスクID>.md`。無ければ G3 は REJECT） |
| C11 | `03_coverage_mutation.md` に生存ミュータントの内訳と未到達行を出す | `jsix_evidence_pack.py` | 小 | ✅ 2026-09-19 |
| C14 | RED タグの解決をプロジェクト単位にする。タグはリポジトリ共有のため、モノレポでは別プロジェクトのタスクの `jsix/red-*` を比較元に拾う（`JSIX_TASK_ID` 未指定時） | `jsix_test_tamper_check.py`, `jsix_run_checks.py` | 小 | ✅ 2026-09-19（自プロジェクトのディレクトリを変更したコミットのタグだけを使う） |
| C13 | ヘッドレス実行を `claude plugin eval` の評価ケースにし、Plugin 変更時の受入試験にする | `plugin/evals/` | 中 | ✅ 2026-09-19（2ケース。各3回で6回とも満点、$3.79。CI では実行せず、Plugin 変更時とリリース前に手元で実行） |

## H. J-SIX Hub（構想）

**狙い**: 大規模・複数チーム・複数ベンダーの案件で、工程（Phase・ゲート・証跡）の適合性を中央で統制する構想を、方法論レベルの提案としてまとめる。実案件への適用は行わない。
J-SIX 本体は Hub に依存しない（[ADR-0003](control-plane/adr/0003-dependency-direction-and-process-as-data.md)）。A〜C とは独立に進め、J-SIX 本体の版数とも連動させない。

| # | タスク | 成果物 | 規模 | 状態 |
|---|---|---|---|---|
| H0 | 決定事項（D1〜D9）の記録 | `docs/control-plane/README.md`, `docs/control-plane/adr/` ×5 | 小 | ✅ 2026-09-22（ADR は「提案中」） |
| H1 | 構想文書（課題・状態モデル・関連研究・評価計画・課題と制約）とスイムレーン図。関連研究の出典を REFERENCES_AUDIT で監査 | `docs/control-plane/concept.md` | 大 | ✅ 2026-09-22（関連研究 [35]-[59] を REFERENCES_AUDIT 2.9 に登録。「フェーズ状態機械による統制は既存に見当たらない」は否定されたため、独自性を4点の組み合わせに改めた。ICSSP・JSEP 等は未確認で、論文化の前に追加調査する） |
| H2 | プロセス定義のデータ化（Phase・ゲート・成果物・役割・遷移・逸脱）と JSON Schema、CI でのスキーマ検証。J-SIX.md との照合結果を報告 | `process/jsix-process.yaml`, `process/jsix-process.schema.json` | 中 | ☐ |
| H2' | Plugin から `jsix-process.yaml` を参照する実装（H2 では設計メモのみ） | `plugin/` | 中 | ☐（H2 の後に判断） |
| H3 | リプレイ用イベントデータ。approval-workflow の実行記録から、実測 / 再構成のラベル付きで作成。記録が不足すればイベント出力用 Hook（オプトイン）を Plugin に追加して再実行 | j-six-hub `data/`（Hook を追加する場合は `plugin/`） | 中 | ☐ |
| H4 | リプレイ型サンプル Web アプリ（静的・GitHub Pages）。Hub 自体を J-SIX で開発する | [j-six-hub](https://github.com/SeckeyJP/j-six-hub) | 大 | ☐ |
| H5 | Hub を J-SIX で開発した記録のケーススタディ | `docs/case-study-NN.md` | 中 | ☐（番号は着手時点で決める） |

---

## 推奨実行順（依存関係を考慮）

```
Q1,Q2（整合）→ A1 ケーススタディ題材を決定
        └→ その題材を B1/B2（実例）と C2（デモ）で再利用 ＝ 一貫した1本の縦串
C1（Hook）は独立して並行可
A2,A3,B3,C3 は仕上げ
```

### v2.1 完了後の残タスク

```
A5 （第1章 1.3 の能力データ更新）  ← 次回の四半期鮮度レビューで実施
B1'（Next.js / Spring Boot の記入済み実例）
中規模題材での mutation score 再現（ケーススタディ #2 の次アクション）
```

A1'（人手のみ実装との工数 A/B 比較）は見送った（上表）。工数削減は推定のまま扱う。

### H（J-SIX Hub）の順序

```
H0 → H1 → H2 → (H3 ∥ H4 前半) → H4 後半
```

---

## 改訂履歴

| Date | 内容 |
|---|---|
| 2026-06-14 | 初版作成（v2.0 完了後の次フェーズ計画） |
| 2026-09-10 | v2.1（レビュー前品質ゲートの再設計）を反映。A2/A3 の実績を反映、A4/A5・C4/C5/C6 を追加 |
| 2026-09-10 | v2.1 完了。A4・C3・C4・C5・C6 を実績反映。残タスクは A1'（工数 A/B 比較）、A5（1.3 能力データ更新）、B1'（別スタック実例）、C2（Skill 実行ログ）|
| 2026-09-19 | B4-B6・B6' を追加し完了（工程成果物テンプレート・組立定義・非機能要求グレード対応） |
| 2026-09-19 | C2 完了（Plugin 実動検証 #1）。そこで見つかった C7〜C11・C14 を完了。C13（評価ケース化）が残る |
| 2026-09-19 | C13 完了（`plugin/evals/`） |
| 2026-09-19 | A1'（人手のみ実装との工数 A/B 比較）を見送り。実装工数の削減率は推定のまま据え置く |
| 2026-09-19 | v2.1.0 をリリース。残タスクは A5（12月の鮮度レビュー）、B1'（別スタック実例）、中規模題材での mutation score 再現。A1' は見送り |
| 2026-09-22 | H（J-SIX Hub の構想）を追加。H0（決定事項の記録）を完了。項目番号は、構想の決定事項 D1〜D9 と区別するため H とした |
| 2026-09-22 | H1（構想文書）を完了 |
