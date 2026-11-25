-- Order-lifecycle funnel: placed -> approved (payment) -> shipped -> delivered -> reviewed.
-- Window functions give the share of the top of the funnel and the step-to-step drop.
SELECT
    stage_order,
    stage,
    orders,
    ROUND(100.0 * orders / FIRST_VALUE(orders) OVER (ORDER BY stage_order), 2) AS pct_of_placed,
    ROUND(100.0 * orders / LAG(orders) OVER (ORDER BY stage_order), 2)        AS pct_of_previous_stage,
    LAG(orders) OVER (ORDER BY stage_order) - orders                          AS dropped_vs_previous
FROM (
    SELECT 1 AS stage_order, '1. Order placed'   AS stage, SUM(s1_placed)    AS orders FROM order_stages
    UNION ALL
    SELECT 2, '2. Payment approved', SUM(s2_approved)  FROM order_stages
    UNION ALL
    SELECT 3, '3. Shipped',          SUM(s3_shipped)   FROM order_stages
    UNION ALL
    SELECT 4, '4. Delivered',        SUM(s4_delivered) FROM order_stages
    UNION ALL
    SELECT 5, '5. Review submitted', SUM(s5_reviewed)  FROM order_stages
)
ORDER BY stage_order;
