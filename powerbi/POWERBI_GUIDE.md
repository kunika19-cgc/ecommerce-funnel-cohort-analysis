# Power BI dashboard guide

Load these CSVs from `outputs/tables/` (Get Data > Text/CSV): `funnel`, `funnel_by_month`,
`delivery_vs_review`, `cohort_retention`, `monthly_kpis`, `repeat_rate`.

## Page 1 - Executive summary
- Cards: Total Orders, Total Revenue, AOV, Repeat Rate %.
- Line chart: revenue by `purchase_month`. Column chart: orders by month.

## Page 2 - Funnel
- Funnel visual: `stage` vs `orders`.
- Table: `pct_of_previous_stage`, `dropped_vs_previous` (conditional formatting on lowest value).
- Line chart from `funnel_by_month`: approved / shipped / delivered / reviewed % over time.

## Page 3 - Cohort retention
- Matrix: rows = `cohort_month`, columns = `month_number`, values = `retention_pct`
  (Average). Use Background color > Gradient. Filter `month_number` > 0 so month 0 (100%) doesn't dominate.
- Slicer on `cohort_month`.

## Page 4 - Delivery and satisfaction
- Clustered column: `delivery_outcome` vs `avg_review_score`; card for `pct_low_reviews`.

## Page 5 - Insights
- Text box: 4-5 recommendations written from YOUR findings (see `outputs/insights.md`).

## DAX measures
```DAX
Total Orders  = SUM ( monthly_kpis[orders] )
Total Revenue = SUM ( monthly_kpis[revenue] )
AOV           = DIVIDE ( [Total Revenue], [Total Orders] )
Repeat Rate % = AVERAGE ( repeat_rate[repeat_rate_pct] )

Revenue MoM % =
VAR cur  = [Total Revenue]
VAR prev = CALCULATE ( [Total Revenue], PREVIOUSMONTH ( 'Date'[Date] ) )
RETURN DIVIDE ( cur - prev, prev )
```
(For `Revenue MoM %` add a Date table, or just use the `revenue_mom_pct` column from the CSV.)
