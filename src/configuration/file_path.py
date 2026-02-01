from dataclasses import dataclass
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    """アプリケーション設定を管理するクラス"""

    # Quants Project Directories
    quants_dir: Path
    src_dir: Path
    notebook_dir: Path

    # Data directories
    data_dir: Path

    # GEQ
    geq_dir: Path
    geq_list_dir: Path
    geq_list_origin_dir: Path

    # FACTSET
    factset_root_dir: Path
    factset_financials_dir: Path
    factset_index_constituents_dir: Path

    # BPM
    bpm_root_dir: Path
    bpm_data_dir: Path
    bpm_src_dir: Path

    # BLOOMBERG
    bloomberg_root_dir: Path
    bloomberg_data_dir: Path
    bloomberg_price_dir: Path

    # FRED
    fred_dir: Path

    # TSA
    tsa_dir: Path

    # log
    log_dir: Path

    # --- API ---
    # FRED
    fred_api_key: str

    # --- Configurations ---
    # FRED SERIES ID
    fred_series_id_json: str

    @classmethod
    def from_env(cls, env_path: Path | None = None) -> "Config":
        """環境変数から設定を読み込む"""
        load_dotenv(env_path)

        # 必須環境変数のリスト
        required_vars = [
            # Quants Project
            "QUANTS_DIR",
            "SRC_DIR",
            "NOTEBOOK_DIR",
            # Data
            "DATA_DIR",
            # GEQ
            "GEQ_DIR",
            "GEQ_LIST_DIR",
            "GEQ_LIST_ORIGIN_DIR",
            # FACTSET
            "FACTSET_ROOT_DIR",
            "FACTSET_FINANCIALS_DIR",
            "FACTSET_INDEX_CONSTITUENTS_DIR",
            # BPM
            "BPM_ROOT_DIR",
            "BPM_DATA_DIR",
            "BPM_SRC_DIR",
            # BLOOMBERG
            "BLOOMBERG_ROOT_DIR",
            "BLOOMBERG_DATA_DIR",
            "BLOOMBERG_PRICE_DIR",
            # FRED
            "FRED_DIR",
            # TSA
            "TSA_DIR",
            # log
            "LOG_DIR",
            # --- API ---
            # FRED
            "FRED_API_KEY",
            # --- Configurations ---
            # FRED SERIES
            "FRED_SERIES_ID_JSON",
        ]

        # 環境変数の存在チェック
        missing = [var for var in required_vars if not os.environ.get(var)]

        if missing:
            raise ValueError(
                "必須の環境変数が未設定です:\n"
                + "\n".join(f"  - {var}" for var in missing)
            )

        return cls(
            # Quants Project
            quants_dir=Path(os.environ["QUANTS_DIR"]),
            src_dir=Path(os.environ["SRC_DIR"]),
            notebook_dir=Path(os.environ["NOTEBOOK_DIR"]),
            # Data
            data_dir=Path(os.environ["DATA_DIR"]),
            # GEQ
            geq_dir=Path(os.environ["GEQ_DIR"]),
            geq_list_dir=Path(os.environ["GEQ_LIST_DIR"]),
            geq_list_origin_dir=Path(os.environ["GEQ_LIST_ORIGIN_DIR"]),
            # FACTSET
            factset_root_dir=Path(os.environ["FACTSET_ROOT_DIR"]),
            factset_financials_dir=Path(os.environ["FACTSET_FINANCIALS_DIR"]),
            factset_index_constituents_dir=Path(
                os.environ["FACTSET_INDEX_CONSTITUENTS_DIR"]
            ),
            # BPM
            bpm_root_dir=Path(os.environ["BPM_ROOT_DIR"]),
            bpm_data_dir=Path(os.environ["BPM_DATA_DIR"]),
            bpm_src_dir=Path(os.environ["BPM_SRC_DIR"]),
            # BLOOMBERG
            bloomberg_root_dir=Path(os.environ["BLOOMBERG_ROOT_DIR"]),
            bloomberg_data_dir=Path(os.environ["BLOOMBERG_DATA_DIR"]),
            bloomberg_price_dir=Path(os.environ["BLOOMBERG_PRICE_DIR"]),
            # FRED
            fred_dir=Path(os.environ["FRED_DIR"]),
            # TSA
            tsa_dir=Path(os.environ["TSA_DIR"]),
            # log
            log_dir=Path(os.environ["LOG_DIR"]),
            # --- API ---
            # FRED
            fred_api_key=os.environ["FRED_API_KEY"],
            # --- Configurations ---
            # FRED SERIES
            fred_series_id_json=os.environ["FRED_SERIES_ID_JSON"],
        )
