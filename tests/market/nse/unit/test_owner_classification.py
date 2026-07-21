"""Unit tests for market.nse.analysis.owner_classification module.

NSE の株主構成集計値から owner_flag を導出する ``classify_owner_flag`` の
テストスイート。

Tier 1 の自然人 promoter 判定は **株主数ベース** (``hufi_num >= 1``) である。
保有比率 (``hufi_pct``) は小数第2位で丸められるため、持株会社経由で支配する
一族が個人名義で名目的な株数のみ保有する場合に 0.00% となり、比率ベースでは
「自然人 promoter 不在」と誤読される（実例: INOXGREEN は自然人3名で計500株、
発行済4.01億株に対し hufi_pct=0.00%）。

Test TODO List:
- [x] classify_owner_flag(): hufi_num>=1 かつ dir/kmp あり → individual_and_director
- [x] classify_owner_flag(): hufi_pct が丸めで0でも hufi_num>=1 なら individual_and_director
- [x] classify_owner_flag(): hufi_num==0 かつ dir/kmp あり → director_only
- [x] classify_owner_flag(): hufi_num>=1 かつ dir/kmp なし → individual
- [x] classify_owner_flag(): hufi_pct<0.5 かつ dir/kmp なし → individual_passive
- [x] classify_owner_flag(): 自然人なし + nri あり → probable_nri_family
- [x] classify_owner_flag(): 自然人なし + govt>=50 → excluded_state_dominant
- [x] classify_owner_flag(): 自然人なし + 保有なし → excluded_no_natural_no_holding
- [x] classify_owner_flag(): 自然人なし + 外資優勢 → ambiguous_holding_foreign
- [x] classify_owner_flag(): 自然人なし + 国内優勢 → ambiguous_holding_indian
- [x] derive_owner_flag_final(): owner_confirmed_* / owner_probable_* → OWNER
- [x] derive_owner_flag_final(): excluded_* → NOT_OWNER
- [x] derive_owner_flag_final(): ambiguous_* → OWNER_WEAK
"""

import pytest

from market.nse.analysis.owner_classification import (
    classify_owner_flag,
    derive_owner_flag_final,
)


def _composition(**overrides: float) -> dict[str, float]:
    """全項目 0 のベース構成に overrides を適用したキーワード引数を返す。"""
    base: dict[str, float] = {
        "hufi_num": 0,
        "hufi_pct": 0.0,
        "nri_pct": 0.0,
        "dir_pct": 0.0,
        "kmp_pct": 0.0,
        "natural_pct_sum": 0.0,
        "govt_pct": 0.0,
        "other_indian_pct": 0.0,
        "other_foreign_pct": 0.0,
        "foreign_non_govt_pct": 0.0,
    }
    base.update(overrides)
    return base


class TestClassifyOwnerFlag:
    """classify_owner_flag() 関数のテスト。"""

    def test_正常系_自然人と役員がいる場合はindividual_and_director(self) -> None:
        """hufi_num>=1 かつ dir/kmp 保有ありなら individual_and_director。"""
        result = classify_owner_flag(
            **_composition(hufi_num=3, hufi_pct=25.0, dir_pct=1.5, natural_pct_sum=26.5)
        )

        assert result == "owner_confirmed_individual_and_director"

    def test_正常系_hufi_pctが丸めで0でも株主数があればindividual_and_director(
        self,
    ) -> None:
        """持株会社経由支配で hufi_pct=0.00 でも自然人の存在を認識すること。

        INOXGREEN の実データ（自然人3名・計500株、kmp_pct=0.03）を再現する。
        """
        result = classify_owner_flag(
            **_composition(hufi_num=3, hufi_pct=0.0, kmp_pct=0.03, natural_pct_sum=0.03)
        )

        assert result == "owner_confirmed_individual_and_director"

    def test_正常系_自然人がおらず役員のみならdirector_only(self) -> None:
        """hufi_num==0 かつ dir/kmp 保有ありなら director_only。"""
        result = classify_owner_flag(
            **_composition(hufi_num=0, kmp_pct=0.01, natural_pct_sum=0.01)
        )

        assert result == "owner_confirmed_director_only"

    def test_正常系_自然人のみで実質保有ありならindividual(self) -> None:
        """dir/kmp なし・hufi_pct>=0.5 なら individual。"""
        result = classify_owner_flag(
            **_composition(hufi_num=2, hufi_pct=45.0, natural_pct_sum=45.0)
        )

        assert result == "owner_confirmed_individual"

    def test_エッジケース_自然人の保有が微小ならindividual_passive(self) -> None:
        """hufi_pct<0.5 かつ dir/kmp なしなら individual_passive。"""
        result = classify_owner_flag(
            **_composition(hufi_num=1, hufi_pct=0.2, natural_pct_sum=0.2)
        )

        assert result == "owner_confirmed_individual_passive"

    def test_正常系_自然人なしでnri保有ありならprobable_nri_family(self) -> None:
        """hufi_num==0・dir/kmp なし・nri 保有ありなら probable_nri_family。"""
        result = classify_owner_flag(**_composition(nri_pct=30.0, natural_pct_sum=30.0))

        assert result == "owner_probable_nri_family"

    def test_正常系_政府保有が過半なら除外(self) -> None:
        """自然人 promoter がおらず govt_pct>=50 なら excluded_state_dominant。"""
        result = classify_owner_flag(**_composition(govt_pct=51.0))

        assert result == "excluded_state_dominant"

    def test_エッジケース_自然人も法人保有もなければ除外(self) -> None:
        """promoter 保有が一切ない場合は excluded_no_natural_no_holding。"""
        result = classify_owner_flag(**_composition())

        assert result == "excluded_no_natural_no_holding"

    def test_正常系_外資保有が国内を上回る場合はambiguous_holding_foreign(self) -> None:
        """自然人なしで外資保有優勢なら ambiguous_holding_foreign。"""
        result = classify_owner_flag(
            **_composition(other_indian_pct=10.0, other_foreign_pct=45.0)
        )

        assert result == "ambiguous_holding_foreign"

    def test_正常系_国内法人保有優勢ならambiguous_holding_indian(self) -> None:
        """自然人なしで国内法人保有優勢なら ambiguous_holding_indian。"""
        result = classify_owner_flag(
            **_composition(other_indian_pct=60.0, other_foreign_pct=5.0)
        )

        assert result == "ambiguous_holding_indian"


class TestDeriveOwnerFlagFinal:
    """derive_owner_flag_final() 関数のテスト。"""

    @pytest.mark.parametrize(
        "flag",
        [
            "owner_confirmed_individual_and_director",
            "owner_confirmed_director_only",
            "owner_probable_nri_family",
        ],
    )
    def test_正常系_owner_confirmedとowner_probableはOWNER(self, flag: str) -> None:
        """owner_confirmed_* / owner_probable_* は OWNER に集約されること。"""
        assert derive_owner_flag_final(flag) == "OWNER"

    @pytest.mark.parametrize(
        "flag", ["excluded_state_dominant", "excluded_no_natural_no_holding"]
    )
    def test_正常系_excludedはNOT_OWNER(self, flag: str) -> None:
        """excluded_* は NOT_OWNER に集約されること。"""
        assert derive_owner_flag_final(flag) == "NOT_OWNER"

    @pytest.mark.parametrize(
        "flag", ["ambiguous_holding_indian", "ambiguous_mnc_jv_candidate"]
    )
    def test_正常系_ambiguousはOWNER_WEAK(self, flag: str) -> None:
        """ambiguous_* は OWNER_WEAK に集約されること。"""
        assert derive_owner_flag_final(flag) == "OWNER_WEAK"
