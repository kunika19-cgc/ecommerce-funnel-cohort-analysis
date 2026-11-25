-- Monthly cohort retention.
-- Cohort = month of a customer's FIRST order. We use customer_unique_id
-- (customer_id changes on every order in this dataset).
WITH purchases AS (
    SELECT customer_unique_id, purchase_month
    FROM order_stages
    WHERE order_status NOT IN ('canceled', 'unavailable')
),
first_purchase AS (
    SELECT customer_unique_id, MIN(purchase_month) AS cohort_month
    FROM purchases
    GROUP BY customer_unique_id
),
activity AS (
    SELECT DISTINCT
        p.customer_unique_id,
        f.cohort_month,
        (CAST(substr(p.purchase_month, 1, 4) AS INTEGER) - CAST(substr(f.cohort_month, 1, 4) AS INTEGER)) * 12
      + (CAST(substr(p.purchase_month, 6, 2) AS INTEGER) - CAST(substr(f.cohort_month, 6, 2) AS INTEGER)) AS month_number
    FROM purchases p
    JOIN first_purchase f USING (customer_unique_id)
),
cohort_size AS (
    SELECT cohort_month, COUNT(*) AS cohort_size
    FROM first_purchase
    GROUP BY cohort_month
)
SELECT
    a.cohort_month,
    a.month_number,
    COUNT(DISTINCT a.customer_unique_id)                                  AS active_customers,
    s.cohort_size,
    ROUND(100.0 * COUNT(DISTINCT a.customer_unique_id) / s.cohort_size, 2) AS retention_pct
FROM activity a
JOIN cohort_size s USING (cohort_month)
GROUP BY a.cohort_month, a.month_number
ORDER BY a.cohort_month, a.month_number;
