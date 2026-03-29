---
name: spec-create
description: J-SIX Phase 1-2 で使用。要求Spec または Design Spec を日本語テンプレートに沿って策定する。ユーザーとの対話を通じて Spec を完成させる。
allowed-tools: Read, Write, Edit, Glob, Grep
---

# Spec 策定スキル

J-SIX プロセスの Phase 1（要求の合意）または Phase 2（技術設計）で Spec を策定する。

## 手順

### 1. Spec 種別の確認

ユーザーに以下を確認する:
- **要求 Spec**（Phase 1）: 業務背景・目的・スコープ・制約を定義
- **Design Spec**（Phase 2）: アーキテクチャ方針・技術選定・非機能要件を定義

### 2. テンプレートの読み込み

要求 Spec の場合:
```
!`cat templates/spec/requirement-spec.md`
```

Design Spec の場合:
```
!`cat templates/spec/design-spec.md`
```

### 3. 対話的な Spec 策定

テンプレートの各セクションについて、ユーザーに質問しながら内容を埋めていく。

**重要なルール**:
- ユーザーの回答をそのまま記録する。勝手に要件を追加しない
- 不明確な箇所は「TBD」として残し、ユーザーに確認を促す
- 技術的な提案をする場合は、理由と代替案も併記する
- 数値目標は根拠を確認する

### 4. Spec ファイルの出力

完成した Spec を `docs/specs/` ディレクトリに保存する。

ファイル名規則: `requirement-spec-[機能名].md` または `design-spec-[機能名].md`

### 5. Phase Gate チェックリスト

Spec 完成時に以下を確認:
- [ ] 全ステークホルダーの期待が記録されているか
- [ ] スコープ（対象/対象外）が明確か
- [ ] 受入条件が検証可能な形式で書かれているか
- [ ] 非機能要件に具体的な数値があるか
- [ ] 制約・前提条件が明示されているか
