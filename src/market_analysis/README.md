# market_analysis

金融市場分析パッケージ

## 概要

このパッケージは市場データの取得・分析・可視化機能を提供します。

**現在のバージョン:** 0.1.0

## ディレクトリ構成

```
market_analysis/
├── __init__.py           # 公開 API 定義（__version__含む）
├── py.typed              # PEP 561 マーカー
├── types.py              # 型定義
├── core/                 # コアビジネスロジック
│   └── __init__.py
└── utils/                # ユーティリティ関数
    ├── __init__.py
    └── logging_config.py # 構造化ロギング設定
```

## 実装状況

| モジュール                | 状態        | 備考                                |
| ------------------------- | ----------- | ----------------------------------- |
| `types.py`                | ✅ 実装済み | 基本型定義                          |
| `utils/logging_config.py` | ✅ 実装済み | 構造化ロギング                      |
| `core/`                   | ⏳ 未実装   | `/issue` → `feature-implementer` で実装 |

## 公開 API

```python
from market_analysis import get_logger
```

## 拡張ガイド

1. **コアモジュール追加**: `/issue` → `feature-implementer` で TDD 実装
2. **ユーティリティ追加**: `/issue` → `feature-implementer` で TDD 実装
3. **型定義追加**: `types.py` に追加

## 関連ドキュメント

-   `template/src/template_package/README.md` - テンプレート実装の詳細
-   `docs/development-guidelines.md` - 開発ガイドライン
