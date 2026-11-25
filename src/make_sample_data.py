"""
Generate a SMALL SYNTHETIC dataset with the same file names/columns as the
Olist Brazilian E-Commerce dataset.

!! This is ONLY for testing that the pipeline runs end-to-end. !!
!! Never quote numbers from it. Use the real Olist data for results. !!
"""
from pathlib import Path
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
OUT = Path(__file__).resolve().parents[1] / "data" / "sample"
OUT.mkdir(parents=True, exist_ok=True)

N_CUSTOMERS = 6000
START, END = pd.Timestamp("2017-01-01"), pd.Timestamp("2018-08-31")
SPAN = (END - START).days
STATES = ["SP", "RJ", "MG", "RS", "PR", "SC", "BA", "DF"]
FMT = "%Y-%m-%d %H:%M:%S"


def hexid(n):
    return [f"{x:032x}" for x in rng.integers(0, 2**62, size=n, dtype=np.int64)]


# ---- who orders when ------------------------------------------------------
unique_ids = hexid(N_CUSTOMERS)
states = rng.choice(STATES, N_CUSTOMERS, p=[.4, .15, .12, .1, .08, .06, .05, .04])
n_orders = rng.choice([1, 2, 3], N_CUSTOMERS, p=[0.94, 0.05, 0.01])

rows = []
for uid, st, k in zip(unique_ids, states, n_orders):
    t = START + pd.Timedelta(days=int(rng.integers(0, SPAN)))
    for j in range(k):
        if j:
            t += pd.Timedelta(days=int(rng.integers(20, 200)))
        if t > END:
            break
        rows.append((uid, st, t + pd.Timedelta(seconds=int(rng.integers(0, 86400)))))

n = len(rows)
order_ids = hexid(n)
customer_ids = hexid(n)  # Olist: a new customer_id for every order

customers = pd.DataFrame({
    "customer_id": customer_ids,
    "customer_unique_id": [r[0] for r in rows],
    "customer_zip_code_prefix": rng.integers(1000, 99999, n),
    "customer_city": "city",
    "customer_state": [r[1] for r in rows],
})

# ---- order lifecycle ------------------------------------------------------
status = rng.choice(["delivered", "canceled", "shipped", "unavailable", "processing"],
                    n, p=[.955, .015, .015, .005, .01])
purchase = pd.Series([r[2] for r in rows])
approved = purchase + pd.to_timedelta(rng.integers(1, 48, n), unit="h")
carrier = approved + pd.to_timedelta(rng.integers(1, 5, n), unit="D")
delivered = carrier + pd.to_timedelta(rng.integers(3, 20, n), unit="D")
estimated = purchase + pd.to_timedelta(rng.integers(15, 30, n), unit="D")

approved = approved.where(~np.isin(status, ["canceled"]) | (rng.random(n) < .5))
carrier = carrier.where(np.isin(status, ["delivered", "shipped"]))
delivered_c = delivered.where(status == "delivered")

orders = pd.DataFrame({
    "order_id": order_ids,
    "customer_id": customer_ids,
    "order_status": status,
    "order_purchase_timestamp": purchase.dt.strftime(FMT),
    "order_approved_at": approved.dt.strftime(FMT),
    "order_delivered_carrier_date": carrier.dt.strftime(FMT),
    "order_delivered_customer_date": delivered_c.dt.strftime(FMT),
    "order_estimated_delivery_date": estimated.dt.strftime(FMT),
})

# ---- payments / items -----------------------------------------------------
value = np.round(rng.lognormal(4.6, 0.7, n), 2)
payments = pd.DataFrame({
    "order_id": order_ids,
    "payment_sequential": 1,
    "payment_type": rng.choice(["credit_card", "boleto", "voucher", "debit_card"], n, p=[.74, .19, .05, .02]),
    "payment_installments": rng.integers(1, 10, n),
    "payment_value": value,
})
items = pd.DataFrame({
    "order_id": order_ids,
    "order_item_id": 1,
    "product_id": hexid(n),
    "seller_id": hexid(n),
    "shipping_limit_date": (approved + pd.Timedelta(days=3)).dt.strftime(FMT),
    "price": np.round(value * 0.85, 2),
    "freight_value": np.round(value * 0.15, 2),
})

# ---- reviews: late deliveries get lower scores ----------------------------
is_late = (delivered_c > estimated).fillna(False).to_numpy()
has_review = (status == "delivered") & (rng.random(n) < 0.92)
score = np.where(is_late,
                 rng.choice([1, 2, 3, 4, 5], n, p=[.35, .15, .15, .15, .2]),
                 rng.choice([1, 2, 3, 4, 5], n, p=[.04, .03, .08, .25, .6]))
reviews = pd.DataFrame({
    "review_id": hexid(n),
    "order_id": order_ids,
    "review_score": score,
    "review_comment_title": "",
    "review_comment_message": "",
    "review_creation_date": delivered_c.dt.strftime(FMT),
    "review_answer_timestamp": delivered_c.dt.strftime(FMT),
})[has_review]

files = {
    "olist_orders_dataset.csv": orders,
    "olist_customers_dataset.csv": customers,
    "olist_order_payments_dataset.csv": payments,
    "olist_order_items_dataset.csv": items,
    "olist_order_reviews_dataset.csv": reviews,
}
for name, df in files.items():
    df.to_csv(OUT / name, index=False)
print(f"SYNTHETIC sample written to {OUT} ({n} orders). For pipeline testing only.")
