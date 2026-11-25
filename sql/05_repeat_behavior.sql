-- Window functions: order sequence number per customer and days between orders.
WITH ranked AS (
    SELECT
        customer_unique_id,
        order_purchase_timestamp AS ts,
        ROW_NUMBER() OVER (PARTITION BY customer_unique_id ORDER BY order_purchase_timestamp) AS order_number
    FROM order_stages
    WHERE order_status NOT IN ('canceled', 'unavailable')
),
gaps AS (
    SELECT
        customer_unique_id,
        order_number,
        julianday(ts) - julianday(LAG(ts) OVER (PARTITION BY customer_unique_id ORDER BY ts)) AS days_since_prev
    FROM ranked
)
SELECT
    order_number,
    COUNT(*)                         AS orders,
    ROUND(AVG(days_since_prev), 1)   AS avg_days_since_previous_order
FROM gaps
GROUP BY order_number
ORDER BY order_number;
