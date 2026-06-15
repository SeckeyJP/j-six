# J-SIX 改善ロードマップ

**Author**: H.Sekita | **対象バージョン**: v2.1 → v2.5 想定

J-SIX は v2.0・全15記事公開で一区切りついた。本ロードマップは次フェーズの改善・追加機能を、
**実証・信頼性 / テンプレート充実 / Plugin 実用拡張** の3領域で整理したものである。

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
| A2 | 期待効果の数値に「検証ステータス」列を追加（推定/実測/外部出典を明示） | `docs/J-SIX.md` 第1章, `README.md` | 小 | ☐ |
| A3 | 出典鮮度の定期レビュー運用（四半期）。`/schedule` 化も検討 | `docs/REFERENCES_AUDIT.md` に運用節追加 | 小 | ☐（Q2 で監査日は更新済） |
| A1' | 同一題材で「人手のみ実装」との工数 A/B 比較（工数削減の初の実測） | case-study に追記 | 中 | ☐（A1 で次アクションとして提起） |

## B. テンプレート充実

**狙い**: プレースホルダーのみ → 「動く実例」を併置し初心者の導入障壁を下げる。

| # | タスク | 成果物 | 規模 | 状態 |
|---|---|---|---|---|
| B1 | **記入済みサンプル**（FastAPI api-service の CLAUDE.md 実例） | `examples/approval-workflow/CLAUDE.md` | 中 | ✅ 2026-06-14 |
| B2 | Spec / ADR の記入済み実例（A1 題材と連動） | `examples/approval-workflow/docs/`（spec×2, adr×2, traceability） | 中 | ✅ 2026-06-14 |
| B3 | templates/README に「テンプレ → 実例 → 該当 Skill」の導線表を追加 | `templates/README.md` | 小 | ✅ 2026-06-14 |
| B1' | 別スタック（Next.js / Spring Boot）の記入済み CLAUDE.md 実例 | `examples/` | 中 | ☐（FastAPI 版を先行） |

## C. Plugin 実用拡張

**狙い**: 「説明はあるが prompt 型 Hook のみ」→ **決定論的に動く**ガードレールへ。

| # | タスク | 成果物 | 規模 | 状態 |
|---|---|---|---|---|
| C1 | **コマンド型 Hook 追加**（カバレッジ閾値ゲート、要件⇔テストのトレーサビリティ自動チェック）。番外編 Hooks 記事の知見を本体還元 | `plugin/scripts/` ×3 + Stop command Hook（オプトイン） | 中 | ✅ 2026-06-14 |
| C2 | **end-to-end デモ**（B1/A1 と同一題材で Skills 6 / Agents 5 を実際に動かした証跡） | `examples/approval-workflow/README.md`（Phase別 Skill 対応表） | 大 | ◐ 部分（成果物と対応表は整備済。各 Skill の実行ログ取得は残） |
| C3 | plugin.json に `keywords` 等メタ補強、インストール手順の検証 | `plugin/.claude-plugin/plugin.json` | 小 | ☐ |

---

## 推奨実行順（依存関係を考慮）

```
Q1,Q2（整合）→ A1 ケーススタディ題材を決定
        └→ その題材を B1/B2（実例）と C2（デモ）で再利用 ＝ 一貫した1本の縦串
C1（Hook）は独立して並行可
A2,A3,B3,C3 は仕上げ
```

---

## 改訂履歴

| Date | 内容 |
|---|---|
| 2026-06-14 | 初版作成（v2.0 完了後の次フェーズ計画） |
