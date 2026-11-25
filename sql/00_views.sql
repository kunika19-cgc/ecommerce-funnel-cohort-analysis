-- Helper views (SQLite). Revenue/review are aggregated per order first
-- so that joins never multiply rows (a classic fan-out bug).

DROP VIEW IF EXISTS order_revenue;
CREATE VIEW order_revenue AS
SELECT order_id, SUM(payment_value) AS revenue
FROM order_payments
GROUP BY order_id;

DROP VIEW IF EXISTS order_review_score;
CREATE VIEW order_review_score AS
SELECT order_id, AVG(review_score) AS score
FROM order_reviews
GROUP BY order_id;

-- One row per order with a 0/1 flag for every lifecycle stage.
DROP VIEW IF EXISTS order_stages;
CREATE VIEW order_stages AS
SELECT
    o.order_id,
    c.customer_unique_id,
    c.customer_state,
    o.order_status,
    o.order_purchase_timestamp,
    strftime('%Y-%m', o.order_purchase_timestamp)                      AS purchase_month,
    1                                                                   AS s1_placed,
    CASE WHEN o.order_approved_at            IS NOT NULL THEN 1 ELSE 0 END AS s2_approved,
    CASE WHEN o.order_delivered_carrier_date IS NOT NULL THEN 1 ELSE 0 END AS s3_shipped,
    CASE WHEN o.order_delivered_customer_date IS NOT NULL THEN 1 ELSE 0 END AS s4_delivered,
    CASE WHEN o.order_delivered_customer_date IS NOT NULL
          AND r.order_id IS NOT NULL THEN 1 ELSE 0 END                  AS s5_reviewed
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id
LEFT JOIN order_review_score r ON r.order_id = o.order_id;
