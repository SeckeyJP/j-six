# ケーススタディ #2 — 「カバレッジ 99%」の mutation score を実測する

**Author**: H.Sekita | **Date**: 2026-09-10 | **題材**: 申請承認ワークフロー（[ケーススタディ #1](case-study-01.md) と同一）

> J-SIX v2.1 は「カバレッジは必要条件であって十分条件ではない」と主張し、Phase 4 の G2 に
> mutation score を加えた。本ケーススタディはその主張を**同一題材で実測**する試みである。
> ケーススタディ #1 で **カバレッジ 99%** を達成したコードに mutation testing をかけたら、
> mutation score はいくつになるのか。そして生き残ったミュータントからどんな性質テストが
> 導けるのか。

---

## 1. 何を確かめたか

| 問い | 答え |
|---|---|
| カバレッジ 99% のコードの mutation score は？ | **91.8%**（183 ミュータント中 168 killed / 15 survived） |
| 生存ミュータントは本物のテストの穴か？ | **15件中3件が本物**。残り12件はエラーメッセージ文言などの等価に近い変異 |
| 性質テスト（PBT）を足すと改善するか？ | **93.4%**（171 killed / 12 survived）。狙った3件を正確に殺した |
| 閾値はいくつが妥当か？ | この題材では **90%**。ただし N=1 であり一般化しない（後述） |

**カバレッジ 99% と mutation score 91.8% の差（約7pt）が、「テストが実行した行」と
「テストが誤りを検出できる行」のずれである。** これが v2.1 で mutation score を
G2 に加えた理由の実測的な裏づけになる。

---

## 2. 測定条件（再現情報）

| 項目 | 値 |
|---|---|
| 対象 | `examples/approval-workflow/app/`（368 行 / 207 ステートメント） |
| テスト | `tests/`（例ベース 37件 + hold-out 受入 10件） |
| カバレッジ | 99%（207 stmt 中 未到達 2）— ケーススタディ #1 と同一 |
| mutation ツール | mutmut 3.7.0 |
| Python | 3.13.12（mutation 実行用。アプリ本体は 3.9 でも動作） |
| ミュータント総数 | 183（`app/workflow.py` 151 / `app/main.py` 32） |

### 再現手順

```bash
cd examples/approval-workflow
make setup            # 本体（Python 3.9+）
make setup-mutation   # mutation 用（Python 3.10+ が必要）
make test             # カバレッジ計測
make mutation         # mutation score 計測 → reports/mutation.json
make gate             # 品質ゲート G1→G4
```

### 環境上のつまずき（記録）

mutmut 3.3.1 を **Python 3.9** で動かすと、ミュータントの trampoline が
`multiprocessing.set_start_method('fork')` を実行時に呼び、`RuntimeError: context has
already been set` で停止した。mutmut 3.x は Python 3.10+ を前提としている。

対処として mutation testing 専用の venv（Python 3.13）を分けた。アプリ本体の実行環境は
3.9 のまま変えていない。**mutation testing のためにプロダクトの対応バージョンを
上げる必要はない**という点は、導入判断の材料になる。

---

## 3. 実測 ①：PBT 追加前

```
183 ミュータント: 168 killed / 15 survived / 0 timeout / 0 skipped
mutation score = 168 / 183 = 91.80%
```

### 生存した 15 件の内訳

| 分類 | 件数 | 内容 | 本物の穴か |
|---|---|---|---|
| エラーメッセージ文字列の変異 | 9 | `"タイトルは必須です"` → `"XXタイトルは必須ですXX"` 等 | ✗（API は 409 を返すため外部の振る舞いは不変） |
| 既定引数 `note=""` の変異 | 3 | `note: str = ""` → `note: str = "XXXX"` | ✗（監査ログの既定 note を検証していないだけ） |
| **境界値** | 1 | `if amount <= 0` → `if amount <= 1` | **✓ 本物** |
| **監査ログの操作者** | 1 | `self._log(req, Action.REMAND, actor, note)` → `self._log(req, Action.REMAND, note)` | **✓ 本物** |
| **監査ログの note** | 1 | `self._log(req, Action.REMAND, actor, note)` → `self._log(req, Action.REMAND, actor, )` | **✓ 本物** |

### 本物の穴3件が意味すること

**① 境界値 `amount <= 0` → `amount <= 1`**
金額 1 円の申請を試すテストが1つも無かった。カバレッジ上はこの行を通っている
（金額 0 の異常系テストがあるため）が、**境界の反対側を確かめていない**。
カバレッジでは原理的に検出できない種類の穴である。

**② 監査ログの操作者が note で上書きされる**
`_log(req, Action.REMAND, note)` は引数が1つずれ、`actor` に note の文字列が入る。
つまり **差し戻しの監査ログに、操作者ではなくコメント文字列が記録される**。
REQ-010（全状態遷移を時刻・操作者付きで記録）に対する明確な違反だが、
差し戻しの監査ログの `actor` を検証するテストが無かったため通過していた。

**③ 差し戻しの note が記録されない**
同じく `_log` の引数欠落。差し戻し理由が監査ログに残らない。

②③ は**内部統制の要件そのもの**に関わる。「カバレッジ 99% だから監査ログは検証できている」
とは言えないことが、具体例として示された。

---

## 4. 生存ミュータント → Property → PBT

本物の穴3件は、いずれも「個別の例では気づきにくいが、性質として書けば必ず破れる」種類だった。
そこで要求 Spec に Property（`PROP-nnn`）を追加し、Hypothesis で PBT に変換した。

| PROP | 性質 | 殺したミュータント |
|---|---|---|
| PROP-002 | 任意の金額 ≥ 1 と妥当な承認者について、起票は必ず成功し DRAFT になる | ① 境界値 |
| PROP-005 | 任意の操作について、監査ログ末尾の `actor` は操作を行った本人と一致する | ② 操作者 / ③ note |
| PROP-001 | 任意の2つの金額 a ≤ b について `levels(a) ≤ levels(b)`（単調非減少） | （既に killed） |
| PROP-003 | 起票が成功したなら、承認者リストに申請者は含まれない | （既に killed） |
| PROP-004 | 監査ログの件数は成功した状態遷移の回数と一致する | （既に killed） |
| PROP-006 | 順序どおりに全段承認すると必ず APPROVED になる | （既に killed） |

**PROP-002 が ① を殺す理由**: 金額を 1〜10,000,000 の範囲で生成するため、
Hypothesis は境界値 1 を必ず試す。例ベースのテストで境界を1つずつ書き足すのではなく、
**「範囲全体で成り立つ」と書くだけで境界が自動的に含まれる**。

**PROP-005 が ②③ を殺す理由**: 「監査ログ末尾の actor は操作者本人」という性質は、
差し戻し・却下・提出のすべてに同時に適用される。個別の例を書き漏らす余地がない。

---

## 5. 実測 ②：PBT 追加後

```
183 ミュータント: 171 killed / 12 survived
mutation score = 171 / 183 = 93.44%（+1.64pt）
```

追加した PBT は 8 件（テスト総数 37 → 45）。**狙った3件を正確に殺し、それ以外の
ミュータントの状態は変わっていない。**

### 残る 12 件について

すべてエラーメッセージ文字列（9件）と既定引数 `note`（3件）の変異である。
これらを殺すには「エラーメッセージの文言をテストで固定する」ことになるが、
J-SIX ではこれを**やらない方針**とした。理由は2つある。

1. 文言は仕様ではない。Design Spec が規定しているのは HTTP 409 / 404 であって
   メッセージ本文ではない。仕様が定めていない詳細をテストで固定すると、
   文言の改善のたびにテストが壊れる（脆いテスト）
2. hold-out 受入テストで実演したのと同じ問題である。仕様にない詳細を監督面に
   すると、**正しい実装まで落とす**

したがって **12件は意図的に生かしている**。mutation score 100% を目指すことは目的ではない。

---

## 6. 閾値をいくつにするか

J-SIX v2.1 は mutation score の**既定閾値を定めていない**。ハンドオフ時点の仮値（70）は
根拠がなかったため、Plugin の既定値としては採用しなかった（`min_score` 未指定なら計測のみ）。

本ケーススタディの実測に基づき、**この題材では 90%** を設定した
（`examples/approval-workflow/.jsix-checks.json`）。

| 判断 | 根拠 |
|---|---|
| 実測値 93.4% | 現状の到達点 |
| 閾値 90% | 実測から約3pt の余裕。等価に近いミュータント（メッセージ文言）が12件あり、リファクタリングでこの比率が変動しうるため |
| 70%（ハンドオフの仮値）を採らない | 実測値と23pt 離れており、ゲートとして機能しない |

**この 90% を他プロジェクトに一般化してはいけない。** N=1 かつ小規模（207 ステートメント）で
あり、ドメインの性質（純粋なステートマシン、外部依存なし）が mutation score を高く出やすくする。
自プロジェクトで数タスク計測してから決めること（`j-six:quality-metrics` Skill に手順がある）。

---

## 7. 実測値と推定値の切り分け

### 実測できたこと（再現可能）

| 指標 | 実測値 | 計測方法 |
|---|---|---|
| カバレッジ | **99%**（207 stmt 中 未到達 2） | `make test` |
| mutation score（PBT 前） | **91.80%**（168/183） | `make mutation` |
| mutation score（PBT 後） | **93.44%**（171/183） | `make mutation` |
| 生存ミュータント中の本物の穴 | **3 / 15 件** | 手作業で分類（§3） |
| PBT で殺せた本物の穴 | **3 / 3 件** | mutation 再実行で確認 |
| 追加した PBT | **8件**（テスト 37 → 45） | `tests/test_properties.py` |
| REQ / PROP トレーサビリティ | **16/16**（REQ 10 + PROP 6） | `make gate` |

### 実測できていないこと

| 主張 | 状態 |
|---|---|
| mutation score の閾値 90% が妥当 | **本題材でのみ実測**。他プロジェクトへの一般化は未検証（N=1・小規模・外部依存なし） |
| 「カバレッジと mutation score の差は一般に約7pt」 | **言えない**。本題材で 99% vs 91.8% だったというだけ |
| mutation testing の導入コスト（実行時間・運用負荷） | 本題材は 183 ミュータント / 約2分。**大規模での実行時間は未測定** |
| G2 に mutation を加えたことで欠陥が減ったか | **未実測**。本ケースは「テストの穴を検出した」ところまで |

---

## 8. 結論として言えること / 言えないこと

**言える**:

- **カバレッジ 99% でも mutation score は 91.8% にとどまり、本物のテストの穴が3件残っていた。**
  うち2件は内部統制要件（監査ログの操作者・理由）に関わるもので、実務上見逃せない
- **生存ミュータントは性質テストの出発点として質が高い。** 3件とも「例では気づきにくいが
  性質としては必ず破れる」形をしており、PROP 化 → PBT で正確に塞げた
- **mutation score 100% は目的ではない。** 仕様が規定していない詳細（エラーメッセージ文言）を
  固定するテストは、脆いテストを生む

**言えない**:

- 閾値 90% の一般性（N=1）
- 「カバレッジ + N pt」のような一般則
- 大規模プロジェクトでの実行時間と運用コスト
- 欠陥流出率が実際に下がるか（それを測るには本番運用のデータが要る）

---

## 9. 次のアクション

- [ ] 中規模題材（永続化・外部連携あり）での mutation score 実測。純粋なステートマシンでは
      高く出やすいという仮説の検証
- [ ] mutation testing の実行時間の測定と、`scope: changed`（変更ファイルに限定）による
      短縮効果の実測
- [ ] 複数タスクを回した後の `j-six:quality-metrics` によるプロセス健全性の集計
      （G3 judge 却下率、ゲート失敗理由の分布）

---

## 付録: 生存ミュータントの全リスト（PBT 追加後）

```
app.workflow.xǁWorkflowServiceǁcreate_request__mutmut_4   # エラーメッセージ文言
app.workflow.xǁWorkflowServiceǁcreate_request__mutmut_7   # エラーメッセージ文言
app.workflow.xǁWorkflowServiceǁcreate_request__mutmut_10  # エラーメッセージ文言
app.workflow.xǁWorkflowServiceǁcreate_request__mutmut_13  # エラーメッセージ文言
app.workflow.xǁWorkflowServiceǁsubmit__mutmut_6           # エラーメッセージ文言
app.workflow.xǁWorkflowServiceǁsubmit__mutmut_9           # エラーメッセージ文言
app.workflow.xǁWorkflowServiceǁreject__mutmut_1           # 既定引数 note
app.workflow.xǁWorkflowServiceǁremand__mutmut_1           # 既定引数 note
app.workflow.xǁWorkflowServiceǁremand__mutmut_6           # エラーメッセージを None に
app.workflow.xǁWorkflowServiceǁwithdraw__mutmut_6         # エラーメッセージ文言
app.workflow.xǁWorkflowServiceǁ_ensure_pending__mutmut_4  # エラーメッセージ文言
app.workflow.xǁWorkflowServiceǁ_log__mutmut_1             # 既定引数 note
```

生の計測結果は `examples/approval-workflow/reports/mutation.json`（`make mutation` で再生成）。
