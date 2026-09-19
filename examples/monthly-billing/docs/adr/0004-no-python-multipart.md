# ADR-0004: form の解析に python-multipart を使わない

## ステータス

承認

## 日付

2026-09-19

## コンテキスト（背景）

請求の確定（ACT-004 / UC-006）は、画面からの form post と、プログラムからの JSON の両方で
操作者（`actor`）を受け取る（監査ログ REQ-010 に正しい操作者を残すため）。form の解析には
Starlette の `request.form()` を使っており、これは python-multipart に依存する。

CI の依存脆弱性スキャン（品質ゲート G1 の deps。trivy）が、python-multipart 0.0.20 に
HIGH 3件（CVE-2026-24486 / CVE-2026-42561 / CVE-2026-53539）を検出し、ゲートが止まった。
修正版（0.0.22 以降）はいずれも **Python 3.10 以上**を要求し、0.0.20 が 3.9 で入る最後の版である。

- 関連要件: REQ-010（監査記録）, UC-006
- 関連画面: SCR-003（請求書プレビュー）のフォームは `enctype` 未指定（= x-www-form-urlencoded）

## 判断（Decision）

- python-multipart を依存から外す
- form（`application/x-www-form-urlencoded`）は標準ライブラリの `urllib.parse.parse_qs` で読む
- `multipart/form-data` は **HTTP 415** で拒否し、確定しない

## 理由（Rationale）

本サンプルが form で受け取る値は `actor` の1項目だけで、ファイル添付も無い。multipart の
解析器を持つ必要がそもそも無く、依存を外せば脆弱性の対象ごと消える。

multipart を黙って既定値の操作者で処理しないのは、ACT-004 がもともと「片方の形式を黙って
既定値にすると監査ログに誤った操作者が残る」ことを避けるために両形式を受けているためである。
受け付けない形式は明示的に拒否する。

## 検討した代替案

### 代替案A: Python の下限を 3.10 に上げて python-multipart を更新する

- メリット: `request.form()` をそのまま使える。multipart も受け付けられる
- デメリット: `examples/approval-workflow` と揃えた「Python 3.9+」の前提が崩れる。
  本サンプルのローカル環境（3.9）で再現できなくなる
- 却下理由: 使っていない機能（multipart）のために動作環境の前提を変えることになる

### 代替案B: 例外として許容し、deps ゲートの閾値を下げる

- メリット: 変更が最小
- デメリット: 既知の HIGH を抱えたまま「ゲート通過」と表示される
- 却下理由: ゲートを通すために閾値を動かすのは、J-SIX が禁じるテスト弱体化と同じ構図である

## 影響（Consequences）

### ポジティブ

- 依存が1つ減り、G1 deps が通る
- Python 3.9 のまま動く

### ネガティブ・リスク

- multipart/form-data で送るクライアントは 415 になる。画面を multipart に変える場合
  （ファイル添付など）は本 ADR を見直す

## 参照

- CI 実行: G1 deps が python-multipart の HIGH 3件で失敗（本 ADR の起点）
- テスト: `tests/test_api.py::TestConfirmActor::test_multipart_is_rejected_not_defaulted`
