-- Initial schema for market database
-- Creates base tables for market data storage

-- Stock/Asset master table
CREATE TABLE IF NOT EXISTS assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL UNIQUE,
    name TEXT,
    asset_type TEXT NOT NULL,  -- 'stock', 'forex', 'index', 'indicator'
    exchange TEXT,
    sector TEXT,
    currency TEXT DEFAULT 'USD',
    source TEXT NOT NULL,  -- 'yfinance', 'fred'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Daily price data
CREATE TABLE IF NOT EXISTS prices_daily (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    date DATE NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    adj_close REAL,
    volume INTEGER,
    source TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, date, source),
    FOREIGN KEY (symbol) REFERENCES assets(symbol)
);

-- Economic indicators (FRED data)
CREATE TABLE IF NOT EXISTS indicators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    date DATE NOT NULL,
    value REAL NOT NULL,
    source TEXT NOT NULL DEFAULT 'fred',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, date, source),
    FOREIGN KEY (symbol) REFERENCES assets(symbol)
);

-- Data fetch history
CREATE TABLE IF NOT EXISTS fetch_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    symbol TEXT NOT NULL,
    start_date DATE,
    end_date DATE,
    row_count INTEGER,
    success INTEGER DEFAULT 1,
    error_message TEXT,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_assets_symbol ON assets(symbol);
CREATE INDEX IF NOT EXISTS idx_assets_type ON assets(asset_type);
CREATE INDEX IF NOT EXISTS idx_assets_source ON assets(source);

CREATE INDEX IF NOT EXISTS idx_prices_symbol ON prices_daily(symbol);
CREATE INDEX IF NOT EXISTS idx_prices_date ON prices_daily(date);
CREATE INDEX IF NOT EXISTS idx_prices_symbol_date ON prices_daily(symbol, date);

CREATE INDEX IF NOT EXISTS idx_indicators_symbol ON indicators(symbol);
CREATE INDEX IF NOT EXISTS idx_indicators_date ON indicators(date);

CREATE INDEX IF NOT EXISTS idx_fetch_source ON fetch_history(source);
CREATE INDEX IF NOT EXISTS idx_fetch_symbol ON fetch_history(symbol);
