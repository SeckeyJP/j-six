# 月次請求書発行 — J-SIX サンプルアプリ（画面・帳票・バッチ）

J-SIX の**第2サンプル**。[`examples/approval-workflow/`](../approval-workflow/) が
API のみで画面・帳票・バッチを持たないため、IPA の工程成果物27点のうち15点
（画面6・帳票5・バッチ4）の記入済み実例を作れない。その穴を埋めるための題材である。

| サンプル | 役割 |
|---|---|
| `approval-workflow` | 品質ゲート（G1〜G4）と mutation testing の実証。[ケーススタディ #1](../../docs/case-study-01.md) / [#2](../../docs/case-study-02.md) |
| **`monthly-billing`（本サンプル）** | **設計書テンプレート27点の記入済み実例**。画面・帳票・バッチ・外部IF を持つ |

## 題材

備品・経費の売上データから月次で請求書を発行する。日本の SI で最も頻出する業務の一つ。

**中心にあるのは消費税の端数処理**である。素朴な実装（明細ごとに丸めて合計）は
制度上認められないが、明細1件や端数の出ない入力では正しい実装と同じ結果になるため、
例ベースのテストをすり抜ける。

```
誤: Σ floor(明細金額 × 税率)      ← 明細ごとに丸める
正: floor(Σ 明細金額 × 税率)      ← 税率ごとに1回だけ丸める（ADR-0001）
```

根拠: [国税庁「インボイス制度に関するQ&A」問57](https://www.nta.go.jp/taxes/shiraberu/zeimokubetsu/shohi/keigenzeiritsu/pdf/qa/57.pdf)
—「一の適格請求書につき、税率ごとに1回の端数処理を行う」。

## 構成

```
monthly-billing/
├── CLAUDE.md                 # 記入済み CLAUDE.md 実例
├── app/
│   ├── models.py             # ドメインモデル（InvoiceLine は消費税額を持たない）
│   ├── billing.py            # 業務ルールの集約点（締め・税計算）
│   ├── importer.py           # EIF-002 売上取込
│   ├── accounting.py         # EIF-001 会計連携ファイル
│   ├── batch.py              # BATCH-001/002 のエントリポイント
│   ├── reports.py            # RPT-002 請求一覧表 / 表示用ビュー
│   ├── main.py               # 画面（SCR）と帳票（RPT）の HTTP 層
│   └── templates/            # 画面・帳票の Jinja2（設計書の逆生成元）
├── tests/
│   ├── test_billing.py       # ドメイン単体（REQ-nnn タグ付き）
│   ├── test_properties.py    # 性質テスト（PROP-nnn / Hypothesis）
│   ├── test_api.py           # 画面・帳票の結線
│   ├── test_importer.py / test_accounting.py / test_reports.py
│   └── acceptance/           # hold-out 受入テスト（UC 単位）
└── docs/
    ├── requirement-spec.md   # UC 6 / REQ 10 / PROP 6
    ├── design-spec.md        # PROP の実装方針・品質ゲート設定を含む
    ├── adr/                  # 0001 端数処理の単位 / 0002 方法 / 0003 帳票形式
    ├── traceability.md
    └── deliverables/         # ★ 工程成果物27点の記入済み実例
```

## ID 体系

| 接頭辞 | 対象 |
|---|---|
| `UC-nnn` | ユースケース |
| `REQ-nnn` | 業務ルール（トレーサビリティ・キー） |
| `PROP-nnn` | 性質（property-based testing で検証） |
| `SCR-nnn` | 画面 |
| `RPT-nnn` | 帳票 |
| `BATCH-nnn` | バッチ |
| `EIF-nnn` | 外部インタフェース |

## セットアップと実行

```bash
cd examples/monthly-billing
make setup                    # venv 作成 + 依存インストール
make setup-mutation           # mutation testing 用の venv（Python 3.10+ が必要）

make test                     # 単体・性質テスト
make test-acceptance          # hold-out 受入テスト
make mutation                 # mutation score 計測
make gate                     # 品質ゲート G1→G4

.venv/bin/python -m uvicorn app.main:app --reload
# → http://127.0.0.1:8000/invoices で請求一覧画面（SCR-001）
```

## 計測結果（2026-09-18 時点）

| 指標 | 実測値 |
|---|---|
| アプリ実装 | 321 ステートメント（app/） |
| テスト件数 | 93 件（例ベース + 性質）＋ hold-out 受入 19 件 |
| ステートメントカバレッジ | 98.8% |
| **mutation score** | **92.95%**（454 ミュータント中 422 killed） |
| トレーサビリティ | 16/16（REQ 10 + PROP 6） |

### mutation testing が見つけたテストの穴

初回計測は 87.89% で閾値（90%）に届かなかった。生存55件を分類すると**本物の穴が8種**あった。

| 生存ミュータント | 意味 |
|---|---|
| `period_of`: `month > 1` → `month >= 1` | 1月締め（前月が前年12月）が未検証 |
| `_find_invoice`: 再利用経路 | **再締めで請求番号が変わっても気づけない** |
| `accounting`: `continue` → `break` | 請求番号順で先頭が未確定だと、以降の確定済みが会計連携から丸ごと欠ける |
| `_next_invoice_no`: `+= 1` → `-= 1` | 採番の連番が未検証 |
| `line_no=i + 1` → `None` | 明細番号が未検証（帳票に出る） |
| CSV の `lineterminator` | 改行コードが環境依存になる |

例ベース14件と性質2件を追加して **92.95%** へ。残る32件はエラーメッセージ文言と
表示用ビューの変異が中心で、外部から見た振る舞いを変えないため意図的に生かしている
（[ケーススタディ #2](../../docs/case-study-02.md) と同じ方針）。

## 業務フロー

```
販売管理システム ──EIF-002──▶ 売上取込（UC-001）
                                    │
                            BATCH-001 月次締め（UC-002）
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
            SCR-001/002/003    RPT-001/002    確定（UC-006）
            請求一覧・明細      請求書・一覧表        │
                                            BATCH-002 会計連携
                                                    │
                                              EIF-001 会計システム
```

## 設計書（工程成果物）の記入済み実例

[`docs/deliverables/`](docs/deliverables/) に IPA「機能要件の合意形成ガイド」が想定する
**工程成果物27点**の記入済み実例を置いている。

| 領域 | 点数 | うちコード／テストから逆生成 |
|---|---|---|
| システム振舞い | 4 | 1（システム化業務説明 ← hold-out 受入テスト） |
| 画面 | 6 | 5 |
| データモデル | 4 | 4 |
| 外部インタフェース | 4 | 3 |
| バッチ | 4 | 3 |
| 帳票 | 5 | 3 |
| **合計** | **27** | **17** |

27点中17点が実物から起こせる。**人手更新が必要なのは「なぜ作るか」「どう運用するか」を
記す7点に限られる**（残り3点はコードと Spec の併用）。

空のテンプレートは `templates/deliverables/` を参照。
