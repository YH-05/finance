-- Market_Data.db Schema

CREATE TABLE IF NOT EXISTS price_history (
    ticker TEXT NOT NULL,
    date TEXT NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume INTEGER,
    PRIMARY KEY (ticker, date)
);

CREATE INDEX IF NOT EXISTS idx_price_date ON price_history (date);

CREATE TABLE IF NOT EXISTS macro_history (
    series_id TEXT NOT NULL,
    date TEXT NOT NULL,
    value REAL,
    PRIMARY KEY (series_id, date)
);

CREATE INDEX IF NOT EXISTS idx_macro_date ON macro_history (date);

-- Valuation_History.db Schema

CREATE TABLE IF NOT EXISTS valuation_snapshot (
    date TEXT NOT NULL,
    ticker TEXT NOT NULL,
    forward_pe REAL,
    trailing_pe REAL,
    peg_ratio REAL,
    price_to_book REAL,
    enterprise_value REAL,
    enterprise_to_ebitda REAL,
    profit_margins REAL,
    PRIMARY KEY (date, ticker)
);

CREATE INDEX IF NOT EXISTS idx_valuation_ticker ON valuation_snapshot (ticker);
