-- Monthly orders, revenue, AOV and month-over-month revenue growth.
WITH m AS (
    SELECT
        s.purchase_month,
        COUNT(*)                   AS orders,
        ROUND(SUM(r.revenue), 2)   AS revenue
    FROM order_stages s
    JOIN order_revenue r ON r.order_id = s.order_id
    WHERE s.order_status NOT IN ('canceled', 'unavailable')
    GROUP BY s.purchase_month
)
SELECT
    purchase_month,
    orders,
    revenue,
    ROUND(revenue * 1.0 / orders, 2) AS aov,
    ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY purchase_month))
          / LAG(revenue) OVER (ORDER BY purchase_month), 2) AS revenue_mom_pct
FROM m
ORDER BY purchase_month;
