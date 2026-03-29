# CLAUDE.md 追加セクション — Web アプリケーション向け

> base.md の内容に加え、以下のセクションを CLAUDE.md に追記してください。

---

## 画面設計ルール

### UI フレームワーク

- コンポーネントライブラリ: [TODO: MUI / Chakra UI / shadcn/ui / 独自 等]
- CSS 方針: [TODO: CSS Modules / Tailwind CSS / styled-components 等]
- アイコン: [TODO: lucide-react / Material Icons 等]

### コンポーネント設計

- コンポーネントの分類:
  - `components/ui/`: 汎用UIコンポーネント（ボタン、モーダル等）
  - `components/features/`: 機能固有コンポーネント
  - `components/layouts/`: レイアウトコンポーネント
- 1コンポーネント = 1ファイル。150行を超える場合は分割を検討
- Props は型定義を必須とする（TypeScript の場合）
- 状態管理: [TODO: useState / Zustand / Redux 等]
- データフェッチ: [TODO: SWR / React Query / Server Components 等]

### 画面遷移

- ルーティング: [TODO: Next.js App Router / React Router 等]
- 画面遷移図: `docs/specs/design-spec.md#画面遷移` を参照
- 新規画面を追加する場合は、画面遷移図との整合を確認すること

### アクセシビリティ

- セマンティック HTML を優先（`div` の乱用を避ける）
- フォーム要素には `label` を必ず紐付ける
- 画像には `alt` を設定
- キーボード操作に対応する
- [TODO: WCAG 準拠レベル（AA / AAA）]

### レスポンシブ対応

- ブレイクポイント: [TODO: sm:640px / md:768px / lg:1024px 等]
- モバイルファースト / デスクトップファースト: [TODO: どちらか]
- 対応ブラウザ: [TODO: Chrome最新2バージョン、Edge、Safari 等]

---

## フロントエンドテスト

- コンポーネントテスト: [TODO: React Testing Library / Vitest 等]
- E2E テスト: [TODO: Playwright / Cypress 等]
- E2E テストの配置: [TODO: e2e/ / tests/e2e/ 等]
- ビジュアルリグレッションテスト: [TODO: 使用する場合のツール]

```bash
# コンポーネントテスト実行
[TODO: コマンド]

# E2E テスト実行
[TODO: コマンド]
```

---

## 認証・認可

- 認証方式: [TODO: セッション / JWT / OAuth2 等]
- 認証プロバイダ: [TODO: Auth0 / Firebase Auth / 自前実装 等]
- 認可モデル: [TODO: RBAC / ABAC 等]
- ログイン画面: [TODO: パス]
- 未認証時の挙動: [TODO: ログイン画面にリダイレクト 等]

---

## SEO・メタ情報

- [TODO: SSR / SSG / CSR の方針]
- メタタグ管理: [TODO: next/head / react-helmet 等]
- OGP 画像: [TODO: 生成方針]
- サイトマップ: [TODO: 自動生成 / 手動管理]
