"""Owner-flag classification rule for the NSE owner-company screening pipeline.

NSE の XBRL 株主構成開示から集計した promoter 構成値をもとに、
``owner_flag`` (12 種) と ``owner_flag_final`` (OWNER / OWNER_WEAK / NOT_OWNER)
を導出する。

本モジュールは判定ルールの唯一の実装である。従来は
``nse_owner_analysis.ipynb`` と ``persist_*.py`` 系スクリプト3本に別々の実装が
存在し、同一データでも「どの経路で処理されたか」によって結果が変わっていた
(実例: INOXGREEN が再取得を機に OWNER → OWNER_WEAK へ反転)。

**判定軸は原則として株主数 (``*_num``) である。** 保有比率は小数第2位で丸め
られるため、持株会社ピラミッドで支配するインドの典型的な promoter 構造では
一族の個人名義が 0.00% となり、比率で判定すると存在を取りこぼす
(実例: INOXGREEN は自然人3名で計500株、発行済4.01億株に対し hufi_pct=0.00%)。
保有比率は閾値判定 (promoter 総計・政府保有・外資保有・微少個人) にのみ使う。

本ルールは rev1 手動ラベル 425 銘柄に対する実測で選定した。
Precision 99.0% / Recall 96.7% / F1 97.9% (TP 411 / FP 4 / FN 14) であり、
株主数を使わない比率ベース実装 (F1 96.4%) より高精度である。

See Also
--------
notebook/NSE/docs/owner_labeling_methodology.md : 判定ルールの仕様書。
"""

from __future__ import annotations

from utils_core.logging import get_logger

logger = get_logger(__name__)

MIN_PROMOTER_PCT = 10.0
"""promoter 総保有がこの比率未満なら低 promoter として除外する閾値。

根拠: SEBI SAST 2011 Regulation 3 の支配的取得閾値 (dec-2026-04-16-002)。
"""

GOVT_DOMINANT_PCT = 10.0
"""政府保有がこの比率以上なら state-dominant として除外する閾値 (PSU 除外)。"""

MAX_FOREIGN_NON_GOVT_PCT = 50.0
"""外国機関投資家の保有がこの比率以上なら MNC-JV 候補として扱う境界。"""

MINOR_HUFI_PCT = 0.5
"""自然人 promoter の保有をこの比率未満なら微少とみなす境界。"""

MIN_HOLDING_PCT = 10.0
"""自然人 promoter 不在時に holding 経由型とみなす法人保有の下限。"""

NATURAL_SUBS = (
    "IndividualsOrHinduUndividedFamily",
    "NonResidentIndividualsOrForeignIndividuals",
    "DirectorsAndDirectorsRelatives",
    "KeyManagerialPersonnel",
    "RelativesOfPromotersOtherThanPromoterGroup",
    "TrustsWhereAnyPersonBelongingToPromoterAndPromoterGroupIsisTrusteeOrBeneficiaryOrAuthorOfTrust",
)
"""自然人 promoter とみなす XBRL sub_category。"""

GOVT_COMPONENT_SUBS = (
    "CentralGovernmentOrPresidentOfIndia",
    "StateGovernmentsOrGovernors",
    "ShareholdingByCompaniesOrBodiesCorporatewhereCentralOrStateGovernmentIsPromoter",
    "ForeignGovernment",
    "CentralGovernmentOrStateGovernmentS",
)
"""政府系の内訳を表す XBRL sub_category。"""

GOVT_ROLLUP_SUBS = ("Governments", "Goverments")
"""政府系の合計を表す XBRL sub_category。

:data:`GOVT_COMPONENT_SUBS` の合計行であり、内訳と同時に開示されることがある。
``Goverments`` は NSE 側の綴り誤りだが実データに出現するため含める。
"""

FOREIGN_NON_GOVT_SUBS = (
    "ForeignInstitutions",
    "ForeignPortfolioInvestor",
    "OtherForeignShareholders",
)
"""外資（非政府）とみなす XBRL sub_category。

``OtherForeignShareholders`` は海外親会社が promoter として直接保有する枠であり、
MNC 判定の主要シグナルとなるため必ず含める。これを外すと Saint-Gobain のような
海外親会社の支配を検出できない (実例: GRINDWELL は Saint-Gobain 系2社が 51.33% を
``OtherForeignShareholders`` で保有しており、除外すると Owner と誤判定される)。
"""


def compute_govt_pct(component_pct: float, rollup_pct: float) -> float:
    """政府系保有比率を内訳と合計行から算出する.

    XBRL は政府系保有を内訳 (:data:`GOVT_COMPONENT_SUBS`) と合計
    (:data:`GOVT_ROLLUP_SUBS`) の両方で開示することがあり、単純に足すと二重計上
    になる。逆に一方しか開示されない銘柄もあるため、大きい方を採用する。

    Parameters
    ----------
    component_pct : float
        :data:`GOVT_COMPONENT_SUBS` の保有比率合計。
    rollup_pct : float
        :data:`GOVT_ROLLUP_SUBS` の保有比率合計。

    Returns
    -------
    float
        政府系保有比率。

    Examples
    --------
    内訳と合計の両方が開示されるケース (TORNTPOWER 相当)。単純加算だと 16.70%
    となり誤って state-dominant 判定されるが、本関数は 8.35% を返す:

    >>> compute_govt_pct(8.35, 8.35)
    8.35

    合計行のみが開示されるケース (GSFC 相当):

    >>> compute_govt_pct(0.0, 5.65)
    5.65
    """
    return max(component_pct, rollup_pct)


def classify_owner_flag(
    *,
    promoter_total_pct: float,
    hufi_num: int,
    hufi_pct: float,
    nri_num: int,
    dir_num: int,
    kmp_num: int,
    rel_num: int,
    trust_num: int,
    natural_num_sum: int,
    govt_pct: float,
    other_indian_pct: float,
    other_foreign_pct: float,
    foreign_non_govt_pct: float,
) -> str:
    """promoter 構成値から ``owner_flag`` を導出する.

    Parameters
    ----------
    promoter_total_pct : float
        promoter 総保有比率。
    hufi_num : int
        ``IndividualsOrHinduUndividedFamily`` の株主数。Tier 1 の主判定軸。
    hufi_pct : float
        同カテゴリの保有比率。微少個人の判定にのみ使う。
    nri_num : int
        ``NonResidentIndividualsOrForeignIndividuals`` の株主数。
    dir_num : int
        ``DirectorsAndDirectorsRelatives`` の株主数。
    kmp_num : int
        ``KeyManagerialPersonnel`` の株主数。
    rel_num : int
        ``RelativesOfPromotersOtherThanPromoterGroup`` の株主数。
    trust_num : int
        promoter 関連信託の株主数。
    natural_num_sum : int
        自然人系カテゴリの株主数合計。
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
    自然人 promoter が名目的な株数のみ保有する持株会社型 (INOXGREEN 相当):

    >>> classify_owner_flag(
    ...     promoter_total_pct=56.12,
    ...     hufi_num=3,
    ...     hufi_pct=0.0,
    ...     nri_num=0,
    ...     dir_num=0,
    ...     kmp_num=1,
    ...     rel_num=0,
    ...     trust_num=0,
    ...     natural_num_sum=4,
    ...     govt_pct=0.0,
    ...     other_indian_pct=56.12,
    ...     other_foreign_pct=0.0,
    ...     foreign_non_govt_pct=0.0,
    ... )
    'owner_confirmed_individual_and_director'
    """
    has_dir_or_kmp = dir_num >= 1 or kmp_num >= 1
    foreign_ok = foreign_non_govt_pct < MAX_FOREIGN_NON_GOVT_PCT

    # Tier 4: 先に除外条件を判定する
    if promoter_total_pct < MIN_PROMOTER_PCT:
        return "excluded_low_promoter"
    if govt_pct >= GOVT_DOMINANT_PCT:
        return "excluded_state_dominant"

    # Tier 1: 自然人 promoter の存在を株主数で確認する
    if hufi_num >= 1 and has_dir_or_kmp and foreign_ok:
        return "owner_confirmed_individual_and_director"
    if hufi_num >= 1 and foreign_ok:
        return "owner_confirmed_individual"
    if has_dir_or_kmp and hufi_num == 0 and nri_num == 0 and foreign_ok:
        return "owner_confirmed_director_only"

    # Tier 3: 外資優勢な MNC-JV 候補
    if hufi_num >= 1 and not foreign_ok:
        return "ambiguous_mnc_jv_candidate"

    # Tier 3: 自然人の保有が微少
    if hufi_num >= 1 and hufi_pct < MINOR_HUFI_PCT and dir_num == 0 and kmp_num == 0:
        return "ambiguous_minor_individual"

    # Tier 2: 海外個人・親族信託のみ
    if nri_num >= 1 and hufi_num == 0:
        return "owner_probable_nri_family"
    if (
        (rel_num >= 1 or trust_num >= 1)
        and hufi_num == 0
        and nri_num == 0
        and not has_dir_or_kmp
    ):
        return "owner_probable_relatives_trust"

    # Tier 3: 自然人不在の holding 経由型
    if natural_num_sum == 0 and other_indian_pct >= MIN_HOLDING_PCT:
        return "ambiguous_holding_indian"
    if natural_num_sum == 0 and other_foreign_pct >= MIN_HOLDING_PCT:
        return "ambiguous_holding_foreign"

    return "excluded_no_natural_no_holding"


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
        ``ambiguous_*`` は後段の AI レビュー対象として ``OWNER_WEAK`` に置く。

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
    "FOREIGN_NON_GOVT_SUBS",
    "GOVT_COMPONENT_SUBS",
    "GOVT_DOMINANT_PCT",
    "GOVT_ROLLUP_SUBS",
    "MAX_FOREIGN_NON_GOVT_PCT",
    "MINOR_HUFI_PCT",
    "MIN_HOLDING_PCT",
    "MIN_PROMOTER_PCT",
    "NATURAL_SUBS",
    "classify_owner_flag",
    "compute_govt_pct",
    "derive_owner_flag_final",
]
