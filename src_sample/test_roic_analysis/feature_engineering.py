from typing import List

import numpy as np
import pandas as pd


class FactorEngineer:
    def __init__(self):
        pass

    def calculate_wacc(
        self,
        df: pd.DataFrame,
        rf: float = 0.04,
        erp: float = 0.05,
        tax_rate: float = 0.25,
    ) -> pd.DataFrame:
        """
        Calculate WACC (Weighted Average Cost of Capital).
        WACC = Ke * (E/V) + Kd * (D/V) * (1 - t)
        Ke = Rf + Beta * ERP
        """
        # Check if necessary columns exist
        required_cols = ["Total_Debt", "Total_Equity"]
        if not all(col in df.columns for col in required_cols):
            print(
                f"Missing columns for WACC calculation: {set(required_cols) - set(df.columns)}"
            )
            return df

        # Assume Beta is 1.0 if not present
        beta = df["Beta"] if "Beta" in df.columns else 1.0

        # Cost of Equity
        ke = rf + beta * erp

        # Cost of Debt (Simplified: Interest Expense / Total Debt, or assumed rate if missing)
        # Here we assume a fixed spread over Rf for simplicity if Interest_Expense is missing
        kd = (
            df["Interest_Expense"] / df["Total_Debt"]
            if "Interest_Expense" in df.columns
            else rf + 0.02
        )

        total_capital = df["Total_Debt"] + df["Total_Equity"]
        weight_equity = df["Total_Equity"] / total_capital
        weight_debt = df["Total_Debt"] / total_capital

        df["WACC"] = ke * weight_equity + kd * weight_debt * (1 - tax_rate)
        return df

    def calculate_economic_profit(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Economic Profit (EVA).
        EP = (ROIC - WACC) * Invested Capital
        """
        if (
            "ROIC" in df.columns
            and "WACC" in df.columns
            and "Invested_Capital" in df.columns
        ):
            df["Economic_Profit"] = (df["ROIC"] - df["WACC"]) * df["Invested_Capital"]
        else:
            print("Missing columns for Economic Profit calculation.")
        return df

    def calculate_incremental_roic(
        self, df: pd.DataFrame, periods: List[int] = [1, 3, 5]
    ) -> pd.DataFrame:
        """
        Calculate Incremental ROIC (iROIC).
        iROIC = Delta NOPAT / Delta Invested Capital
        """
        required_cols = ["NOPAT", "Invested_Capital", "P_SYMBOL"]
        if not all(col in df.columns for col in required_cols):
            print("Missing columns for iROIC calculation.")
            return df

        df.sort_values(["P_SYMBOL", "date"], inplace=True)

        for n in periods:
            # Assuming annual data or adjusting for frequency.
            # If monthly data, n years = n * 12 months.
            # Here we assume the input dataframe might be monthly but we want n-year changes.
            # Let's assume 'date' allows us to find n-year lag.
            # For simplicity, using shift assuming sorted and regular intervals (e.g. monthly)
            lag = n * 12

            delta_nopat = df.groupby("P_SYMBOL")["NOPAT"].diff(lag)
            delta_ic = df.groupby("P_SYMBOL")["Invested_Capital"].diff(lag)

            df[f"iROIC_{n}Y"] = delta_nopat / delta_ic

        return df

    def decompose_dupont(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        DuPont Decomposition of ROIC.
        ROIC = NOPAT Margin * Asset Turnover (Sales / Invested Capital)
        """
        if (
            "NOPAT" in df.columns
            and "Sales" in df.columns
            and "Invested_Capital" in df.columns
        ):
            df["NOPAT_Margin"] = df["NOPAT"] / df["Sales"]
            df["Invested_Capital_Turnover"] = df["Sales"] / df["Invested_Capital"]
        return df

    def add_roic_rank_cols(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add rank columns for ROIC.
        """
        if "ROIC" in df.columns:
            df["ROIC_Rank"] = df.groupby("date")["ROIC"].transform(
                lambda x: pd.qcut(x, 5, labels=False, duplicates="drop") + 1
            )
        return df

    def capitalize_intangibles(
        self, df: pd.DataFrame, amortization_years: int = 5
    ) -> pd.DataFrame:
        """
        Capitalize R&D expenses.
        Adjusted IC = IC + Capitalized R&D
        Adjusted NOPAT = NOPAT + R&D Expense - Amortization
        """
        if "RD_Expense" not in df.columns:
            return df

        # Simplified capitalization: Accumulate last N years of R&D
        # This requires historical data.
        # For this implementation, we'll use a rolling sum if data is sufficient.

        df.sort_values(["P_SYMBOL", "date"], inplace=True)

        # Rolling sum of R&D over amortization period (approximate capitalization)
        # Assuming monthly data, window = amortization_years * 12
        window = amortization_years * 12

        df["Rnd_Capital"] = df.groupby("P_SYMBOL")["RD_Expense"].transform(
            lambda x: x.rolling(window=window, min_periods=1).sum()
        )

        # Amortization (Simplified: Rnd_Capital / amortization_years)
        # Or more accurately, average of past R&D.
        # Let's assume straight line: Amortization ~ Rnd_Capital / amortization_years
        # Note: This is a rough proxy.
        amortization = df["Rnd_Capital"] / amortization_years

        if "Invested_Capital" in df.columns:
            df["Invested_Capital_Adj"] = df["Invested_Capital"] + df["Rnd_Capital"]

        if "NOPAT" in df.columns:
            df["NOPAT_Adj"] = df["NOPAT"] + df["RD_Expense"] - amortization

        if "Invested_Capital_Adj" in df.columns and "NOPAT_Adj" in df.columns:
            df["ROIC_Adj"] = df["NOPAT_Adj"] / df["Invested_Capital_Adj"]

        return df


# Helper functions can remain as standalone or static methods
def clipped_mean(series: pd.Series, percentile: float = 5.0) -> float:
    lower_bound = np.percentile(series, percentile)
    upper_bound = np.percentile(series, 100 - percentile)
    return np.clip(series, lower_bound, upper_bound).mean()
