---
name: doc-reverse-gen
description: J-SIX Phase 6 の設計書逆生成。実装済みコードと受入テストから IPA の工程成果物（27点）を領域単位で逆生成し、組立定義に従って顧客様式の設計書（基本設計書・詳細設計書など）に束ねる。証跡パッケージから品質・テスト系の納品物も作る。3層ドキュメント戦略の第3層を担当。
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
argument-hint: "[種別: behavior|screen|data|external-if|batch|report|deliverables|assemble <組立定義>|quality|all] [対象パス]"
---

# 設計書逆生成スキル

J-SIX プロセスの Phase 6（ドキュメント生成）で、実装済みコードから設計書を逆生成する。
3層ドキュメント戦略の第3層「逆生成設計書（What/How）」を担当する。

## 概要

設計書は2段階で作る。

```
コード / 受入テスト / Spec / ADR
    ↓ ① 逆生成（種別: behavior〜report, deliverables）
工程成果物27点（docs/deliverables/）              ← 正
    ↓ ② 組立（種別: assemble）
顧客様式の設計書（docs/design-docs/）             ← ビュー。直接編集しない
```

**「基本設計書」を直接生成しない。**工程成果物と設計書は1対1ではなく、顧客ごとに目次が違う
（IPA 機能要件の合意形成ガイド 概要編 2.1）。まず工程成果物の粒度で逆生成し、顧客と合意した
組立定義に従って束ねる。こうすると顧客様式が変わっても逆生成をやり直さずに済み、
設計書を直接直して工程成果物と食い違う事故も起きない。

## 引数

- **種別**（第1引数）

  | 種別 | 生成物 | 出力先 |
  |---|---|---|
  | `behavior` | システム振舞い（4点） | `docs/deliverables/behavior/` |
  | `screen` | 画面（6点） | `docs/deliverables/screen/` |
  | `data` | データモデル（4点） | `docs/deliverables/data/` |
  | `external-if` | 外部インタフェース（4点）。他システムに提供する API もここに含める | `docs/deliverables/external-if/` |
  | `batch` | バッチ（4点） | `docs/deliverables/batch/` |
  | `report` | 帳票（5点） | `docs/deliverables/report/` |
  | `deliverables` | 上記6領域すべて。対象システムが持たない領域は「該当なし」を記録する | `docs/deliverables/` |
  | `assemble <組立定義>` | 組立定義に従って工程成果物を束ねた設計書 | `docs/design-docs/<設計書名>.md` |
  | `quality` | 品質・テスト系の納品物（証跡パッケージから変換） | `docs/design-docs/` |
  | `all` | `deliverables` → プロジェクトの全組立定義で `assemble` → `quality` | 上記すべて |

- **対象パス**（第2引数、省略可）: 解析対象のディレクトリまたはファイル。省略時はプロジェクト全体

### v2.0 の種別からの移行

v2.0 の種別は引き続き受け付け、次のように読み替える。読み替えたことを出力の冒頭で1行知らせる。

| v2.0 の種別 | 読み替え |
|---|---|
| `basic` | `deliverables` → `assemble kihon-sekkei` |
| `detail` | `assemble shousai-sekkei`（必要な工程成果物が無ければ先に逆生成する） |
| `if` | `external-if`（API エンドポイントは外部インタフェースとして扱う） |
| `db` | `data` |

## 雛形と記入済み実例

次のファイルを雛形・手本として読む。テンプレートは本 Skill に同梱している
（`${CLAUDE_SKILL_DIR}/templates/deliverables/`）。

**Glob や Grep で同梱ディレクトリを探さず、下のリンクのファイルを Read で直接読むこと。**
**テンプレートを読めない場合は、テンプレートなしで逆生成せず、作業を止めてその旨を報告する。**
テンプレートを読まずに書くと、ファイル名・節構成・由来の表示が J-SIX の工程成果物と
一致しない成果物になる（ヘッドレス実行で権限が足りず、独自の形式で書いた例がある）。

| 領域 | 同梱テンプレート（Read で読む） |
|---|---|
| 索引 | [README.md](templates/deliverables/README.md) — 27点の索引・由来・作る順序 |
| システム振舞い（`behavior/`） | [01-system-function-list.md](templates/deliverables/behavior/01-system-function-list.md) / [02-business-flow.md](templates/deliverables/behavior/02-business-flow.md) / [03-business-description.md](templates/deliverables/behavior/03-business-description.md) / [04-common-rules.md](templates/deliverables/behavior/04-common-rules.md) |
| 画面（`screen/`） | [01-screen-list.md](templates/deliverables/screen/01-screen-list.md) / [02-screen-transition.md](templates/deliverables/screen/02-screen-transition.md) / [03-screen-layout.md](templates/deliverables/screen/03-screen-layout.md) / [04-screen-io-items.md](templates/deliverables/screen/04-screen-io-items.md) / [05-screen-actions.md](templates/deliverables/screen/05-screen-actions.md) / [06-common-rules.md](templates/deliverables/screen/06-common-rules.md) |
| データモデル（`data/`） | [01-er-diagram.md](templates/deliverables/data/01-er-diagram.md) / [02-entity-list.md](templates/deliverables/data/02-entity-list.md) / [03-entity-definition.md](templates/deliverables/data/03-entity-definition.md) / [04-crud-matrix.md](templates/deliverables/data/04-crud-matrix.md) |
| 外部インタフェース（`external-if/`） | [01-system-relation.md](templates/deliverables/external-if/01-system-relation.md) / [02-interface-list.md](templates/deliverables/external-if/02-interface-list.md) / [03-interface-items.md](templates/deliverables/external-if/03-interface-items.md) / [04-interface-process.md](templates/deliverables/external-if/04-interface-process.md) |
| バッチ（`batch/`） | [01-batch-list.md](templates/deliverables/batch/01-batch-list.md) / [02-batch-flow.md](templates/deliverables/batch/02-batch-flow.md) / [03-batch-definition.md](templates/deliverables/batch/03-batch-definition.md) / [04-common-rules.md](templates/deliverables/batch/04-common-rules.md) |
| 帳票（`report/`） | [01-report-list.md](templates/deliverables/report/01-report-list.md) / [02-report-overview.md](templates/deliverables/report/02-report-overview.md) / [03-report-layout.md](templates/deliverables/report/03-report-layout.md) / [04-report-items.md](templates/deliverables/report/04-report-items.md) / [05-report-edit-rules.md](templates/deliverables/report/05-report-edit-rules.md) |
| 組立（`assembly/`） | [GUIDE.md](templates/deliverables/assembly/GUIDE.md) / [kihon-sekkei.md](templates/deliverables/assembly/kihon-sekkei.md) / [shousai-sekkei.md](templates/deliverables/assembly/shousai-sekkei.md) |

記入済み実例は https://github.com/SeckeyJP/j-six/tree/main/examples/monthly-billing/docs/deliverables
（Plugin には同梱していない）。成果物のファイル名はテンプレートと同じにする（例: `data/03-entity-definition.md`）。

各テンプレート末尾の「記入ガイド」に、その成果物の**逆生成の手順と書き落としやすい点**が書いてある。
逆生成の前に必ず読む。

## 共通: コードベース解析

1. プロジェクト構造を把握する（ディレクトリ構成、主要ファイル）
2. 技術スタックを特定する（言語、フレームワーク、DB、外部連携）
3. 既存の Spec（`docs/specs/`）、ADR（`docs/adr/`）、CLAUDE.md を読む
4. **対象システムが持つ領域を判定する**（画面・帳票・バッチ・外部 IF の有無）。持たない領域は
   逆生成せず「該当なし」を記録する（`docs/deliverables/README.md` の索引に理由付きで書く）

## 種別 behavior〜report: 工程成果物の逆生成

### 由来ごとの扱い

27点は由来が4種類ある（同梱の `templates/deliverables/README.md` の索引）。**由来によって
このスキルがしてよいことが違う。**

| 由来 | 件数 | このスキルの扱い |
|---|---|---|
| コードから逆生成 | 18 | 逆生成元のコードから機械的に写す。推測で補わない |
| 受入テストから逆生成 | 1（③ システム化業務説明） | `tests/acceptance/` の各テストから、fixture → 事前条件、操作列 → 基本シナリオ、アサーション → 事後条件を写す。**通っているテストだけ**を根拠にする |
| コード＋Spec／ADR の併用 | 3（⑱ ㉔ ㉗） | コード由来の部分を逆生成し、Spec・ADR 由来の部分は引用元を明示して転記する |
| Spec / CLAUDE.md（人手） | 5（① ② ④ ⑩ ㉒） | **生成しない。**Phase 1-2 で人が書いたものが既にあるはずなので、存在と最新性を確認するだけにする。無い場合は Spec・CLAUDE.md からドラフトを作り、冒頭に「ドラフト（人手の確認が必要）」と書く |

### 手順

1. 対象領域のテンプレートを `docs/deliverables/<領域>/` にコピーする
2. 各ファイル冒頭の**由来・逆生成元・対象・版・日付**を埋める。逆生成元には実際に読んだ
   ファイルと関数・定数の名前を書く
3. テンプレートの「記入ガイド」の手順に従って `[TODO: ...]` を埋める
4. ID（`SCR-nnn` / `RPT-nnn` / `EIF-nnn` / `BATCH-nnn` / `REQ-nnn` / `PROP-nnn` など）は
   コード・テスト・Spec にあるものをそのまま使う。新たに採番しない
5. 「記入ガイド（記入後は削除する）」の節を削除する
6. 非自明な設計判断（入力形式・端数処理・スキップと打ち切りの違いなど）は、根拠となる
   ADR・品質ゲートの検出結果を成果物の中に残す

## 種別 assemble: 設計書の組立

`${CLAUDE_SKILL_DIR}/templates/deliverables/assembly/GUIDE.md` の手順に従う。要点は次のとおり。

1. **組立定義を探す。**`docs/design-docs/assembly-<設計書名>.md` を優先し、無ければ
   同梱の `${CLAUDE_SKILL_DIR}/templates/deliverables/assembly/<設計書名>.md`（`kihon-sekkei` / `shousai-sekkei`）を使う。
   プロジェクトの組立定義が無いまま雛形を使った場合は、その旨を出力の冒頭に書く
   （顧客と目次を合意していない設計書である）
2. 組立定義の章の順に構成要素を連結する。**構成要素の本文を書き換えない**（要約・言い換えを
   しない）。見出しレベルだけを章構成に合わせて調整する
3. 章ごとに由来を表示する（例: `> 由来: コードから逆生成（app/main.py）`）
4. 構成要素が無い章は「該当なし（理由）」と書く。章を消さない
5. 同じ工程成果物を2冊に全文で入れない。2冊目では参照だけにする
6. 巻末に構成要素の版表（工程成果物ごとの版・日付・逆生成元のコミット）を付ける
7. GUIDE 5「組立後の検査」を実施し、結果を出力に含める

**組み立てた設計書は直接編集しない。**修正依頼を受けたら、該当する工程成果物（さらにその
逆生成元）を直してから組み立て直す。

## 出力ルール（全種別共通）

1. **Spec・ADR からの引用**: 引用元を `> 出典: docs/specs/[ファイル名]#[セクション]` / `> ADR-NNNN: [タイトル]` で明示する
2. **コードからの抽出**: 逆生成元のファイルパス（と関数・定数名）を成果物の冒頭に書く
3. **図**: Mermaid 記法を使う。ノードラベルは引用符で囲む（`[TODO: ...]` のような入れ子括弧はパースが落ちる）
4. **不明・未実装の箇所**: `[要確認]` / `[TODO: 未実装]` で明示し、隠さない。推測で補完しない
5. **Excel / Word が必要な場合**: 組み立てた Markdown を変換して `docs/design-docs/export/` に出力する。
   表構造と由来の表示を落とさない。変換物も直接編集しない（1段目の原則と同じ）

## 種別 `quality`: 証跡パッケージから品質・テスト系の納品物を生成（v2.1）

従来 V字モデルで人手作成していた品質・テスト系の納品物は、**Phase 4 でタスクごとに
自動生成された証跡**（`reports/evidence/<タスクID>/`）を変換して作る。
「納品直前に人手で書き起こす」のではなく「実行時の実データを整形する」ため、
コードとの乖離が原理的に発生しない。

### 対応表

| 従来納品物 | 元データ | 生成物 |
|---|---|---|
| 単体テスト仕様書・テスト結果報告書 | `01_traceability.md`, `02_test_results.md` | `docs/design-docs/test-report.md` |
| 品質報告書（品質メトリクス） | `03_coverage_mutation.md`, `05_scope_and_integrity.md` ＋ `quality-metrics` の集計 | `docs/design-docs/quality-report.md` |
| セキュリティ診断結果 | `04_security.md` | `docs/design-docs/security-report.md` |
| トレーサビリティマトリクス | `01_traceability.md` | `docs/design-docs/traceability-matrix.md` |
| レビュー記録 | `06_judge_advisory.md`（参考所見）, `07_approval.md`（承認） | `docs/design-docs/review-record.md` |

### 変換時の必須ルール

証跡パッケージの **3区分（証跡 / 参考所見 / 承認）を納品物でも保つこと。**
区分が混ざると、決定論的に検証された事実と AI の所見が同じ重みで読まれてしまう。

1. **数値は証跡から引用する。** 再計算・推定をしない。証跡に無い数値は書かない
2. **参考所見（`06` と `00` の要約節）を証跡と同じ節に置かない。** 別節にし、
   「AI による参考所見。単独で品質判定の根拠にしない」の注記を残す
3. **レビュー記録には人間の承認（`07`）を必ず含める。** `07` が未記入なら
   「未承認」と明記し、記入済みであるかのように書かない
4. **再現情報を添付する。** `env.json` の commit SHA・ツール名と版・実行日時・
   設定ハッシュを、各納品物の末尾に「検証条件」として載せる
5. 複数タスクをまとめる場合は、タスクIDごとに行を分け、どの証跡由来かを追える形にする

### Excel / Word 出力

従来フォーマットが必要な場合は、上記 Markdown を変換して
`docs/design-docs/export/` に出力する。表構造をそのまま保ち、
**区分の見出し（証跡 / 参考所見 / 承認）を落とさないこと。**

---

## 品質チェック

生成後に以下を自己検証:
- [ ] コードに存在する画面・帳票・バッチ・外部 IF・エンティティが工程成果物に漏れなく記載されているか
- [ ] 工程成果物に記載された内容がコードと一致しているか（逆生成元を実際に読んだか）
- [ ] 各成果物の冒頭に由来と逆生成元が書かれているか
- [ ] ③ システム化業務説明が、通っている受入テストだけを根拠にしているか
- [ ] 人手由来の5点を上書きしていないか（ドラフトを作った場合は「ドラフト」と明記したか）
- [ ] 対象システムが持たない領域が「該当なし（理由）」として記録されているか
- [ ] ID がコード・テスト・Spec と同じか（新たに採番していないか）
- [ ] 「記入ガイド」の節が削除されているか
- [ ] Mermaid 図の構文が正しいか
- [ ] （`assemble`）構成要素の本文を書き換えていないか。章ごとに由来が表示されているか
- [ ] （`assemble`）GUIDE 5「組立後の検査」の全項目を満たすか
- [ ] （`quality`）数値がすべて証跡由来で、推定値が混ざっていないか
- [ ] （`quality`）証跡 / 参考所見 / 承認 の区分が保たれているか
- [ ] （`quality`）検証条件（commit SHA・ツール版・実行日時）が記載されているか
