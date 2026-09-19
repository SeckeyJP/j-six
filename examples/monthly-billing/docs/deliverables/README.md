# 工程成果物（記入済み実例）— 月次請求書発行

IPA「[機能要件の合意形成ガイド](https://www.ipa.go.jp/archive/files/000004517.pdf)」が想定する
**工程成果物27点**を、本サンプルの実物から起こした記入済み実例。
空のテンプレートは [`templates/deliverables/`](../../../../templates/deliverables/) を参照。

## この単位で作る理由

IPA 自身が、外部設計工程には業界標準の工程成果物が存在しないこと、および
**工程成果物と設計書は1対1ではない**ことを明記している。

> 外部設計工程には、現時点では業界として標準とされる「工程成果物」が存在しません。
> …設計書の作成単位や構成が、本ガイドで想定している「工程成果物」と一致しないことがあります。
> 例えば、画面編では、「工程成果物」として「画面レイアウト」、「画面入出力項目一覧」、
> 「画面アクション明細」などを想定していますが、実際のプロジェクトでは、これらを合わせて
> １つの「ユーザインタフェース設計書」として作成する場合があります。
> — 同ガイド 概要編 2.1

したがって「基本設計書」のような大きな単位ではなく**工程成果物の粒度**で作り、
顧客の様式に応じて束ねる。束ね方は [`templates/deliverables/assembly/`](../../../../templates/deliverables/assembly/GUIDE.md) に定義する。
本サンプルを基本設計書・詳細設計書に束ねた場合の対応は、各組立例の「組立結果: monthly-billing」を参照。

## 27成果物の索引と由来

**由来**が J-SIX の主張の核心である。コードやテストから逆生成できるものは設計書⇔コードの
乖離が原理的に起こらない。人手更新のものは乖離リスクが残るため、その旨を明示する。

### システム振舞い（4点）

| # | 工程成果物 | 由来 | 逆生成元 |
|---|---|---|---|
| 1 | [システム化業務一覧](behavior/01-system-function-list.md) | Spec（人手） | 要求 Spec 3.1 ユースケース一覧 |
| 2 | [システム化業務フロー](behavior/02-business-flow.md) | Spec（人手） | 要求 Spec 1.1 / 2.1 |
| 3 | [システム化業務説明](behavior/03-business-description.md) | **受入テストから逆生成** | `tests/acceptance/`（通っているテストが根拠） |
| 4 | [システム振舞い共通ルール](behavior/04-common-rules.md) | CLAUDE.md（人手） | CLAUDE.md, ADR |

### 画面（6点）

| # | 工程成果物 | 由来 | 逆生成元 |
|---|---|---|---|
| 5 | [画面一覧](screen/01-screen-list.md) | **コードから逆生成** | `app/main.py` のルート定義 |
| 6 | [画面遷移](screen/02-screen-transition.md) | **コードから逆生成** | テンプレートの `<a href>` / `<form action>` |
| 7 | [画面レイアウト](screen/03-screen-layout.md) | **コードから逆生成** | `app/templates/*.html` |
| 8 | [画面入出力項目一覧](screen/04-screen-io-items.md) | **コードから逆生成** | テンプレートの変数と `reports.invoice_view` |
| 9 | [画面アクション明細](screen/05-screen-actions.md) | **コードから逆生成** | `app/main.py` の POST ハンドラ |
| 10 | [画面遷移・レイアウト共通ルール](screen/06-common-rules.md) | CLAUDE.md（人手） | `app/templates/_base.html`, CLAUDE.md |

### データモデル（4点）

| # | 工程成果物 | 由来 | 逆生成元 |
|---|---|---|---|
| 11 | [ER図](data/01-er-diagram.md) | **コードから逆生成** | `app/models.py` |
| 12 | [エンティティ一覧](data/02-entity-list.md) | **コードから逆生成** | 同上 |
| 13 | [エンティティ定義](data/03-entity-definition.md) | **コードから逆生成** | 同上（型・制約） |
| 14 | [CRUD図](data/04-crud-matrix.md) | **コードから逆生成** | `app/billing.py` のアクセス解析 |

### 外部インタフェース（4点）

| # | 工程成果物 | 由来 | 逆生成元 |
|---|---|---|---|
| 15 | [外部システム関連図](external-if/01-system-relation.md) | **コードから逆生成** | `app/importer.py`, `app/accounting.py` |
| 16 | [外部インタフェース一覧](external-if/02-interface-list.md) | **コードから逆生成** | 同上 |
| 17 | [外部インタフェース項目説明](external-if/03-interface-items.md) | **コードから逆生成** | `COLUMNS`, `HEADER` 定数 |
| 18 | [外部インタフェース処理説明](external-if/04-interface-process.md) | コード＋Spec | `importer.import_sales`, `accounting.build_accounting_csv` |

### バッチ（4点）

| # | 工程成果物 | 由来 | 逆生成元 |
|---|---|---|---|
| 19 | [バッチ処理一覧](batch/01-batch-list.md) | **コードから逆生成** | `app/batch.py` |
| 20 | [バッチ処理フロー](batch/02-batch-flow.md) | **コードから逆生成** | 同上 |
| 21 | [バッチ処理定義](batch/03-batch-definition.md) | **コードから逆生成** | 同上＋`app/billing.py` |
| 22 | [バッチ処理共通ルール](batch/04-common-rules.md) | CLAUDE.md（人手） | CLAUDE.md, ADR |

### 帳票（5点）

| # | 工程成果物 | 由来 | 逆生成元 |
|---|---|---|---|
| 23 | [帳票一覧](report/01-report-list.md) | **コードから逆生成** | `app/main.py`, `app/reports.py` |
| 24 | [帳票概要](report/02-report-overview.md) | コード＋Spec | 同上 |
| 25 | [帳票レイアウト](report/03-report-layout.md) | **コードから逆生成** | `app/templates/report_invoice.html` |
| 26 | [帳票項目説明](report/04-report-items.md) | **コードから逆生成** | 同上＋`reports.invoice_view` |
| 27 | [帳票編集定義](report/05-report-edit-rules.md) | コード＋ADR | テンプレートの条件分岐、ADR-0001/0002 |

## 由来の内訳

| 由来 | 件数 | 乖離リスク |
|---|---|---|
| コードから逆生成 | 18 | **原理的にゼロ** |
| 受入テストから逆生成 | 1 | **ゼロ**（通っているテストが根拠） |
| コード＋Spec／ADR の併用 | 3 | 一部残る |
| Spec / CLAUDE.md（人手） | 5 | 残る |

27点中19点が実物から自動で起こせる。**人手更新が必要なのは「なぜ作るか」「どう運用するか」を
記す5点に限られる**。これが J-SIX の3層ドキュメント戦略の主張そのものである。

## 合意成熟度

IPA ガイドは合意形成を3段階に分けている（同ガイド 3.1.1）。

| レベル | 定義 |
|---|---|
| 仕掛レベル | 発注者が「言い切った」、開発者が「聞き切った」 |
| 充実レベル | 図表に書いてレビューを繰り返し、合意内容が充実する |
| 完成レベル | 合意内容が管理され、双方が確認できた |

本実例は実装済み・テスト通過済みの状態から起こした **Phase 6 時点の版**であり、内容は実装と
一致している。ただしサンプルのため顧客による確認は行っておらず、完成レベルの条件のうち
「双方が確認できた」は満たしていない。成果物ごとの到達基準は
[`templates/deliverables/README.md`](../../../../templates/deliverables/README.md) の「合意成熟度」を参照。

## 出典について

IPA「機能要件の合意形成ガイド ver.1.0」（2010年3月31日）に基づく。同ガイドは
発注者ビューガイドライン ver.1.0 の改訂版であり、現在は IPA のアーカイブに置かれている。
**項目名と構造を参照した独自のテンプレート**であり、ガイドの様式を引き写したものではない。
