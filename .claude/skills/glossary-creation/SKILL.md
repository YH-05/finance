---
name: glossary-creation
description: 用語集を作成するための詳細ガイドとテンプレート。用語集作成時にのみ使用。
allowed-tools: Read, Write
---

# 用語集作成スキル

このスキルは、ライブラリ固有の用語と技術用語を体系的に定義するための詳細ガイドです。

## 前提条件

用語集作成を開始する前に、以下を確認してください:

### 推奨ドキュメント

1. **src/<library_name>/docs/library-requirements.md** (LRD)
2. **src/<library_name>/docs/functional-design.md** (機能設計書)
3. **src/<library_name>/docs/architecture.md** (アーキテクチャ設計書)
4. **src/<library_name>/docs/repository-structure.md** (リポジトリ構造)
5. **src/<library_name>/docs/development-guidelines.md** (開発ガイドライン)

用語集は、全てのドキュメントで使用される用語を統一的に定義します。
各ドキュメントから用語を抽出し、体系的に整理してください。

## 既存ドキュメントの優先順位

**重要**: `src/<library_name>/docs/glossary.md` に既存の用語集がある場合、
以下の優先順位に従ってください:

1. **既存の用語集 (`src/<library_name>/docs/glossary.md`)** - 最優先
   - ライブラリ固有の用語定義が記載されている
   - このスキルのガイドより優先する

2. **このスキルのガイド** - 参考資料
   - 汎用的なテンプレートと例
   - 既存用語集がない場合、または補足として使用

**新規作成時**: このスキルのテンプレートとガイドを参照
**更新時**: 既存用語集の構造と内容を維持しながら更新

## 出力先

作成した用語集は以下に保存してください:

```
src/<library_name>/docs/glossary.md
```

**注意**: `<library_name>` は `/new-project` コマンドの引数パスから抽出してください。

## テンプレートの参照

用語集を作成する際は、次のテンプレートを使用してください ./template.md

## 詳細ガイド

さらに詳しい作成ガイドは次のファイルを参照してください: ./guide.md
