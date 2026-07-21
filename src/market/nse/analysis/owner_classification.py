"""Owner-flag classification rule for the NSE owner-company screening pipeline.

NSE の XBRL 株主構成開示から集計した promoter 構成値をもとに、
``owner_flag`` (12 種) と ``owner_flag_final`` (OWNER / OWNER_WEAK / NOT_OWNER)
を導出する。

本モジュールは判定ルールの唯一の実装である。従来は
``persist_incremental.py`` / ``persist_rev1_missing.py`` /
``persist_and_classify.py`` の3スクリプトに同じロジックが複製されており、
さらに ``nse_owner_analysis.ipynb`` が異なる判定式を持っていたため、
同一データでも「どの経路で処理されたか」によって結果が変わる状態にあった
(実例: INOXGREEN が再取得を機に OWNER → OWNER_WEAK へ反転)。

Tier 1 の自然人 promoter 判定は **株主数ベース** (``hufi_num >= 1``) とする。
インドの支配的な promoter 構造は持株会社ピラミッドであり、一族は holdco 経由で
支配して個人名義は名目的な株数にとどまる。``hufi_pct`` は小数第2位で丸められる
ため、この構造では 0.00% となり、比率ベースでは「自然人不在」と誤読される。

See Also
--------
notebook/NSE/docs/owner_labeling_methodology.md : 判定ルールの仕様書。
"""

from __future__ import annotations

from utils_core.logging import get_logger

logger = get_logger(__name__)

GOVT_DOMINANT_PCT = 50.0
"""政府保有がこの比率以上なら state-dominant として除外する閾値。"""

MINOR_HUFI_PCT = 0.5
"""自然人 promoter の保有をパッシブとみなす上限比率。"""


def classify_owner_flag(
    *,
    hufi_num: int,
    hufi_pct: float,
    nri_pct: float,
    dir_pct: float,
    kmp_pct: float,
    natural_pct_sum: float,
    govt_pct: float,
    other_indian_pct: float,
    other_foreign_pct: float,
    foreign_non_govt_pct: float,
) -> str:
    """promoter 構成値から ``owner_flag`` を導出する.

    Parameters
    ----------
    hufi_num : int
        ``IndividualsOrHinduUndividedFamily`` の株主数。Tier 1 の自然人
        promoter 判定はこの値で行う（比率ではない点に注意）。
    hufi_pct : float
        同カテゴリの保有比率。パッシブ判定 (``< 0.5``) にのみ使う。
    nri_pct : float
        ``NonResidentIndividualsOrForeignIndividuals`` の保有比率。
    dir_pct : float
        ``DirectorsAndDirectorsRelatives`` の保有比率。
    kmp_pct : float
        ``KeyManagerialPersonnel`` の保有比率。
    natural_pct_sum : float
        自然人系カテゴリ (hufi + nri + dir + kmp + rel) の保有比率合計。
    govt_pct : float
        政府系カテゴリの保有比率合計。
    other_indian_pct : float
        ``OtherIndianShareholders`` の保有比率。
    other_foreign_pct : float
        ``OtherForeignShareholders`` の保有比率。
    foreign_non_govt_pct : float
        外国機関投資家系の保有比率。

    Returns
    -------
    str
        ``owner_confirmed_*`` / ``owner_probable_*`` / ``ambiguous_*`` /
        ``excluded_*`` のいずれか。

    Examples
    --------
    >>> classify_owner_flag(
    ...     hufi_num=3,
    ...     hufi_pct=0.0,
    ...     nri_pct=0.0,
    ...     dir_pct=0.0,
    ...     kmp_pct=0.03,
    ...     natural_pct_sum=0.03,
    ...     govt_pct=0.0,
    ...     other_indian_pct=56.12,
    ...     other_foreign_pct=0.0,
    ...     foreign_non_govt_pct=0.0,
    ... )
    'owner_confirmed_individual_and_director'
    """
    has_natural = natural_pct_sum > 0

    if has_natural:
        if dir_pct > 0 or kmp_pct > 0:
            # 自然人 promoter の「存在」は株主数で判定する。保有比率は丸めで
            # 0.00% になりうるため、比率で判定すると holdco 経由で支配する
            # 一族を取りこぼす。
            if hufi_num >= 1:
                return "owner_confirmed_individual_and_director"
            return "owner_confirmed_director_only"
        if hufi_num >= 1:
            if hufi_pct < MINOR_HUFI_PCT and dir_pct == 0 and kmp_pct == 0:
                return "owner_confirmed_individual_passive"
            return "owner_confirmed_individual"
        if nri_pct > 0:
            return "owner_probable_nri_family"
        return "owner_probable_relatives_trust"

    if govt_pct >= GOVT_DOMINANT_PCT:
        return "excluded_state_dominant"
    if other_indian_pct == 0 and other_foreign_pct == 0 and foreign_non_govt_pct == 0:
        return "excluded_no_natural_no_holding"
    if other_foreign_pct + foreign_non_govt_pct > other_indian_pct:
        return "ambiguous_holding_foreign"
    if other_indian_pct > 0:
        return "ambiguous_holding_indian"
    return "ambiguous_mnc_jv_candidate"


def derive_owner_flag_final(owner_flag: str) -> str:
    """``owner_flag`` を3値の ``owner_flag_final`` に集約する.

    Parameters
    ----------
    owner_flag : str
        :func:`classify_owner_flag` が返すフラグ。

    Returns
    -------
    str
        ``OWNER`` / ``NOT_OWNER`` / ``OWNER_WEAK`` のいずれか。

    Examples
    --------
    >>> derive_owner_flag_final("owner_confirmed_director_only")
    'OWNER'
    >>> derive_owner_flag_final("excluded_state_dominant")
    'NOT_OWNER'
    >>> derive_owner_flag_final("ambiguous_holding_indian")
    'OWNER_WEAK'
    """
    if owner_flag.startswith(("owner_confirmed", "owner_probable")):
        return "OWNER"
    if owner_flag.startswith("excluded"):
        return "NOT_OWNER"
    return "OWNER_WEAK"


__all__ = [
    "GOVT_DOMINANT_PCT",
    "MINOR_HUFI_PCT",
    "classify_owner_flag",
    "derive_owner_flag_final",
]
