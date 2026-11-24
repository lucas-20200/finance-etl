import math
import os
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine, MetaData, Table, text
from sqlalchemy.dialects.postgresql import insert

load_dotenv()


def get_db_engine():
    """建立 PostgreSQL SQLAlchemy 連線引擎。"""
    user = os.getenv("POSTGRES_USER", "etl_user")
    password = os.getenv("POSTGRES_PASSWORD", "etl_password123")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "finance_db")

    db_url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
    return create_engine(db_url)


def _clean_nan_to_none(records: list[dict]) -> list[dict]:
    """將字典清單中的 float('nan') 徹底轉換為 SQL 相容的 None (NULL)。"""
    cleaned = []
    for row in records:
        cleaned_row = {
            k: (None if isinstance(v, float) and math.isnan(v) else v)
            for k, v in row.items()
        }
        cleaned.append(cleaned_row)
    return cleaned


def _upsert_dataframe(engine, df: pd.DataFrame, schema: str, table_name: str, conflict_cols: list[str]):
    """通用 PostgreSQL Upsert 函式（遇到主鍵衝突時自動更新該列數據）。"""
    if df.empty:
        print(f"[略過] {schema}.{table_name} 無資料可寫入。")
        return

    metadata = MetaData(schema=schema)
    target_table = Table(table_name, metadata, autoload_with=engine)

    raw_records = df.to_dict(orient="records")
    records = _clean_nan_to_none(raw_records)

    with engine.begin() as conn:
        stmt = insert(target_table).values(records)
        update_dict = {
            col.name: stmt.excluded[col.name]
            for col in target_table.columns
            if col.name not in conflict_cols and col.name != "updated_at"
        }
        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=conflict_cols,
            set_=update_dict,
        )
        conn.execute(upsert_stmt)

    print(f"[成功] 已寫入/更新 {len(records)} 筆資料至 {schema}.{table_name}")


def load_to_postgres(ods_df: pd.DataFrame, dm_df: pd.DataFrame):
    """將 ODS 與 DM 兩層資料寫入 PostgreSQL。"""
    engine = get_db_engine()
    _upsert_dataframe(engine, ods_df, "ods", "stock_daily_prices", ["trade_date", "ticker"])
    _upsert_dataframe(engine, dm_df, "dm", "stock_daily_metrics", ["trade_date", "ticker"])


if __name__ == "__main__":
    from datetime import datetime, timedelta
    from src.extract import TARGET_TICKERS, fetch_stock_data
    from src.transform import transform_stock_data

    end_dt = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    start_dt = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")

    ods_df = fetch_stock_data(TARGET_TICKERS, start_dt, end_dt)
    dm_df = transform_stock_data(ods_df)
    load_to_postgres(ods_df, dm_df)

    engine = get_db_engine()
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT trade_date, ticker, stock_name, close_price, ma_5, ma_20 FROM dm.stock_daily_metrics WHERE ticker = '2330.TW' ORDER BY trade_date DESC LIMIT 3;")
        )
        print("\n--- 資料庫驗證查詢（dm.stock_daily_metrics）---")
        for row in result:
            print(row)