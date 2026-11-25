-- Funnel conversion by purchase month: is the drop-off getting better or worse?
SELECT
    purchase_month,
    COUNT(*)                                          AS orders_placed,
    ROUND(100.0 * SUM(s2_approved)  / COUNT(*), 2)    AS approved_pct,
    ROUND(100.0 * SUM(s3_shipped)   / COUNT(*), 2)    AS shipped_pct,
    ROUND(100.0 * SUM(s4_delivered) / COUNT(*), 2)    AS delivered_pct,
    ROUND(100.0 * SUM(s5_reviewed)  / COUNT(*), 2)    AS reviewed_pct
FROM order_stages
GROUP BY purchase_month
ORDER BY purchase_month;
