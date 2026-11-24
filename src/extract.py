from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf

# 精選具代表性的台股大型權值股與 ETF（上市股票代號後綴 .TW）
TARGET_TICKERS = [
    "0050.TW",  # 元大台灣50
    "2330.TW",  # 台積電
    "2317.TW",  # 鴻海
    "2454.TW",  # 聯發科
    "2308.TW",  # 台達電
    "2881.TW",  # 富邦金
    "2882.TW",  # 國泰金
    "2412.TW",  # 中華電
]


def fetch_stock_data(
    tickers: list[str], start_date: str, end_date: str
) -> pd.DataFrame:
    """使用 yfinance 批次下載指定日期區間的台股日線行情。"""
    print(f"正在批次抓取 {len(tickers)} 檔標的 ({start_date} ~ {end_date})...")
    extracted_at = datetime.now()

    try:
        # 一次傳入整個 list，合併連線請求並依股票代號分組
        raw_data = yf.download(
            tickers=tickers,
            start=start_date,
            end=end_date,
            group_by="ticker",
            progress=False,
            auto_adjust=False,
            threads=False,  # 關閉多執行緒併發，降低被 Yahoo 擋連線的機率
        )
    except Exception as e:
        print(f"[錯誤] 批次抓取失敗: {e}")
        return pd.DataFrame()

    if raw_data.empty:
        print("[略過] 此區間無任何交易資料（可能為休市日）。")
        return pd.DataFrame()

    all_records = []

    for ticker in tickers:
        # 確認該檔股票有在回傳結果中
        if ticker not in raw_data.columns.get_level_values(0):
            print(f"  [略過] {ticker} 無交易資料。")
            continue

        df = raw_data[ticker].copy()
        df.columns.name = None

        # 移除全為空值的列（例如某檔股票當天停牌）
        df = df.dropna(how="all")
        if df.empty:
            continue

        df = df.reset_index()
        df = df.rename(
            columns={
                "Date": "trade_date",
                "Open": "open_price",
                "High": "high_price",
                "Low": "low_price",
                "Close": "close_price",
                "Adj Close": "adj_close_price",
                "Volume": "volume",
            }
        )

        df["ticker"] = ticker
        df["extracted_at"] = extracted_at

        cols = [
            "trade_date",
            "ticker",
            "open_price",
            "high_price",
            "low_price",
            "close_price",
            "adj_close_price",
            "volume",
            "extracted_at",
        ]
        all_records.append(df[cols])

    if not all_records:
        return pd.DataFrame()

    result_df = pd.concat(all_records, ignore_index=True)
    result_df["trade_date"] = pd.to_datetime(result_df["trade_date"]).dt.date
    return result_df


if __name__ == "__main__":
    end_dt = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    start_dt = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")

    raw_df = fetch_stock_data(TARGET_TICKERS, start_dt, end_dt)

    print("\n--- 抓取結果摘要 ---")
    print(f"總筆數: {len(raw_df)}")
    if not raw_df.empty:
        print(f"成功抓取標的 ({raw_df['ticker'].nunique()} 檔): {raw_df['ticker'].unique().tolist()}")
        print(raw_df.head(5))