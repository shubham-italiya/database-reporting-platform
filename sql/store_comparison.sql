-- Rentals, customers and revenue per store in [:start, :end).
SELECT s.store_id,
       ci.city,
       COUNT(r.rental_id)            AS rentals,
       COUNT(DISTINCT r.customer_id) AS customers,
       ROUND(CAST(COALESCE(SUM(p.amount), 0) AS NUMERIC), 2) AS revenue
FROM store AS s
JOIN address   AS a  ON a.address_id    = s.address_id
JOIN city      AS ci ON ci.city_id      = a.city_id
LEFT JOIN inventory AS i ON i.store_id  = s.store_id
LEFT JOIN rental    AS r ON r.inventory_id = i.inventory_id AND r.rental_date >= :start AND r.rental_date < :end
LEFT JOIN payment   AS p ON p.rental_id = r.rental_id
GROUP BY s.store_id, ci.city
ORDER BY s.store_id;
