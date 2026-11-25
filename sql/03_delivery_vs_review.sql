-- Does late delivery hurt customer satisfaction?
SELECT
    CASE WHEN o.order_delivered_customer_date <= o.order_estimated_delivery_date
         THEN 'On time' ELSE 'Late' END     AS delivery_outcome,
    COUNT(*)                                AS orders,
    ROUND(AVG(r.score), 2)                  AS avg_review_score,
    ROUND(100.0 * SUM(CASE WHEN r.score <= 2 THEN 1 ELSE 0 END) / COUNT(*), 2) AS pct_low_reviews
FROM orders o
JOIN order_review_score r ON r.order_id = o.order_id
WHERE o.order_delivered_customer_date IS NOT NULL
GROUP BY delivery_outcome;
