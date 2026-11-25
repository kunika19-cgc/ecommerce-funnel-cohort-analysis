WITH per_customer AS (
    SELECT customer_unique_id, COUNT(*) AS n_orders
    FROM order_stages
    WHERE order_status NOT IN ('canceled', 'unavailable')
    GROUP BY customer_unique_id
)
SELECT
    COUNT(*)                                          AS customers,
    SUM(CASE WHEN n_orders > 1 THEN 1 ELSE 0 END)     AS repeat_customers,
    ROUND(100.0 * SUM(CASE WHEN n_orders > 1 THEN 1 ELSE 0 END) / COUNT(*), 2) AS repeat_rate_pct
FROM per_customer;
