<!-- 自動生成: tools/sync_plugin_templates.py が templates/deliverables/assembly/shousai-sekkei.md から生成。直接編集せず、正のファイルを直して再生成すること -->
# 組立例: 詳細設計書

**設計書**: 詳細設計書（内部設計） ／ **構成要素**: コード・テスト・PROP・ADR からの逆生成が中心
**組立の原則と手順**: [`GUIDE.md`](GUIDE.md)

> 顧客に様式が無い場合の**出発点**となる目次。顧客に様式がある場合は、その目次の章ごとに
> 下表の構成要素を対応付け直す（GUIDE 4）。

---

## 0. 基本設計書との違い

IPA の工程成果物27点は**外部設計工程**の成果物であり、内部設計（モジュール構成・処理の
実装方式）は対象に含まれていない（[IPA 機能要件の合意形成ガイド](https://www.ipa.go.jp/archive/files/000004517.pdf)
概要編 2.1）。したがって詳細設計書の章立ては IPA ガイドに拠らない。**以下の目次は J-SIX の
方針（著者見解）として定めたものである。**

J-SIX では詳細設計書を**実装前に書かない**。詳細設計工程に相当する Phase 3 の成果物は
タスク一覧（受入条件・PROP・変更許可ファイル範囲）であり、詳細設計書は Phase 6 に
コード・テスト・ADR から逆生成する。

| 時期 | 顧客に出すもの |
|---|---|
| 実装前 | Phase 3 のタスク一覧（受入条件・PROP・変更許可範囲付き）。**詳細設計書の代替として合意する** |
| 納品 | 本書（Phase 6 に逆生成） |

実装前に関数単位の処理を日本語で書くと、実装後にコードと二重管理になる。GUIDE 4 の分類で
いえば (b)「J-SIX では作らない」にあたり、作らない理由と代替物（タスク一覧）を顧客と合意する。

---

## 1. 何を書き、何を書かないか

詳細設計書の価値は、**コードを読んでもすぐには分からないこと**にある。コードを1行ずつ
日本語に置き換えた処理記述は、コードより読みにくく、コードと食い違う機会を増やすだけである。

| 書く | 書かない |
|---|---|
| モジュールの責務と依存の向き | 関数本体を日本語に置き換えた処理記述 |
| 不変条件（PROP）と、それをどこで守っているか | 変数ごとの説明 |
| 例外と外部への応答の対応（例: 業務エラー → HTTP 409） | コードに書かれた条件分岐の列挙 |
| 状態遷移と、遷移を許す／拒む箇所 | 自明な getter / setter |
| 計算方式と**その根拠**（ADR・法令） | 型注釈から読める引数と戻り値の一覧だけの表 |

---

## 2. 目次と構成要素

| 章 | 構成要素 | 由来 |
|---|---|---|
| **1. モジュール構成** | | |
| 1.1 モジュール一覧と責務 | コード（パッケージ・モジュール構成）＋ Design Spec のアーキテクチャ概要 | コード＋Spec |
| 1.2 依存関係 | コード（import の静的解析）。Mermaid 図 | コードから逆生成 |
| **2. モジュール詳細** | | |
| 2.1 公開インタフェース | コード（公開関数・クラスのシグネチャと docstring） | コードから逆生成 |
| 2.2 不変条件 | 要求 Spec の PROP ＋ 性質テスト（`test_prop_*`） | 受入条件＋テスト |
| 2.3 状態遷移 | コード（状態の列挙型と、遷移を行う・拒否するメソッド） | コードから逆生成 |
| **3. 業務ロジック** | | |
| 3.1 計算方式 | コード ＋ 該当 ADR | コード＋ADR |
| 3.2 採番・一意性 | コード ＋ PROP | コード＋Spec |
| **4. エラー処理** | | |
| 4.1 例外の種類と発生条件 | コード（例外クラスと raise 箇所） | コードから逆生成 |
| 4.2 外部への応答 | コード（例外 → HTTP ステータス・終了コードの変換箇所） | コードから逆生成 |
| **5. 外部仕様の詳細** | 基本設計書に置かなかった項目レベルの工程成果物（[基本設計書 2](kihon-sekkei.md#2-変種-項目レベルを詳細設計書に回す)）。**基本設計書に置いた場合は参照だけにする**（GUIDE 1.5） | 工程成果物に従う |
| **6. 物理データ設計** | DDL・マイグレーション・インデックス定義。⑬ エンティティ定義の物理版 | コードから逆生成 |
| **7. 単体テスト** | | |
| 7.1 テスト観点 | テストコード（テストクラス・関数名、PROP との対応） | コードから逆生成 |
| 7.2 テスト結果 | 証跡パッケージ `01_traceability.md` / `02_test_results.md` / `03_coverage_mutation.md` | 決定論的な実行結果 |
| **8. 設計判断** | 実装段階で追加された ADR | 人手 |

7.2 は `doc-reverse-gen` Skill の `quality` 種別で作る（GUIDE 6）。数値は証跡から引用し、
再計算しない。

---

## 3. 組立結果: monthly-billing

記入済み実例 [`examples/monthly-billing/`](https://github.com/SeckeyJP/j-six/tree/main/examples/monthly-billing) で、各章が
どのコード・テストから起こされるかを示す。

| 章 | 逆生成元（実物） | 書く内容の例 |
|---|---|---|
| 1.1 | `app/` の7モジュール ＋ [Design Spec](https://github.com/SeckeyJP/j-six/blob/main/examples/monthly-billing/docs/design-spec.md) 1.1 | 業務ルールを `billing.py` に集約する（Design Spec 1.1）。帳票・会計連携の生成関数は計算済みの `Invoice` を受け取るだけで、ルールを再実装しない |
| 1.2 | 各モジュールの import | 入口（`main` / `batch` / `importer`）→ `billing` → `models`。出力（`reports` / `accounting`）は `models` だけに依存し、`billing` を呼ばない |
| 2.1 | `BillingService` の公開メソッド（`close_month` / `confirm` / `get_invoice` など） | 呼び出し元と、各メソッドが守る事前条件 |
| 2.2 | 要求 Spec 3.3 の PROP-001〜006 ＋ `tests/test_properties.py` | PROP-005「請求は取引先ごとに高々1件」を `_find_invoice` の再利用で守っている |
| 2.3 | `models.InvoiceStatus`、`BillingService.confirm` / `_ensure_not_confirmed` | 確定は不可逆。確定済みの月は再締めを拒否（REQ-007） |
| 3.1 | `billing.calc_tax` / `summarize_tax` ＋ [ADR-0001・0002](https://github.com/SeckeyJP/j-six/tree/main/examples/monthly-billing/docs/adr) | 税率ごとに1回だけ切り捨てる。単位は法令、方法は運用方針（ADR を分けた理由を含めて書く） |
| 3.2 | `BillingService._next_invoice_no` / `_find_invoice` | 再締めで請求番号が変わらないこと（mutation testing が未検証を検出した箇所） |
| 4.1 | `billing.BillingError` の raise 箇所 | 締め日・支払サイト・税率区分の不正、未登録の取引先、存在しない請求、確定済みの月の再締め、確定済みの再確定 |
| 4.2 | `app/main.py` の `HTTPException` 変換 | 存在しない請求 → 404、確定済みへの操作 → 409 |
| 5 | 該当なし（基本設計書に27点すべてを収めているため） | — |
| 6 | 該当なし（インメモリ実装。Design Spec 1.3 の判断） | 永続化へ差し替える場合に本章を起こす |
| 7.1 | `tests/test_*.py`（例ベース）、`tests/test_properties.py`（性質） | テストクラスと REQ / PROP の対応。[トレーサビリティマトリクス](https://github.com/SeckeyJP/j-six/blob/main/examples/monthly-billing/docs/traceability.md)と同じ ID を使う |
| 7.2 | `reports/evidence/<タスクID>/` | カバレッジ・mutation score・生存ミュータントの扱い |
| 8 | [ADR-0004](https://github.com/SeckeyJP/j-six/blob/main/examples/monthly-billing/docs/adr/0004-no-python-multipart.md) | CI の依存脆弱性スキャンを受けて form の解析から python-multipart を外した判断。Phase 2 の ADR（0001〜0003）と違い、実装段階で追加されたもの |

### この例で目立つ点

**3.2 は mutation testing が穴を見つけた箇所である。**`_build_invoice` の
`existing = None`（既存の請求を見つけても使わない）という変異が当初生き残っており、テストを追加して塞いだ。
詳細設計書にこの経緯を書く価値は、コードからは「再利用している」ことしか読めず、
**なぜ再利用が必須か**（先に通知した番号と食い違うため）が読めない点にある。

**5・6 章が「該当なし」になる。**章を消さず理由を書く（GUIDE 1.4）。とくに 6 章は、
サンプルがインメモリであることを知らない読み手には「物理設計が抜けている」ように見える。
