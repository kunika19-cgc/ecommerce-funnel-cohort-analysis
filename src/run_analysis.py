"""
Run the whole analysis:
    python src/run_analysis.py            # uses data/raw  (real Olist data)
    python src/run_analysis.py --sample   # uses data/sample (SYNTHETIC, test only)

Outputs: outputs/tables/*.csv, outputs/charts/*.png, outputs/insights.md
"""
import argparse
import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from load_data import build_db

ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = ROOT / "sql"
OUT = ROOT / "outputs"
TABLES_DIR, CHARTS_DIR = OUT / "tables", OUT / "charts"

QUERIES = {
    "funnel": "01_funnel.sql",
    "funnel_by_month": "02_funnel_by_month.sql",
    "delivery_vs_review": "03_delivery_vs_review.sql",
    "cohort_retention": "04_cohort_retention.sql",
    "repeat_behavior": "05_repeat_behavior.sql",
    "repeat_rate": "06_repeat_rate.sql",
    "monthly_kpis": "07_monthly_kpis.sql",
}


def run_sql(con, name):
    return pd.read_sql_query((SQL_DIR / name).read_text(), con)


# ----------------------------------------------------------------- charts
def chart_funnel(df):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.barh(df["stage"][::-1], df["orders"][::-1], color="#1F3A5F")
    for i, (v, p) in enumerate(zip(df["orders"][::-1], df["pct_of_placed"][::-1])):
        ax.text(v, i, f"  {v:,.0f} ({p:.1f}%)", va="center", fontsize=9)
    ax.set_title("Order lifecycle funnel")
    ax.set_xlabel("Orders")
    ax.set_xlim(0, df["orders"].max() * 1.25)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "funnel.png", dpi=150)
    plt.close(fig)


def chart_cohort(df, max_months=12):
    pivot = df.pivot(index="cohort_month", columns="month_number", values="retention_pct")
    pivot = pivot[[c for c in pivot.columns if c <= max_months]]
    later = pivot.drop(columns=0, errors="ignore")
    vmax = np.nanmax(later.values) if later.size and not np.all(np.isnan(later.values)) else 1
    fig, ax = plt.subplots(figsize=(11, 7))
    im = ax.imshow(later.values, aspect="auto", cmap="Blues", vmin=0, vmax=vmax)
    ax.set_xticks(range(later.shape[1]), later.columns)
    ax.set_yticks(range(later.shape[0]), later.index)
    ax.set_xlabel("Months since first purchase")
    ax.set_ylabel("Cohort (first purchase month)")
    ax.set_title("Monthly cohort retention (%) - month 0 excluded")
    for i in range(later.shape[0]):
        for j in range(later.shape[1]):
            v = later.values[i, j]
            if not np.isnan(v):
                ax.text(j, i, f"{v:.1f}", ha="center", va="center", fontsize=7,
                        color="white" if v > vmax * 0.6 else "black")
    fig.colorbar(im, ax=ax, label="% of cohort")
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "cohort_retention_heatmap.png", dpi=150)
    plt.close(fig)


def chart_kpis(df):
    fig, ax1 = plt.subplots(figsize=(10, 4.5))
    ax1.bar(df["purchase_month"], df["revenue"], color="#9DB4D1")
    ax1.set_ylabel("Revenue")
    ax1.tick_params(axis="x", rotation=90, labelsize=7)
    ax2 = ax1.twinx()
    ax2.plot(df["purchase_month"], df["aov"], color="#C0392B", marker="o", ms=3)
    ax2.set_ylabel("AOV")
    ax1.set_title("Monthly revenue and average order value")
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "monthly_revenue_aov.png", dpi=150)
    plt.close(fig)


def chart_delivery(df):
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.bar(df["delivery_outcome"], df["avg_review_score"], color=["#C0392B", "#1F3A5F"])
    for i, v in enumerate(df["avg_review_score"]):
        ax.text(i, v, f"{v:.2f}", ha="center", va="bottom")
    ax.set_ylim(0, 5)
    ax.set_ylabel("Average review score")
    ax.set_title("Review score: on-time vs late delivery")
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "delivery_vs_review.png", dpi=150)
    plt.close(fig)


# --------------------------------------------------------------- insights
def write_insights(res, source):
    f, rr = res["funnel"], res["repeat_rate"].iloc[0]
    drops = f.dropna(subset=["dropped_vs_previous"])
    worst = drops.loc[drops["pct_of_previous_stage"].idxmin()]
    d = res["delivery_vs_review"].set_index("delivery_outcome")
    coh = res["cohort_retention"]
    m1 = coh[coh["month_number"] == 1]
    m1_avg = (m1["active_customers"].sum() / m1["cohort_size"].sum() * 100) if len(m1) else float("nan")
    k = res["monthly_kpis"]

    lines = [f"# Auto-generated insights\n", f"_Data source: **{source}**_\n"]
    if source != "real Olist data":
        lines.append("> WARNING: synthetic data - do NOT quote these numbers anywhere.\n")
    lines += [
        "## Funnel",
        f"- {int(f['orders'].iloc[0]):,} orders placed; {f['pct_of_placed'].iloc[-1]:.1f}% reach a review.",
        f"- Biggest step drop: **{worst['stage']}** keeps only {worst['pct_of_previous_stage']:.1f}% "
        f"of the previous stage ({int(worst['dropped_vs_previous']):,} orders lost).",
        "",
        "## Delivery and satisfaction",
    ]
    if {"On time", "Late"} <= set(d.index):
        lines.append(
            f"- On-time orders average {d.loc['On time','avg_review_score']:.2f} stars vs "
            f"{d.loc['Late','avg_review_score']:.2f} for late orders "
            f"({d.loc['Late','pct_low_reviews']:.1f}% of late orders get a 1-2 star review).")
    lines += [
        "",
        "## Retention",
        f"- {rr['repeat_customers']:,.0f} of {rr['customers']:,.0f} customers "
        f"({rr['repeat_rate_pct']:.2f}%) ordered more than once.",
        f"- Average month-1 retention across cohorts: {m1_avg:.2f}%.",
        "",
        "## Revenue",
        f"- Total revenue {k['revenue'].sum():,.0f}; average AOV {k['revenue'].sum()/k['orders'].sum():,.2f}.",
        f"- Best month: {k.loc[k['revenue'].idxmax(),'purchase_month']} "
        f"({k['revenue'].max():,.0f}).",
    ]
    (OUT / "insights.md").write_text("\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", action="store_true", help="use synthetic data (testing only)")
    args = ap.parse_args()

    data_dir = ROOT / "data" / ("sample" if args.sample else "raw")
    source = "SYNTHETIC sample" if args.sample else "real Olist data"
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)

    db_path = OUT / "olist.db"
    print(f"Loading {source} ...")
    build_db(data_dir, db_path)

    con = sqlite3.connect(db_path)
    con.executescript((SQL_DIR / "00_views.sql").read_text())
    res = {}
    for key, fname in QUERIES.items():
        res[key] = run_sql(con, fname)
        res[key].to_csv(TABLES_DIR / f"{key}.csv", index=False)
        print(f"  ran {fname:<28} -> {len(res[key])} rows")
    con.close()

    chart_funnel(res["funnel"])
    chart_cohort(res["cohort_retention"])
    chart_kpis(res["monthly_kpis"])
    chart_delivery(res["delivery_vs_review"])
    write_insights(res, source)
    print(f"\nDone. See {OUT}/")


if __name__ == "__main__":
    main()
