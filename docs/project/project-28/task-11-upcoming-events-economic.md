# Task 11: 経済指標発表予定取得機能の実装

**Phase**: 3 - 来週の注目材料
**依存**: なし
**ファイル**: `src/analyze/reporting/upcoming_events.py`（部分）

## 概要

FRED API を使用して主要経済指標の発表予定を取得する機能を実装する。

## 対象リリース

```python
MAJOR_RELEASES: dict[str, dict[str, str]] = {
    "10": {"name": "Employment Situation", "name_ja": "雇用統計"},
    "50": {"name": "Gross Domestic Product", "name_ja": "GDP速報"},
    "21": {"name": "Consumer Price Index", "name_ja": "消費者物価指数"},
    "53": {"name": "FOMC Statement", "name_ja": "FOMC声明"},
    "46": {"name": "Producer Price Index", "name_ja": "生産者物価指数"},
    "328": {"name": "Personal Income and Outlays", "name_ja": "個人所得・支出"},
    "83": {"name": "Industrial Production and Capacity Utilization", "name_ja": "鉱工業生産"},
    "120": {"name": "Retail Sales", "name_ja": "小売売上高"},
}
```

## 実装仕様

### クラス設計（部分）

```python
class UpcomingEventsCollector:
    """来週の注目材料（決算・経済指標）を取得するクラス."""

    MAJOR_RELEASES: ClassVar[dict[str, dict[str, str]]] = {
        "10": {"name": "Employment Situation", "name_ja": "雇用統計"},
        # ...
    }

    def get_upcoming_economic_releases(
        self,
        start_date: date,
        end_date: date,
    ) -> list[dict[str, Any]]:
        """指定期間内の経済指標発表予定を取得.

        FRED API の releases/dates エンドポイントを使用。

        Parameters
        ----------
        start_date : date
            検索開始日
        end_date : date
            検索終了日

        Returns
        -------
        list[dict[str, Any]]
            経済指標発表予定のリスト
        """
        ...

    def _fetch_release_dates(
        self,
        start_date: date,
        end_date: date,
    ) -> list[dict[str, Any]]:
        """FRED API から発表日を取得."""
        ...
```

### FRED API 使用方法

```python
import requests

api_key = os.environ.get("FRED_API_KEY")
url = "https://api.stlouisfed.org/fred/releases/dates"

params = {
    "api_key": api_key,
    "file_type": "json",
    "include_release_dates_with_no_data": "true",
    "sort_order": "asc",
    # realtime_start と realtime_end で期間指定
}

response = requests.get(url, params=params)
data = response.json()
# {
#     "realtime_start": "2026-01-30",
#     "realtime_end": "2026-02-05",
#     "release_dates": [
#         {"release_id": 10, "release_name": "Employment Situation", "date": "2026-02-07"},
#         ...
#     ]
# }
```

### 出力形式

```python
[
    {
        "release_id": "10",
        "name": "Employment Situation",
        "name_ja": "雇用統計",
        "date": "2026-02-07",
        "importance": "high",  # high / medium / low
    },
    {
        "release_id": "21",
        "name": "Consumer Price Index",
        "name_ja": "消費者物価指数",
        "date": "2026-02-12",
        "importance": "high",
    },
]
```

## 重要度の定義

```python
RELEASE_IMPORTANCE: dict[str, str] = {
    "10": "high",   # 雇用統計
    "50": "high",   # GDP
    "21": "high",   # CPI
    "53": "high",   # FOMC
    "46": "medium", # PPI
    "328": "medium", # 個人所得
    "83": "low",    # 鉱工業生産
    "120": "medium", # 小売売上高
}
```

## 参照

- [FRED releases/dates API](https://fred.stlouisfed.org/docs/api/fred/releases_dates.html)
- `src/market/fred/fetcher.py`: FREDFetcher（API キー取得方法の参考）

## 受け入れ条件

- [ ] FRED API から発表予定を取得できる
- [ ] MAJOR_RELEASES でフィルタリングできる
- [ ] 指定期間でフィルタリングできる
- [ ] 日本語名が含まれる
- [ ] 重要度が含まれる
- [ ] 発表日でソートされている
