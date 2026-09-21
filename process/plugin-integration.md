# 設計メモ：Plugin からプロセス定義を参照する

**Author**: H.Sekita | **Date**: 2026-09-22 | **状態**: 設計メモ（未実装。ROADMAP H2'）

> 本メモは、J-SIX Plugin が `process/jsix-process.yaml` を参照する場合の設計案である。
> 実装は Plugin 側の別作業とし、本メモの時点では Plugin を変更していない。

---

## 1. 目的

現在、Phase・ゲートの構成は `docs/J-SIX.md`、Plugin のスクリプト（`plugin/scripts/jsix_run_checks.py` の G1→G4 の順序）、
Skill の本文（`tdd-cycle` など）に、それぞれ別に書かれている。プロセス定義を Plugin から参照すると、
ゲートの層の順序とチェックの一覧を1か所（yaml）から取れるようになり、J-SIX Hub と Plugin が同じ定義を使える
（[ADR-0003](../docs/control-plane/adr/0003-dependency-direction-and-process-as-data.md)）。

## 2. 制約

| 制約 | 理由 |
|---|---|
| **Plugin は Hub に依存しない** | 決定事項 D3。yaml は j-six リポジトリにあり、Hub ではない。この制約とは矛盾しない |
| **Plugin のスクリプトは標準ライブラリだけで動く** | 現在の `plugin/scripts/` は PyYAML 等に依存していない。利用者の環境に追加のパッケージを求めない |
| **インストールされた Plugin からはリポジトリの `process/` が見えない** | マーケットプレイスからは Plugin ディレクトリだけがコピーされる。`templates/` と同じ問題（`tools/sync_plugin_templates.py` の冒頭を参照） |
| **`origin: hub-concept` の要素は Plugin では使わない** | Interface Contract・逸脱の状態機械は Hub の構想で追加したもの。J-SIX 単体の動作を変えない |

## 3. 案

1. **JSON に変換して同梱する**。`tools/sync_plugin_templates.py` と同じ方式で、yaml を JSON に変換したものを
   `plugin/process/jsix-process.json` に生成する（標準ライブラリの `json` で読める）。正は yaml のままとし、
   CI で `--check` してずれを検出する
2. **読むのは P4 のゲートだけから始める**。`task_quality_gate` の層の順序（G1→G4）、各層のチェック ID、
   `optional`（G3）を `jsix_run_checks.py` が参照する。Phase の遷移や状態機械は Plugin では使わない
3. **`.jsix-checks.json` のキーはチェック ID に合わせる**。現在のキーは次のとおりで、大半は既に一致している

| yaml（`task_quality_gate`） | `.jsix-checks.json` | 差異 |
|---|---|---|
| G1 / build, lint, format, sast, secrets, deps, scope | `gates.g1.*` | 一致 |
| G1 / typecheck | なし | J-SIX.md は G1 に「型」を含むが、設定キーもスクリプトもない。言語によっては build に含まれる。扱いを決める必要がある |
| G1 / interface_contract | なし | `origin: hub-concept`。Plugin では扱わない |
| G2 / tests, holdout, coverage, mutation, test_tamper, traceability | `gates.g2.*` | 一致 |
| G3 / scope_judge | `gates.g3`（agent, verdict, max_auto_fix） | 層の設定であり、チェック ID のキーはない |
| G4 / evidence_pack | `gates.g4`（out, formats） | 同上 |

4. **既定の動作は変えない**。yaml を読めない場合（同梱ファイルが無い等）は、現在のハードコードされた順序で動く

## 4. 未決事項

- G1 の「型検査」を独立したチェックにするか、build に含めるか（上表）
- yaml の版（タグ）と Plugin の版（`plugin.json` の version）の対応をどう記録するか
- Skill の本文（`tdd-cycle` の手順）に書かれた層の説明を、yaml から生成するか、人手で揃えるか
