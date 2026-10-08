-- Headline numbers for the period [:start, :end).
SELECT
    (SELECT COUNT(*)                    FROM rental  WHERE rental_date  >= :start AND rental_date  < :end) AS rentals,
    (SELECT COUNT(DISTINCT customer_id) FROM rental  WHERE rental_date  >= :start AND rental_date  < :end) AS active_customers,
    (SELECT COUNT(*)                    FROM rental  WHERE return_date  >= :start AND return_date  < :end) AS returns,
    (SELECT COALESCE(ROUND(CAST(SUM(amount) AS NUMERIC), 2), 0)
                                        FROM payment WHERE payment_date >= :start AND payment_date < :end) AS revenue;
