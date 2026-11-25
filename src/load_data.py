"""Load the Olist CSV files into a local SQLite database."""
from pathlib import Path
import sqlite3
import pandas as pd

TABLES = {
    "orders": "olist_orders_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "order_payments": "olist_order_payments_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "order_reviews": "olist_order_reviews_dataset.csv",
}


def build_db(data_dir: Path, db_path: Path) -> None:
    missing = [f for f in TABLES.values() if not (data_dir / f).exists()]
    if missing:
        raise FileNotFoundError(
            f"Missing files in {data_dir}: {missing}\n"
            "Download the Olist dataset from Kaggle (olistbr/brazilian-ecommerce) "
            "and unzip the CSVs into data/raw/."
        )
    if db_path.exists():
        db_path.unlink()
    con = sqlite3.connect(db_path)
    for table, fname in TABLES.items():
        df = pd.read_csv(data_dir / fname)
        df.to_sql(table, con, index=False)
        print(f"  loaded {table:<15} {len(df):>8,} rows")
    con.close()
