# J-SIX ワークスルー：Phase 4 TDD 実装の実際

**Author**: H.Sekita | **Date**: 2026-03-29

> J-SIX_v1.0 の補足資料。Phase 4（TDD 実装）で CC が実際にどう動くかを、
> 具体的なコマンド・プロンプト・出力例で示す。

---

## 1. シナリオ設定

**お題**: ECサイトの「ユーザー登録API」を TDD で実装する

**前提**:
- Phase 3 で以下のタスクが承認済み
- CLAUDE.md が整備済み（コーディング規約、テスト方針、ADRルール等）
- 技術スタック: TypeScript + Express + PostgreSQL + Jest

**タスク定義（Phase 3 の成果物）**:
```
タスク: USER-001 ユーザー登録API
受入条件:
  - POST /api/v1/users でユーザーを新規登録できる
  - email の重複チェックを行い、重複時は 409 を返す
  - パスワードは bcrypt でハッシュ化して保存
  - 成功時は 201 + ユーザー情報（パスワード除く）を返す
  - バリデーション: email 形式、パスワード8文字以上
依存: なし（並列実行可能）
```

---

## 2. TDD サイクルの実際

### Step 1: CC にタスクを指示

```
あなた:
  USER-001「ユーザー登録API」をTDDで実装してください。
  受入条件は以下の通りです。
  [受入条件を貼り付け]
  
  TDDの手順:
  1. まずテストを書いてください（Red Phase）
  2. テストが失敗することを確認してコミットしてください
  3. テストが通る最小の実装を書いてください（Green Phase）
  4. テストが通ることを確認してコミットしてください
  5. 必要ならリファクタリングしてください（Refactor Phase）
```

> **ポイント**: CC に「TDDの手順」を明示する。CLAUDE.md にこの手順を書いておけば毎回指示する必要はない。

### Step 2: 🔴 Red Phase — テスト作成（サブエージェント A）

CC がテストコードを生成する。この時点では実装は存在しないためテストは失敗する。

**CC が生成するテストコード（例）**:

```typescript
// src/features/users/__tests__/register-user.test.ts

describe('POST /api/v1/users', () => {
  describe('正常系', () => {
    it('有効な入力でユーザーを登録し201を返す', async () => {
      const res = await request(app)
        .post('/api/v1/users')
        .send({
          email: 'test@example.com',
          password: 'password123',
          name: 'テスト太郎',
        });

      expect(res.status).toBe(201);
      expect(res.body).toHaveProperty('id');
      expect(res.body.email).toBe('test@example.com');
      expect(res.body).not.toHaveProperty('password');
    });
  });

  describe('バリデーション', () => {
    it('不正なemail形式で400を返す', async () => {
      const res = await request(app)
        .post('/api/v1/users')
        .send({ email: 'invalid', password: 'password123', name: '太郎' });

      expect(res.status).toBe(400);
    });

    it('8文字未満のパスワードで400を返す', async () => {
      const res = await request(app)
        .post('/api/v1/users')
        .send({ email: 'test@example.com', password: 'short', name: '太郎' });

      expect(res.status).toBe(400);
    });
  });

  describe('重複チェック', () => {
    it('既存emailで409を返す', async () => {
      // 1人目を登録
      await request(app)
        .post('/api/v1/users')
        .send({ email: 'dup@example.com', password: 'password123', name: '太郎' });

      // 同じemailで2人目を登録
      const res = await request(app)
        .post('/api/v1/users')
        .send({ email: 'dup@example.com', password: 'password456', name: '次郎' });

      expect(res.status).toBe(409);
    });
  });

  describe('セキュリティ', () => {
    it('パスワードがハッシュ化されてDBに保存される', async () => {
      await request(app)
        .post('/api/v1/users')
        .send({ email: 'hash@example.com', password: 'password123', name: '太郎' });

      const user = await db.query('SELECT password_hash FROM users WHERE email = $1', ['hash@example.com']);
      expect(user.rows[0].password_hash).not.toBe('password123');
    });
  });
});
```

**CC のアクション**:
```
CC: テストを作成しました。実行して失敗を確認します。

$ npm test -- --testPathPattern=register-user

  FAIL  src/features/users/__tests__/register-user.test.ts
  ● POST /api/v1/users › 正常系 › 有効な入力でユーザーを登録し201を返す
    Cannot find module '../register-user.controller'

  Tests: 5 failed, 0 passed

テストが期待通り失敗しました。コミットします。

$ git add -A
$ git commit -m "test(users): ユーザー登録APIのテストを追加（Red Phase）"
```

> **ポイント**: テスト失敗を確認してからコミット。これがチェックポイントとなり、次のGreen Phaseで CC がテストを改変した場合に diff で検出できる。

### Step 3: 🟢 Green Phase — 最小実装（サブエージェント B）

CC がテストを通す最小の実装を行う。

**CC のアクション**:
```
CC: テストを通す最小の実装を行います。

[CC がコントローラ、サービス、バリデーション等を生成]

テストを実行します。

$ npm test -- --testPathPattern=register-user

  PASS  src/features/users/__tests__/register-user.test.ts
  ✓ 有効な入力でユーザーを登録し201を返す (45ms)
  ✓ 不正なemail形式で400を返す (12ms)
  ✓ 8文字未満のパスワードで400を返す (8ms)
  ✓ 既存emailで409を返す (67ms)
  ✓ パスワードがハッシュ化されてDBに保存される (34ms)

  Tests: 5 passed

全テスト通過。コミットします。

$ git add -A
$ git commit -m "feat(users): ユーザー登録APIを実装（Green Phase）"
```

### Step 4: 🔵 Refactor Phase — リファクタリング（サブエージェント C）

```
CC: リファクタリングの余地を確認します。

  - バリデーションロジックを共通ミドルウェアに抽出
  - エラーレスポンスのフォーマットを統一ヘルパーに移行
  - [リファクタリング実施]

テストを再実行して、リファクタリングが機能を壊していないことを確認します。

$ npm test -- --testPathPattern=register-user

  Tests: 5 passed

コミットします。

$ git add -A
$ git commit -m "refactor(users): バリデーションを共通ミドルウェアに抽出"
```

### Step 5: ADR の自動記録

```
CC: パスワードのハッシュ化に bcrypt を使用する設計判断を行いました。
    ADR を作成します。

[docs/adr/0005-password-hashing-bcrypt.md を自動生成]

  # ADR-0005: パスワードハッシュに bcrypt を採用
  ## 判断: bcrypt を使用
  ## 検討した代替案:
  | argon2 | より新しい | ライブラリ成熟度が低い | チームの経験不足 |
  | scrypt  | Node.js標準 | チューニングが複雑 | bcryptの方がシンプル |

確認をお願いします。問題なければ承認してください。
```

> **ポイント**: CC が設計判断を検出し、ADR ドラフトを自動提案する。人間は確認・修正するだけ。

---

## 3. エスカレーションの実例

### 例: Spec 外の要件を発見した場合

```
CC: 実装中に確認事項があります。

  受入条件にはメールアドレスの確認（メール送信）について
  記載がありませんが、一般的なユーザー登録フローでは
  メールアドレスの確認ステップが必要です。

  以下のいずれかを選択してください:
  1. メール確認なしで登録完了（現在の受入条件通り）
  2. メール確認フローを追加（Spec の更新が必要）
  3. この判断を保留し、後続タスクで対応

  どちらにしますか？
```

> **ポイント**: CC は Spec に記載のない要件を勝手に実装しない。人間にエスカレーションする。

### 例: テスト3回連続失敗の場合

```
CC: ⚠️ エスカレーション: テストが3回連続で失敗しました。

  失敗しているテスト: 既存emailで409を返す
  
  試行1: unique constraint の catch が不完全
  試行2: PostgreSQL のエラーコード判定を修正したが別のテストが壊れた
  試行3: トランザクション分離レベルの問題の可能性

  根本的な設計判断が必要かもしれません。
  現在のDB設計（unique constraint vs アプリ層でのチェック）について
  方針を確認してください。
```

---

## 4. 並列実行の実例

```
ターミナル配置（tmux / Agent Teams）:

┌─────────────────────┬─────────────────────┐
│ CC Session 1        │ CC Session 2        │
│ (USER-001)          │ (USER-002)          │
│ ユーザー登録API     │ ユーザー検索API     │
│                     │                     │
│ [TDD中...]          │ [TDD中...]          │
│ 🟢 Green Phase      │ 🔴 Red Phase        │
├─────────────────────┼─────────────────────┤
│ CC Session 3        │ メイン（監視）      │
│ (USER-003)          │                     │
│ ユーザー更新API     │ $ git log --oneline │
│                     │ 品質ダッシュボード   │
│ [待機: USER-001依存]│                     │
└─────────────────────┴─────────────────────┘

git worktree で各セッションが独立した作業ディレクトリを持つ:
  main/           ← メインブランチ
  worktrees/
    user-001/     ← CC Session 1 の作業空間
    user-002/     ← CC Session 2 の作業空間
    user-003/     ← CC Session 3（USER-001完了後に開始）
```

---

## 参考文献

- Anthropic. "Best Practices for Claude Code". https://code.claude.com/docs/en/best-practices
- alexop.dev. "Forcing Claude Code to TDD" (2025.11). https://alexop.dev/posts/custom-tdd-workflow-claude-code-vue/
- DataCamp. "Claude Code Best Practices" (2026.03). https://www.datacamp.com/tutorial/claude-code-best-practices
