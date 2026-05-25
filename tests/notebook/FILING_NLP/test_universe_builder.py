"""notebook/FILING_NLP/pipeline/universe_builder.py の単体テスト.

3 段フォールバック (Stage1: 完全一致 / Stage2: '/' → '-' 正規化 + all_tickers 突合 /
Stage3: edgar lookup) と build_membership の振る舞いを検証する.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np
import pandas as pd
import pytest

if TYPE_CHECKING:
    from types import ModuleType


def _load_universe_builder() -> ModuleType:
    """notebook/FILING_NLP/pipeline/universe_builder.py をモジュールとしてロード."""
    here = Path(__file__).resolve()
    repo_root = here.parent.parent.parent.parent  # tests/notebook/FILING_NLP/ → repo
    module_path = (
        repo_root / "notebook" / "FILING_NLP" / "pipeline" / "universe_builder.py"
    )
    # parent package を sys.path に通す (相対 import 用)
    pkg_root = str(repo_root)
    if pkg_root not in sys.path:
        sys.path.insert(0, pkg_root)
    spec = importlib.util.spec_from_file_location("_ub_test_module", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def universe_v2_fixture() -> pd.DataFrame:
    """all_tickers が list / ndarray / NaN 混在の universe_v2 風 DataFrame."""
    return pd.DataFrame(
        {
            "cik": [320193, 14693, 1067983, 99999, 88888],
            "cik_str": [
                "0000320193",
                "0000014693",
                "0001067983",
                "0000099999",
                "0000088888",
            ],
            "ticker": ["AAPL", "BF-A", "BRK-A", "MULTI", "OLDNAME"],
            # 様々な dtype を混在させて両対応を検証
            "all_tickers": [
                np.array(["AAPL"], dtype=object),  # ndarray
                ["BF-A", "BF-B"],  # list
                np.array(["BRK-A", "BRK-B"], dtype=object),  # ndarray
                ["MULTI", "MULTI-A", "MULTI-B"],  # list
                None,  # NaN/None ケース
            ],
            "n_tickers": [1, 2, 2, 3, 0],
            "exchange": ["NASDAQ", "NYSE", "NYSE", "NYSE", "NASDAQ"],
            "company": [
                "Apple Inc.",
                "Brown-Forman Corp",
                "Berkshire Hathaway",
                "Multi Ticker Co",
                "Renamed Co",
            ],
        }
    )


@pytest.fixture
def spx_index_tickers() -> pd.DataFrame:
    """Bloomberg JSON 由来の tickers DataFrame (SPX サブセット)."""
    return pd.DataFrame(
        {
            "ticker": ["AAPL", "BF/B", "BRK/B", "MULTI-A", "UNKNOWN_TICKER_XYZ"],
            "isin": ["US0378331005", "US1156372096", "US0846707026", "US999", "US000"],
            "sedol": ["2046251", "2236820", "2073390", "9999999", "0000000"],
            "mkt_cap": [4.5e12, 1.0e11, 8.0e11, 5.0e9, 1.0e8],
            "gics_sector": [
                "Information Technology",
                "Consumer Staples",
                "Financials",
                "Industrials",
                "Other",
            ],
            "gics_industry_group": ["A", "B", "C", "D", "E"],
            "gics_industry": ["A1", "B1", "C1", "D1", "E1"],
            "gics_sub_industry": ["A1a", "B1a", "C1a", "D1a", "E1a"],
            "index_name": ["SPX", "SPX", "SPX", "SPX", "SPX"],
        }
    )


class TestLoadIndexJson:
    def test_正常系_Bloomberg_JSON形式をDataFrameに変換できる(
        self, tmp_path: Path
    ) -> None:
        ub = _load_universe_builder()
        data = [
            {
                "ID": "AAPL US Equity",
                "ticker": "AAPL",
                "ISIN": "US0378331005",
                "SEDOL": "2046251",
                "CUR_MKT_CAP": 4.5e12,
                "GICS_SECTOR_NAME": "Information Technology",
                "GICS_INDUSTRY_GROUP_NAME": "Technology Hardware & Equipment",
                "GICS_INDUSTRY_NAME": "Technology Hardware, Storage & Peripherals",
                "GICS_SUB_INDUSTRY_NAME": "Technology Hardware, Storage & Peripherals",
            },
            {
                "ID": "BF/B US Equity",
                "ticker": "BF/B",
                "ISIN": "US1156372096",
                "SEDOL": "2236820",
                "CUR_MKT_CAP": 1.0e11,
                "GICS_SECTOR_NAME": "Consumer Staples",
                "GICS_INDUSTRY_GROUP_NAME": "Food, Beverage & Tobacco",
                "GICS_INDUSTRY_NAME": "Beverages",
                "GICS_SUB_INDUSTRY_NAME": "Distillers & Vintners",
            },
        ]
        json_path = tmp_path / "2026-05-22_SPX Index.json"
        json_path.write_text(json.dumps(data), encoding="utf-8")

        df = ub.load_index_json(json_path, index_name="SPX")

        assert len(df) == 2
        # 必須列
        for col in (
            "ticker",
            "isin",
            "sedol",
            "mkt_cap",
            "gics_sector",
            "gics_industry_group",
            "gics_industry",
            "gics_sub_industry",
            "index_name",
        ):
            assert col in df.columns, f"missing column: {col}"
        assert (df["index_name"] == "SPX").all()
        assert df.iloc[0]["ticker"] == "AAPL"
        assert df.iloc[1]["ticker"] == "BF/B"


class TestStage1DirectJoin:
    def test_正常系_stage1_ticker完全一致でCIK解決(
        self,
        spx_index_tickers: pd.DataFrame,
        universe_v2_fixture: pd.DataFrame,
    ) -> None:
        ub = _load_universe_builder()
        resolved = ub._stage1_direct_join(spx_index_tickers, universe_v2_fixture)

        # AAPL は完全一致 → 解決される
        aapl = resolved[resolved["ticker"] == "AAPL"]
        assert len(aapl) == 1
        assert int(aapl.iloc[0]["cik"]) == 320193


class TestStage2NormalizedJoin:
    def test_正常系_stage2_スラッシュ正規化でBF_BをBF_Bにマッチ(
        self,
        spx_index_tickers: pd.DataFrame,
        universe_v2_fixture: pd.DataFrame,
    ) -> None:
        ub = _load_universe_builder()
        # Stage1 で未解決のものだけ Stage2 に投げる想定
        unresolved = spx_index_tickers[
            spx_index_tickers["ticker"].isin(["BF/B", "BRK/B"])
        ].copy()
        resolved = ub._stage2_normalized_join(unresolved, universe_v2_fixture)

        # BF/B → BF-B (BF-A の all_tickers に含まれる) で解決
        bfb = resolved[resolved["ticker"] == "BF/B"]
        assert len(bfb) == 1, "BF/B が解決されていない"
        assert int(bfb.iloc[0]["cik"]) == 14693

    def test_正常系_stage2_all_tickers列の複数候補で先頭マッチ(
        self,
        universe_v2_fixture: pd.DataFrame,
    ) -> None:
        ub = _load_universe_builder()
        unresolved = pd.DataFrame(
            {
                "ticker": ["MULTI-B"],
                "isin": ["US999B"],
                "sedol": ["9999998"],
                "mkt_cap": [4.0e9],
                "gics_sector": ["Industrials"],
                "gics_industry_group": ["D"],
                "gics_industry": ["D1"],
                "gics_sub_industry": ["D1a"],
                "index_name": ["SPX"],
            }
        )
        resolved = ub._stage2_normalized_join(unresolved, universe_v2_fixture)
        assert len(resolved) == 1
        assert int(resolved.iloc[0]["cik"]) == 99999


class TestStage3EdgarLookup:
    def test_正常系_stage3_edgar_lookupで残銘柄解決(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        ub = _load_universe_builder()
        unresolved = pd.DataFrame(
            {
                "ticker": ["NEWTICK"],
                "isin": ["US123"],
                "sedol": ["1234567"],
                "mkt_cap": [1.0e10],
                "gics_sector": ["Tech"],
                "gics_industry_group": ["A"],
                "gics_industry": ["A1"],
                "gics_sub_industry": ["A1a"],
                "index_name": ["SPX"],
            }
        )

        # _lookup_cik_via_edgar を monkeypatch
        def fake_lookup(ticker: str) -> int | None:
            mapping = {"NEWTICK": 555555}
            return mapping.get(ticker)

        monkeypatch.setattr(ub, "_lookup_cik_via_edgar", fake_lookup)

        resolved, unresolved_list = ub._stage3_edgar_lookup(unresolved)

        assert len(resolved) == 1
        assert int(resolved.iloc[0]["cik"]) == 555555
        assert unresolved_list == []

    def test_異常系_stage3_NotFound時にunresolved_tickersに記録(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        ub = _load_universe_builder()
        unresolved = pd.DataFrame(
            {
                "ticker": ["NOTFOUND"],
                "isin": ["US000"],
                "sedol": ["0000000"],
                "mkt_cap": [1.0e8],
                "gics_sector": ["Other"],
                "gics_industry_group": ["E"],
                "gics_industry": ["E1"],
                "gics_sub_industry": ["E1a"],
                "index_name": ["SPX"],
            }
        )

        def fake_lookup_none(_ticker: str) -> int | None:
            return None

        monkeypatch.setattr(ub, "_lookup_cik_via_edgar", fake_lookup_none)

        resolved, unresolved_list = ub._stage3_edgar_lookup(unresolved)

        assert len(resolved) == 0
        assert len(unresolved_list) == 1
        assert unresolved_list[0]["ticker"] == "NOTFOUND"
        assert unresolved_list[0]["reason"] in {"not_found", "edgar_not_found"}

    def test_異常系_stage3_Network例外時にtenacityで3回retry(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        ub = _load_universe_builder()
        call_count = {"n": 0}

        class _Net(Exception):
            pass

        def fake_edgar_company(ticker: str) -> Any:
            call_count["n"] += 1
            raise _Net("network error")

        # 内部の edgar.Company 呼び出しを差し替え
        monkeypatch.setattr(ub, "_edgar_company_factory", fake_edgar_company)

        result = ub._lookup_cik_via_edgar("ANYTICKER")
        # tenacity 3 回 retry → 3 回呼ばれて最終的に None
        assert call_count["n"] == 3
        assert result is None


class TestResolveCiksThreeStage:
    def test_正常系_3段統合でhit数が積み上がる(
        self,
        spx_index_tickers: pd.DataFrame,
        universe_v2_fixture: pd.DataFrame,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        ub = _load_universe_builder()

        # Stage3: UNKNOWN_TICKER_XYZ は edgar で解決成功とする
        def fake_lookup(ticker: str) -> int | None:
            return 777777 if ticker == "UNKNOWN_TICKER_XYZ" else None

        monkeypatch.setattr(ub, "_lookup_cik_via_edgar", fake_lookup)

        resolved, unresolved_list = ub.resolve_ciks_three_stage(
            spx_index_tickers, universe_v2_fixture
        )

        # AAPL (s1), BF/B (s2), BRK/B (s2), MULTI-A (s1 or s2), UNKNOWN (s3) → 5/5
        assert len(resolved) == 5
        assert unresolved_list == []
        # cik 列が int 系
        assert pd.api.types.is_integer_dtype(resolved["cik"])


class TestBuildMembership:
    def test_正常系_in_spx_in_sox_in_riy_in_rayフラグ生成(
        self,
    ) -> None:
        ub = _load_universe_builder()
        resolved = pd.DataFrame(
            {
                "cik": [111, 222, 333, 333],
                "ticker": ["A", "B", "C", "C"],
                "isin": ["i1", "i2", "i3", "i3"],
                "sedol": ["s1", "s2", "s3", "s3"],
                "mkt_cap": [1e9, 2e9, 3e9, 3e9],
                "gics_sector": ["X", "Y", "Z", "Z"],
                "gics_industry_group": ["a", "b", "c", "c"],
                "gics_industry": ["a1", "b1", "c1", "c1"],
                "gics_sub_industry": ["a1a", "b1a", "c1a", "c1a"],
                "index_name": ["SPX", "SOX", "RIY", "RAY"],
            }
        )
        mem = ub.build_membership(
            resolved,
            index_names=["SPX", "SOX", "RIY", "RAY"],
            snapshot_date="2026-05-22",
        )

        for col in (
            "cik",
            "in_spx",
            "in_sox",
            "in_riy",
            "in_ray",
            "snapshot_date",
        ):
            assert col in mem.columns

        # 111: SPX only / 222: SOX only / 333: RIY + RAY
        row_111 = mem[mem["cik"] == 111].iloc[0]
        assert bool(row_111["in_spx"]) is True
        assert bool(row_111["in_sox"]) is False
        row_333 = mem[mem["cik"] == 333].iloc[0]
        assert bool(row_333["in_riy"]) is True
        assert bool(row_333["in_ray"]) is True
        assert bool(row_333["in_spx"]) is False
        # snapshot_date 列がセットされている
        assert (mem["snapshot_date"] == "2026-05-22").all()

    def test_正常系_CIKdedup後にmembershipがCIK単位で1行になる(
        self,
    ) -> None:
        ub = _load_universe_builder()
        resolved = pd.DataFrame(
            {
                "cik": [333, 333, 333, 333],
                "ticker": ["C", "C", "C", "C"],
                "isin": ["i3"] * 4,
                "sedol": ["s3"] * 4,
                "mkt_cap": [3e9] * 4,
                "gics_sector": ["Z"] * 4,
                "gics_industry_group": ["c"] * 4,
                "gics_industry": ["c1"] * 4,
                "gics_sub_industry": ["c1a"] * 4,
                "index_name": ["SPX", "SOX", "RIY", "RAY"],
            }
        )
        mem = ub.build_membership(
            resolved,
            index_names=["SPX", "SOX", "RIY", "RAY"],
            snapshot_date="2026-05-22",
        )
        assert len(mem) == 1
        row = mem.iloc[0]
        assert bool(row["in_spx"]) is True
        assert bool(row["in_sox"]) is True
        assert bool(row["in_riy"]) is True
        assert bool(row["in_ray"]) is True

    def test_エッジケース_4インデックスにまたがる銘柄が1行にまとまる(
        self,
    ) -> None:
        ub = _load_universe_builder()
        # AAPL が SPX/SOX/RIY/RAY すべてに入っている想定
        resolved = pd.DataFrame(
            {
                "cik": [320193] * 4 + [14693],
                "ticker": ["AAPL"] * 4 + ["BF-B"],
                "isin": ["US0378331005"] * 4 + ["US1156372096"],
                "sedol": ["2046251"] * 4 + ["2236820"],
                "mkt_cap": [4.5e12] * 4 + [1.0e11],
                "gics_sector": ["Information Technology"] * 4 + ["Consumer Staples"],
                "gics_industry_group": ["A"] * 4 + ["B"],
                "gics_industry": ["A1"] * 4 + ["B1"],
                "gics_sub_industry": ["A1a"] * 4 + ["B1a"],
                "index_name": ["SPX", "SOX", "RIY", "RAY", "SPX"],
            }
        )
        mem = ub.build_membership(
            resolved,
            index_names=["SPX", "SOX", "RIY", "RAY"],
            snapshot_date="2026-05-22",
        )
        assert len(mem) == 2
        aapl = mem[mem["cik"] == 320193].iloc[0]
        assert all(bool(aapl[c]) for c in ("in_spx", "in_sox", "in_riy", "in_ray"))
        bfb = mem[mem["cik"] == 14693].iloc[0]
        assert bool(bfb["in_spx"]) is True
        assert bool(bfb["in_sox"]) is False
