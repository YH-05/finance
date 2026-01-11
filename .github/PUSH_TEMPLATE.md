# コミットメッセージテンプレート

プッシュ前のコミットメッセージ作成時に参照してください。

## フォーマット

```
<type>: <summary>

<detailed description if needed>

Co-Authored-By: Claude <noreply@anthropic.com>
```

## 変更の種類 (type)

| Type       | 説明                     | 例                                |
| ---------- | ------------------------ | --------------------------------- |
| `feat`     | 新機能                   | feat: ユーザー認証機能を追加      |
| `fix`      | バグ修正                 | fix: ログイン時の500エラーを修正  |
| `docs`     | ドキュメント             | docs: README にインストール手順を追加 |
| `refactor` | リファクタリング         | refactor: 認証ロジックを整理      |
| `test`     | テスト                   | test: ユーザーモデルのテストを追加 |
| `chore`    | その他（ビルド、CI等）   | chore: GitHub Actions を更新      |
| `style`    | コードスタイル           | style: フォーマットを修正         |
| `perf`     | パフォーマンス改善       | perf: クエリを最適化              |

## プッシュ前チェックリスト

- [ ] `make check-all` が成功している
- [ ] 適切なブランチにいることを確認した
- [ ] コミットメッセージが上記フォーマットに従っている
- [ ] 機密情報（APIキー、パスワード等）が含まれていない
- [ ] 不要なファイル（.env、node_modules等）がコミットされていない

## ブランチ命名規則

| プレフィックス | 用途             |
| -------------- | ---------------- |
| `feature/`     | 機能追加         |
| `fix/`         | バグ修正         |
| `refactor/`    | リファクタリング |
| `docs/`        | ドキュメント更新 |
| `test/`        | テスト追加・修正 |

## 例

### 機能追加

```
feat: ユーザー認証機能を追加

JWTトークンベースの認証システムを実装。
- ログイン/ログアウトエンドポイント追加
- トークンリフレッシュ機能
- ミドルウェアによる認証チェック

Co-Authored-By: Claude <noreply@anthropic.com>
```

### バグ修正

```
fix: ログイン時の500エラーを修正

認証トークンの検証ロジックに問題があり、
有効期限切れのトークンで例外が発生していた。

Co-Authored-By: Claude <noreply@anthropic.com>
```

### ドキュメント更新

```
docs: APIドキュメントを更新

新しいエンドポイントの説明を追加。

Co-Authored-By: Claude <noreply@anthropic.com>
```
