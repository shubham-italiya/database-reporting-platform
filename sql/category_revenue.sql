-- Revenue per film category in [:start, :end) and its share of the total (window function).
SELECT c.name AS category,
       COUNT(*) AS payments,
       ROUND(CAST(SUM(p.amount) AS NUMERIC), 2) AS revenue,
       ROUND(CAST(SUM(p.amount) / SUM(SUM(p.amount)) OVER () AS NUMERIC), 4) AS share
FROM payment AS p
JOIN rental        AS r  ON r.rental_id    = p.rental_id
JOIN inventory     AS i  ON i.inventory_id = r.inventory_id
JOIN film_category AS fc ON fc.film_id     = i.film_id
JOIN category      AS c  ON c.category_id  = fc.category_id
WHERE p.payment_date >= :start AND p.payment_date < :end
GROUP BY c.name
ORDER BY revenue DESC;
