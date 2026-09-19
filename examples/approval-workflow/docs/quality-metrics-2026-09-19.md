# 品質メトリクスレポート — TASK-AW-002 の前後比較

**プロジェクト**: 申請承認ワークフロー（approval-workflow）
**集計日**: 2026-09-19
**集計期間**: `05fe639`（2026-09-12、main 相当）〜 `d652475`（HEAD）
**対象タスク数**: 2（`reports/evidence/` の証跡パッケージ `untagged` と `TASK-AW-002`）
**集計方法**: J-SIX quality-metrics Skill（Phase 5）。ゲートは再実行せず、既存の成果物を読んだ

> 数値はすべて下表「出典」の成果物から引用した。成果物に無い指標は「未計測」と書き、推定で埋めていない。
> 「差分」「モジュール別 score」は引用した値からの単純な計算で、表中でそう明記している。

---

## 0. 比較対象と出典

| 区分 | 対象 commit | 出典 | 備考 |
|---|---|---|---|
| 前（TASK-AW-002 実施前） | `05fe639` 相当 | `reports/evidence/untagged/`（commit `6cb5b96` で生成）、`reports/gate-ci.json`、`docs/case-study-02.md` | `05fe639..6cb5b96` の差分は `.jsix-checks.json` / `Makefile` / `docs/*-spec.md` のみ。`app/` と `tests/` は同一 |
| 後（TASK-AW-002 実施後） | `d652475`（HEAD） | `reports/evidence/TASK-AW-002/`、`reports/junit.xml`、`reports/junit-acceptance.xml`、`reports/mutation.json`、`coverage.xml`、`reports/evidence/judge.json` | 証跡は最初 commit `27ca6cf` で生成された（`27ca6cf..d652475` の差分は `docs/traceability.md` のみ）。本レポートを追加したあと Stop hook で G3 を再判定し、証跡は `d652475` で再生成された。数値は変わっていない |

- 前の値は依頼で示されたケーススタディ #2 の計測値（テスト 45件 / hold-out 10件 / カバレッジ 99.0% / mutation 93.4%）と、`untagged` 証跡の値が一致することを確認した。
- 両証跡の `config_sha256` は同じ（`a5721c0d…`）。同じゲート設定で判定している。

---

## 1. プロセスの健全性

| メトリクス | 後（TASK-AW-002） | 前（05fe639） | 判断 |
|---|---|---|---|
| mutation score（全体） | **92.42%**（183 / 198） | 93.44%（171 / 183） | −1.02pt（計算値）。閾値 90% は両方とも満たす。低下の原因は §3 を参照 |
| mutation score（中央値、タスク横断） | 92.93%（2 タスクの中央値、計算値） | — | N=2 のため傾向を読むには少ない |
| G3 judge 却下率 | **0%**（0 / 2） | — | 2 タスクとも 1 回目で PASS。N=2 では「judge が不要になった」とは判断できない |
| G3 却下理由の内訳 | correctness 0 / requirement 0 / scope 0 | — | 却下が無いため還元先なし |
| 人間レビュー指摘数 / PR | **未計測** | **未計測** | 両方の `07_approval.md` が未記入（指摘事項欄・承認欄が空） |

### G3 について補足

- 後: `judge.json` は verdict PASS、attempt 1、reasons なし。最初の判定対象は `05fe639..27ca6cf`（`docs/traceability.md` の未コミット変更を含む作業ツリー）だった。本レポートを追加して diff が変わったため、Stop hook が G3 を「判定が古い」として止めた。そこで `05fe639..d652475` と本レポートを対象に再判定し、PASS だった。この再判定はゲートの失敗ではなく、judge が対象の変化を検出して再判定を求める仕組みが働いたものなので、却下率には数えていない。
- 前: `untagged` 証跡には G3 PASS（attempt 1）があるが、同じ時点の `reports/gate-ci.json` には G3 の項目が無い。CI 用の実行では judge を通していない。

---

## 2. ゲート失敗理由の分布

| ゲート | チェック | 失敗回数 | 還元先 |
|---|---|---|---|
| G1 | 全チェック | 0 | — |
| G2 | 全チェック | 0 | — |
| G3 | judge | 0 | — |

**失敗 0 件は「失敗が無かった」ことを意味しない。** 証跡パッケージと `gate.json` はタスクごとに最後の 1 回で上書きされるので、途中で失敗した実行の記録は残らない。このため、このメトリクスは Phase 0 の月次ループの入力として働いていない（§6 のアクション 1）。

### 実施されなかったチェック（証跡上）

| チェック | 前 | 後 | 理由（証跡の記載） |
|---|---|---|---|
| G1 build / lint / format | ⏭（証跡） / ✅（`gate-ci.json`） | ⏭（証跡） / ✅（`gate.json`） | 証跡パッケージはレポート駆動モードで生成され、コマンドを実行していない。`gate.json` / `gate-ci.json` ではコマンドを実行して成功している |
| G1 secrets / deps | ⏭ | ⏭ | `reports/secrets.sarif` / `reports/deps.sarif` が無い（optional 指定。CI で生成される想定） |
| G2 test_tamper | ⏭ | ✅ | 前は RED タグが無かった。後は `jsix/red-TASK-AW-002` を基準点にして検査した |

G1 scope の変更ファイル数は実行ごとに変わっている。`gate.json`（13:32 生成）は 4、`27ca6cf` で生成した証跡（13:37）は 5、`d652475` で本レポートを含めて再生成した証跡（13:41）は 6 と記録している。`gate.json` には commit SHA が無く、どの commit を判定したか特定できない。

---

## 3. 個別タスクの指標（証跡から引用）

| タスク | テスト | hold-out | カバレッジ（行） | mutation | トレース | G3 |
|---|---|---|---|---|---|---|
| 前（untagged / `6cb5b96`） | 45 / 45 通過 | 10 / 10 通過 | 99.03%（205 / 207） | 93.44%（171 killed / 12 survived） | 16 / 16（REQ 10 / PROP 6） | PASS |
| TASK-AW-002（`27ca6cf` / `d652475`） | 81 / 81 通過 | 72 / 72 通過 | 99.04%（207 / 209） | 92.42%（183 killed / 15 survived） | 21 / 21（REQ 12 / PROP 9） | PASS |
| 差分（計算値） | +36 | +62 | +0.01pt（+2 行） | −1.02pt（ミュータント +15、生存 +3） | +5（REQ +2 / PROP +3） | — |

すべて失敗 0 / エラー 0 / スキップ 0（`junit.xml` / `junit-acceptance.xml` の testsuite 属性）。

### 3.1 カバレッジ

出典: `coverage.xml`（後）、`reports/evidence/untagged/03_coverage_mutation.md`（前）

| ファイル | 後 | 前 | 未到達行（後） |
|---|---|---|---|
| `workflow.py` | 99.0%（96 / 97） | 99.0%（95 / 96） | 133 |
| `models.py` | 97.7%（43 / 44） | 97.7%（43 / 44） | 72 |
| `main.py` | 100.0%（68 / 68） | 100.0%（67 / 67） | — |

- 分岐カバレッジは**未計測**（`coverage.xml` の `branches-valid="0"`）。
- カバレッジは `make test` の計測で、hold-out（`tests/acceptance/`）は含まない。
- `models.py:72` は `next_approver` の範囲外ガード（防御的な分岐）。
- `workflow.py:133` は `remand` を現在の承認者以外が呼んだときの `WorkflowError` 送出。到達できる行で、可視テスト（`tests/`）には、この経路を通るテストが無い。hold-out には `tests/acceptance/test_cross_error_classification.py:293`（`("remand", "carol")`、REQ-008）があるが、hold-out はカバレッジの計測に入らない。
- 前の未到達行の行番号は成果物に記録が無い（件数 2 だけが分かる）。そのため、前後で同じ行かどうかは確認していない。

### 3.2 mutation score

出典: `reports/mutation.json`（後、mutmut 3.7.0）、`docs/case-study-02.md` §2・付録（前）、`mutants/app/*.meta`（後のモジュール別件数）

| モジュール | 後 | 前 | 増減（計算値） |
|---|---|---|---|
| `app/workflow.py` | 148 / 160（92.5%） | 139 / 151（92.1%） | 生存 12 → 12 |
| `app/main.py` | 35 / 38（92.1%） | 32 / 32（100%） | 生存 0 → **3** |
| 全体 | 183 / 198（92.42%） | 171 / 183（93.44%） | 生存 12 → 15 |

**全体 score の低下（−1.02pt）は、新しく生き残った `app/main.py` の 3 件だけが原因である。** 3 件とも `_guard` の `RequestNotFound → 404` 変換（TASK-AW-002 で追加）で、変異先は `detail` の値である（`mutmut show` で確認）。

| ミュータント | 変異内容 |
|---|---|
| `app.main.x__guard__mutmut_2` | `detail=str(exc)` → `detail=None` |
| `app.main.x__guard__mutmut_4` | `detail=str(exc)` → 引数を削除 |
| `app.main.x__guard__mutmut_6` | `detail=str(exc)` → `detail=str(None)` |

- ステータスコード 404 への変異は殺せている。生き残ったのは本文の文言だけ。
- 404 の `detail` の内容は `docs/requirement-spec.md` / `docs/design-spec.md` / ADR-0003 のどれにも定義されていない。このため、ケーススタディ #2 が「エラーメッセージ文言」（等価に近い変異）に分類した 12 件と同じ種類と判断できる（分類は本レポートの判断で、ツールの出力ではない）。
- `workflow.py` の生存は 12 件のまま。関数ごとの件数（`create_request` 4 / `submit` 2 / `reject` 1 / `remand` 2 / `withdraw` 1 / `_ensure_pending` 1 / `_log` 1）も前と同じ。ただしコードが変わったため mutmut の通し番号はずれており（`submit` 6,9 → 7,10、`withdraw` 6 → 7）、同じミュータントかどうかは ID では確認できない。

### 3.3 テスト改変検出（後のみ）

出典: `reports/evidence/TASK-AW-002/05_scope_and_integrity.md`

| 指標 | 基準点 `jsix/red-TASK-AW-002` | 現在 | 増減 |
|---|---|---|---|
| アサーション数 | 191 | 191 | +0 |
| テスト関数数 | 96 | 96 | +0 |
| 無効化マーカー数 | 0 | 0 | +0 |
| 実装から hold-out への参照 | — | 0 | — |

Green 以降に `tests/test_properties.py` と `tests/test_workflow.py` が変更されているが、どちらもアサーション数とテスト関数数は変わっていない（refactor コミット `34e625e` / `05b35b4` の範囲）。
（テスト関数数 96 は `tests/**` の関数定義の数。JUnit の 81 + 72 件はパラメタ化されたケースを数えるため、単位が違う。）

---

## 4. コード品質・セキュリティ

| 指標 | 後 | 前 | 出典 |
|---|---|---|---|
| lint（ruff） | 成功（件数は記録なし） | 成功（件数は記録なし） | `gate.json` / `gate-ci.json` |
| format（ruff format） | 成功 | 成功 | 同上 |
| SAST（Bandit 1.8.6） | error 0 / warning 0 / note 0 | error 0 / warning 0 / note 0 | `04_security.md` |
| 秘密情報スキャン | 未計測 | 未計測 | SARIF なし |
| 依存脆弱性 | 未計測 | 未計測 | SARIF なし |

lint の警告数・カテゴリ別の集計は成果物に無いため**未計測**。

---

## 5. Spec ⇔ コード整合性・ADR

| 指標 | 後 | 前 | 出典 |
|---|---|---|---|
| REQ のテスト網羅 | 12 / 12 | 10 / 10 | `01_traceability.md` |
| PROP のテスト網羅 | 9 / 9 | 6 / 6 | 同上 |
| 未トレース | 0 | 0 | 同上 |
| ADR | 0001〜0003（0003 はエラー分類。TASK-AW-002 で追加） | 0001〜0002 | `docs/adr/` |

TASK-AW-002 の起点は設計レビュー（`docs/reviews/design-review-2026-09-19.md`）の指摘 C-1 / C-2。その判断は ADR-0003 と design-spec 1.1 に記録されている。

---

## 6. 次のアクション

- [ ] **ゲート失敗の履歴を残す。** 証跡パッケージと `gate.json` は最後の実行で上書きされ、「ゲート失敗理由の分布」が常に 0 件になる。実行ごとの結果を追記する仕組み（例: `reports/gate-history.jsonl`）を Plugin 側に入れないと、Phase 0 の月次ループの入力が得られない
- [ ] **`07_approval.md` を記入する。** 人間レビューの指摘数は前後とも未記入で、ゲートの外形指標が取れていない。TASK-AW-002 はレビュアー・責任者の承認欄も空のまま
- [ ] **404 の `detail` を仕様にするかどうか決める。** 決めるなら Spec に書き、受入テストで検証する（生存 3 件が殺せる）。決めないなら、ケーススタディ #2 の 12 件と同じく等価に近い変異として扱う。**テストだけを先に足して score を上げることはしない**（仕様にない詳細を監督面に持ち込まないため）
- [ ] **`remand` を現在の承認者以外が呼ぶ経路（REQ-008、`workflow.py:133`）を可視テストで押さえる**かどうか決める。いまは hold-out でしか検証されておらず、カバレッジ上は未到達の 1 行として残っている
- [ ] **mutation score の下限 90% は据え置く。** 生存 15 件はすべて文言か既定引数の種類で、本物のテストの穴は新たに見つかっていない（§3.2）。N=2 のため、下限の見直しはタスクがさらに溜まってから行う
- [ ] **G1 build / lint / format を実行した状態で証跡パッケージを作る。** 証跡では現状「未実施」になっており、納品物として弱い（`--run-commands` か CI の証跡を使う）
- [ ] **secrets / deps の SARIF をローカルでも生成する**か、CI の証跡を正式版にすると決める
- [ ] **G3 judge の継続判断は保留する。** 却下 0 / 2 だが件数が少なすぎる。10 タスク程度溜まってから却下率と理由の内訳を見る
