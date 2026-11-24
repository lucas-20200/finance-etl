import pandas as pd
import numpy as np

# 股票代號與中文名稱對照表，方便前端儀表板直接顯示中文
TICKER_NAME_MAP = {
    "0050.TW": "元大台灣50",
    "2330.TW": "台積電",
    "2317.TW": "鴻海",
    "2454.TW": "聯發科",
    "2308.TW": "台達電",
    "2881.TW": "富邦金",
    "2882.TW": "國泰金",
    "2412.TW": "中華電",
}


def transform_stock_data(raw_df: pd.DataFrame) -> pd.DataFrame:
    """清洗原始股價資料並計算技術指標（對應資料庫 mart 層結構）。

    計算項目：
    1. 去除重複紀錄並依標的與日期排序
    2. 日報酬率 (daily_return_pct)
    3. 5 日與 20 日移動平均線 (ma_5, ma_20)
    4. 成交量日變化率 (volume_change_pct) 與 5 日均量 (vol_ma_5)
    5. 價格四捨五入至小數點後 2 位（符合台股報價習慣）
    """
    if raw_df.empty:
        print("[警告] 輸入的原始資料為空，跳過 Transform 步驟。")
        return pd.DataFrame()

    df = raw_df.copy()

    # 1. 資料品質檢查與去重（確保同一天同一檔股票只有一筆）
    df = df.drop_duplicates(subset=["trade_date", "ticker"], keep="last")
    df = df.dropna(subset=["open_price", "high_price", "low_price", "close_price"])

    # 2. 確保依照「股票代號」與「交易日期升冪」排序，rolling 與 pct_change 才會正確
    df = df.sort_values(by=["ticker", "trade_date"]).reset_index(drop=True)

    # 3. 加上股票中文名稱
    df["stock_name"] = df["ticker"].map(TICKER_NAME_MAP).fillna(df["ticker"])

    # 4. 依各檔股票分組計算技術指標
    grouped = df.groupby("ticker", group_keys=False)

    # 日報酬率 (%) = (今日收盤 - 昨日收盤) / 昨日收盤 * 100
    df["daily_return_pct"] = grouped["close_price"].pct_change() * 100

    # 5 日均線 & 20 日均線
    df["ma_5"] = grouped["close_price"].transform(lambda s: s.rolling(window=5).mean())
    df["ma_20"] = grouped["close_price"].transform(lambda s: s.rolling(window=20).mean())

    # 成交量變化率 (%) 與 5 日均量
    df["volume_change_pct"] = grouped["volume"].pct_change() * 100
    df["vol_ma_5"] = grouped["volume"].transform(lambda s: s.rolling(window=5).mean())

    # 處理因前一日成交量為 0 可能產生的無限大 (inf)
    df["volume_change_pct"] = df["volume_change_pct"].replace([np.inf, -np.inf], np.nan)

    # 5. 數值精度整理（保留小數點後 2 位）
    price_cols = [
        "open_price",
        "high_price",
        "low_price",
        "close_price",
        "adj_close_price",
        "daily_return_pct",
        "ma_5",
        "ma_20",
        "volume_change_pct",
    ]
    for col in price_cols:
        df[col] = df[col].round(2)

    df["vol_ma_5"] = df["vol_ma_5"].round(0)

    # 6. 整理輸出欄位順序
    mart_cols = [
        "trade_date",
        "ticker",
        "stock_name",
        "open_price",
        "high_price",
        "low_price",
        "close_price",
        "volume",
        "daily_return_pct",
        "ma_5",
        "ma_20",
        "vol_ma_5",
        "volume_change_pct",
    ]
    return df[mart_cols]


if __name__ == "__main__":
    from datetime import datetime, timedelta
    from src.extract import TARGET_TICKERS, fetch_stock_data

    end_dt = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    start_dt = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")

    raw_df = fetch_stock_data(TARGET_TICKERS, start_dt, end_dt)
    mart_df = transform_stock_data(raw_df)

    print("\n--- Transform 結果摘要（台積電 2330.TW 最近 5 個交易日）---")
    tsmc = mart_df[mart_df["ticker"] == "2330.TW"].tail(5)
    print(tsmc.to_string(index=False))