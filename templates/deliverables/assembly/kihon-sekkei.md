# 組立例: 基本設計書

**設計書**: 基本設計書（外部設計） ／ **構成要素**: 工程成果物27点すべて ＋ Spec ＋ ADR
**組立の原則と手順**: [`GUIDE.md`](GUIDE.md)

> 顧客に様式が無い場合の**出発点**となる目次。顧客に様式がある場合は、その目次の章ごとに
> 下表の構成要素を対応付け直す（GUIDE 4）。この目次が業界標準というわけではない。

IPA の工程成果物27点は外部設計工程の成果物として定義されている。本例では、外部設計に相当する
基本設計書に**27点すべて**を収め、内部の実装構造は[詳細設計書](shousai-sekkei.md)に分ける。

---

## 1. 目次と構成要素

**事前提出**の列は、Phase 2 の設計レビュー（コードが存在しない時点）で出せるものを示す
（GUIDE 3）。「代替」は、納品時に逆生成版へ差し替える章である。

| 章 | 構成要素 | 由来 | 事前提出 |
|---|---|---|---|
| **1. システム概要** | | | |
| 1.1 目的・業務背景 | 要求 Spec 1 業務背景 | 人手 | ○ |
| 1.2 対象範囲・対象外 | 要求 Spec 2 スコープ | 人手 | ○ |
| 1.3 制約・前提 | 要求 Spec 4 制約条件 / 5 前提条件 | 人手 | ○ |
| **2. システム構成** | | | |
| 2.1 アーキテクチャ | Design Spec 1 アーキテクチャ概要 | 人手 | ○ |
| 2.2 外部システム関連 | ⑮ [外部システム関連図](../external-if/01-system-relation.md) | コードから逆生成 | 代替: Design Spec の外部 IF 連携先一覧 |
| **3. 業務機能** | | | |
| 3.1 システム化業務一覧 | ① [システム化業務一覧](../behavior/01-system-function-list.md) | 人手 | ○ |
| 3.2 システム化業務フロー | ② [システム化業務フロー](../behavior/02-business-flow.md) | 人手 | ○ |
| 3.3 システム化業務説明 | ③ [システム化業務説明](../behavior/03-business-description.md) | 受入テストから逆生成 | 代替: 要求 Spec の受入条件（3.3）と hold-out 対象（3.4） |
| 3.4 業務ルール | 要求 Spec 3.2 業務ルール（REQ）、3.3 Property（PROP） | 人手 | ○ |
| 3.5 共通ルール | ④ [システム振舞い共通ルール](../behavior/04-common-rules.md) | 人手 | ○ |
| **4. 画面** | | | |
| 4.1 画面一覧 | ⑤ [画面一覧](../screen/01-screen-list.md) | コードから逆生成 | 代替: Design Spec の主要画面一覧 |
| 4.2 画面遷移 | ⑥ [画面遷移](../screen/02-screen-transition.md) | コードから逆生成 | 代替: Design Spec の画面遷移 |
| 4.3 画面レイアウト | ⑦ [画面レイアウト](../screen/03-screen-layout.md) | コードから逆生成 | 代替: **実動プロトタイプ**の画面 |
| 4.4 画面入出力項目 | ⑧ [画面入出力項目一覧](../screen/04-screen-io-items.md) | コードから逆生成 | 代替: 実動プロトタイプ |
| 4.5 画面アクション | ⑨ [画面アクション明細](../screen/05-screen-actions.md) | コードから逆生成 | 代替: Design Spec の API 一覧 |
| 4.6 画面共通ルール | ⑩ [画面遷移・レイアウト共通ルール](../screen/06-common-rules.md) | 人手 | ○ |
| **5. 帳票** | | | |
| 5.1 帳票一覧 | ㉓ [帳票一覧](../report/01-report-list.md) | コードから逆生成 | 代替: 要求 Spec のユースケースに現れる帳票 |
| 5.2 帳票概要 | ㉔ [帳票概要](../report/02-report-overview.md) | コード＋Spec | △ Spec 由来の部分のみ |
| 5.3 帳票レイアウト | ㉕ [帳票レイアウト](../report/03-report-layout.md) | コードから逆生成 | 代替: 実動プロトタイプの帳票出力 |
| 5.4 帳票項目 | ㉖ [帳票項目説明](../report/04-report-items.md) | コードから逆生成 | × |
| 5.5 帳票編集 | ㉗ [帳票編集定義](../report/05-report-edit-rules.md) | コード＋ADR | △ ADR 由来の部分のみ |
| **6. データ** | | | |
| 6.1 ER図 | ⑪ [ER図](../data/01-er-diagram.md) | コードから逆生成 | 代替: Design Spec の ER 概要 |
| 6.2 エンティティ一覧 | ⑫ [エンティティ一覧](../data/02-entity-list.md) | コードから逆生成 | 代替: Design Spec の主要テーブル一覧 |
| 6.3 エンティティ定義 | ⑬ [エンティティ定義](../data/03-entity-definition.md) | コードから逆生成 | × |
| 6.4 CRUD図 | ⑭ [CRUD図](../data/04-crud-matrix.md) | コードから逆生成 | × |
| **7. 外部インタフェース** | | | |
| 7.1 外部インタフェース一覧 | ⑯ [外部インタフェース一覧](../external-if/02-interface-list.md) | コードから逆生成 | 代替: Design Spec の外部 IF 連携先一覧 |
| 7.2 外部インタフェース項目 | ⑰ [外部インタフェース項目説明](../external-if/03-interface-items.md) | コードから逆生成 | 代替: 連携先から受領した仕様 |
| 7.3 外部インタフェース処理 | ⑱ [外部インタフェース処理説明](../external-if/04-interface-process.md) | コード＋Spec | △ Design Spec の連携方針のみ |
| **8. バッチ** | | | |
| 8.1 バッチ処理一覧 | ⑲ [バッチ処理一覧](../batch/01-batch-list.md) | コードから逆生成 | 代替: 要求 Spec のユースケースのうち定期実行するもの |
| 8.2 バッチ処理フロー | ⑳ [バッチ処理フロー](../batch/02-batch-flow.md) | コードから逆生成 | × |
| 8.3 バッチ処理定義 | ㉑ [バッチ処理定義](../batch/03-batch-definition.md) | コードから逆生成 | × |
| 8.4 バッチ共通ルール | ㉒ [バッチ処理共通ルール](../batch/04-common-rules.md) | 人手 | ○ |
| **9. 非機能** | | | |
| 9.1 非機能要件 | 要求 Spec 3.5（非機能要求グレードの6大項目・モデルシステム） | 人手 | ○ |
| 9.2 非機能設計 | Design Spec 7（可用性 / 性能・拡張性 / 運用・保守性 / 移行性 / システム環境・エコロジー） | 人手 | ○ |
| 9.3 セキュリティ | Design Spec 6 セキュリティ設計 | 人手 | ○ |
| **10. 設計判断** | ADR 一覧（`docs/adr/`） | 人手 | ○（Phase 2 時点の ADR） |
| **11. トレーサビリティ** | トレーサビリティマトリクス（REQ / PROP ⇔ テスト ⇔ 実装） | 逆生成 | 代替: 要求 Spec の REQ / PROP 一覧（テスト・実装列は空） |

凡例: ○ そのまま出せる ／ △ 一部だけ出せる ／ × 出せない（事前提出版では章に「納品時に提出」と書く）

### 事前提出で出せる範囲

27点のうち事前提出の時点で完成しているのは人手の5点（①②④⑩㉒）に限られ、併用の3点（⑱㉔㉗）は
Spec・ADR 由来の部分だけが書ける。**顧客が事前に「基本設計書」を求める場合、実質的な中身は Spec・ADR・実動
プロトタイプになる**ことを、Phase 2 の品質ゲートより前に顧客と合意しておく。

「×」の章（帳票項目・エンティティ定義・CRUD図・バッチ処理フロー／定義）は、実装前に書いても
実装後に書き直すことになる。J-SIX ではこれらを事前に書かない。どうしても事前に必要な場合は、
その章を GUIDE 4 の分類 (c)（新たに人手で書く）として扱い、納品時に逆生成版と突き合わせる。

---

## 2. 変種: 項目レベルを詳細設計書に回す

基本設計書を薄くし、項目レベルの成果物を詳細設計書に回す様式もある。その場合は次の6点を
[詳細設計書](shousai-sekkei.md)の「外部仕様の詳細」章に移し、基本設計書からは参照だけにする
（GUIDE 1.5）。

| 移す成果物 | 移した後に基本設計書に残すもの |
|---|---|
| ⑧ 画面入出力項目一覧 | 4.3 画面レイアウトまで |
| ⑬ エンティティ定義 | 6.2 エンティティ一覧まで |
| ⑰ 外部インタフェース項目説明 | 7.1 外部インタフェース一覧まで |
| ㉑ バッチ処理定義 | 8.2 バッチ処理フローまで |
| ㉖ 帳票項目説明 ／ ㉗ 帳票編集定義 | 5.3 帳票レイアウトまで |

どちらの様式でも、27点の中身と由来は変わらない。変わるのは**どの冊子に綴じるか**だけである。

---

## 3. 組立結果: monthly-billing

記入済み実例 [`examples/monthly-billing/`](../../../examples/monthly-billing/) を上の目次で
組み立てた場合の対応。画面・帳票・バッチ・外部 IF の全領域を持つため、「該当なし」の章は無い。

| 章 | 構成要素（実物） |
|---|---|
| 1.1〜1.3 | [要求 Spec](../../../examples/monthly-billing/docs/requirement-spec.md) 1・2・4・5 |
| 2.1 | [Design Spec](../../../examples/monthly-billing/docs/design-spec.md) 1 |
| 2.2 | [⑮ 外部システム関連図](../../../examples/monthly-billing/docs/deliverables/external-if/01-system-relation.md) |
| 3.1〜3.3, 3.5 | [① 業務一覧](../../../examples/monthly-billing/docs/deliverables/behavior/01-system-function-list.md) ／ [② 業務フロー](../../../examples/monthly-billing/docs/deliverables/behavior/02-business-flow.md) ／ [③ 業務説明](../../../examples/monthly-billing/docs/deliverables/behavior/03-business-description.md) ／ [④ 共通ルール](../../../examples/monthly-billing/docs/deliverables/behavior/04-common-rules.md) |
| 3.4 | 要求 Spec 3.2（REQ-001〜010）、3.3（PROP-001〜006） |
| 4.1〜4.6 | [画面6点](../../../examples/monthly-billing/docs/deliverables/screen/) |
| 5.1〜5.5 | [帳票5点](../../../examples/monthly-billing/docs/deliverables/report/) |
| 6.1〜6.4 | [データモデル4点](../../../examples/monthly-billing/docs/deliverables/data/) |
| 7.1〜7.3 | [外部インタフェース](../../../examples/monthly-billing/docs/deliverables/external-if/) ⑯⑰⑱ |
| 8.1〜8.4 | [バッチ4点](../../../examples/monthly-billing/docs/deliverables/batch/) |
| 9.1 | 要求 Spec 3.5（モデルシステム: 社会的影響が限定されるシステム。移行性は「移行しない」と決定、システム環境・エコロジーは理由付きで対象外） |
| 9.2 | Design Spec 7 非機能設計 |
| 9.3 | Design Spec 6 セキュリティ設計 |
| 10 | [ADR-0001〜0004](../../../examples/monthly-billing/docs/adr/)（端数処理の単位・方法、帳票形式、form の解析方法） |
| 11 | [トレーサビリティマトリクス](../../../examples/monthly-billing/docs/traceability.md) |

### この例で目立つ点

**3.3 システム化業務説明は hold-out 受入テストから逆生成している。**事前条件・基本シナリオ・
事後条件が、それぞれ fixture・テスト本体・アサーションに対応する。この章は「通っている
テスト」を根拠にしており、テストが落ちれば章の記述も誤りになる。基本設計書の中で、
**記述の正しさが品質ゲート（G2）で機械的に保証されている章**である。

**5.5 帳票編集定義の端数処理は ADR-0001 に依存する。**「税率ごとに1回だけ丸める」という
記述の根拠は法令（国税庁 インボイス制度 Q&A 問57）であり、コードからは「そう実装されている」
ことしか分からない。コード＋ADR の併用由来になっているのはこのためで、組立時には 10 章の
ADR-0001 への参照を 5.5 に残す。
