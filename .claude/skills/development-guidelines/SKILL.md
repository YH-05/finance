---
name: development-guidelines
description: チーム全体で統一された開発プロセスとコーディング規約を確立するための包括的なガイドとテンプレート。開発ガイドライン作成時、コード実装時に使用する。
allowed-tools: Read, Write, Edit
---

# 開発ガイドラインスキル

チーム開発に必要な 2 つの要素をカバーします:

1. 実装時のコーディング規約 (coding-standards.md)
2. 開発プロセスの標準化 (development-process.md)

## 前提条件

開発ガイドライン作成を開始する前に、以下を確認してください:

### 推奨ドキュメント

1. `src/<library_name>/docs/architecture.md` (アーキテクチャ設計書) - 技術スタックの確認
2. `src/<library_name>/docs/repository-structure.md` (リポジトリ構造) - ディレクトリ構造の確認

開発ガイドラインは、ライブラリの技術スタックとディレクトリ構造に
基づいた具体的なコーディング規約と開発プロセスを定義します。

## 既存ドキュメントの優先順位

**重要**: `src/<library_name>/docs/development-guidelines.md` に既存の開発ガイドラインがある場合、
以下の優先順位に従ってください:

1. **既存の開発ガイドライン (`src/<library_name>/docs/development-guidelines.md`)** - 最優先

    - ライブラリ固有の規約とプロセスが記載されている
    - このスキルのガイドより優先する

2. **このスキルのガイド** - 参考資料
    - docs/coding-standards.md: 汎用的なコーディング規約
    - docs/development-process.md: 汎用的な開発プロセス
    - 既存ガイドラインがない場合、または補足として使用

**新規作成時**: このスキルのガイドとテンプレートを参照
**更新時**: 既存ガイドラインの構造と内容を維持しながら更新

## 出力先

作成した開発ガイドラインは以下に保存してください:

```
src/<library_name>/docs/development-guidelines.md
```

**注意**: `<library_name>` は `/new-project` コマンドの引数パスから抽出してください。

## クイックリファレンス

### コード実装時

コード実装時のルールと規約: docs/coding-standards.md

含まれる内容:

-   Python 規約（PEP 695 準拠）
-   型定義・命名規則
-   関数設計とエラーハンドリング
-   コメント規約（NumPy 形式）
-   セキュリティとパフォーマンス
-   テストコード実装（pytest）
-   リファクタリング手法

### 開発プロセスの参照／策定時

Git 運用、テスト戦略、コードレビュー: docs/development-process.md

含まれる内容:

-   基本原則（具体例の重要性、理由説明）
-   Git 運用ルール（Git Flow ブランチ戦略）
-   コミットメッセージと PR プロセス
-   テスト戦略（ピラミッドとカバレッジ）
-   コードレビューのプロセス
-   品質自動化

### テンプレート

開発ガイドライン作成時: ./template.md

## 使用シーン別ガイド

### 新規開発時

1. docs/coding-standards.md で命名規則・コーディング規約を確認
2. docs/development-process.md でブランチ戦略・PR 処理を確認
3. テストを先に書く（TDD）

### コードレビュー時

-   docs/development-process.md の「コードレビュープロセス」を参照
-   docs/coding-standards.md で規約違反がないか確認

### テスト設計時

-   docs/development-process.md の「テスト戦略」（ピラミッド、カバレッジ）
-   docs/coding-standards.md の「テストコード」（実装パターン）

### リリース準備時

-   docs/development-process.md の「Git 運用ルール」（main へのマージ方針）
-   コミットメッセージが Conventional Commits に従っているか確認

## チェックリスト

-   [ ] コーディング規約が具体例付きで定義されている
-   [ ] 命名規則が明確である（言語別・ライブラリ固有）
-   [ ] エラーハンドリングの方針が定義されている
-   [ ] ブランチ戦略が決まっている（Git Flow 推奨）
-   [ ] コミットメッセージ規約が明確である
-   [ ] PR テンプレートが用意されている
-   [ ] テストの種類とカバレッジ目標が設定されている
-   [ ] コードレビュープロセスが定義されている
-   [ ] CI/CD パイプラインが構築されている
