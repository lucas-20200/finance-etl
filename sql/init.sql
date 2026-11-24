CREATE SCHEMA IF NOT EXISTS ods;
CREATE SCHEMA IF NOT EXISTS dm;

CREATE TABLE IF NOT EXISTS ods.stock_daily_prices (
    trade_date DATE NOT NULL,
    ticker VARCHAR(20) NOT NULL,
    open_price NUMERIC(12, 4),
    high_price NUMERIC(12, 4),
    low_price NUMERIC(12, 4),
    close_price NUMERIC(12, 4),
    adj_close_price NUMERIC(12, 4),
    volume BIGINT,
    extracted_at TIMESTAMP,
    PRIMARY KEY (trade_date, ticker)
);

CREATE TABLE IF NOT EXISTS dm.stock_daily_metrics (
    trade_date DATE NOT NULL,
    ticker VARCHAR(20) NOT NULL,
    stock_name VARCHAR(50),
    open_price NUMERIC(12, 2),
    high_price NUMERIC(12, 2),
    low_price NUMERIC(12, 2),
    close_price NUMERIC(12, 2),
    volume BIGINT,
    daily_return_pct NUMERIC(8, 2),
    ma_5 NUMERIC(12, 2),
    ma_20 NUMERIC(12, 2),
    vol_ma_5 BIGINT,
    volume_change_pct NUMERIC(10, 2),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (trade_date, ticker)
);
