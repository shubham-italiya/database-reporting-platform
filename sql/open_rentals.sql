-- Rentals still out at :as_of (taken before it, not returned by then). Overdue is worked out in Python
-- from rental_duration, because date arithmetic differs between SQLite and PostgreSQL.
SELECT r.rental_id,
       r.rental_date,
       f.title,
       f.rental_duration,
       cu.first_name || ' ' || cu.last_name AS customer,
       cu.email,
       i.store_id
FROM rental AS r
JOIN inventory AS i  ON i.inventory_id = r.inventory_id
JOIN film      AS f  ON f.film_id      = i.film_id
JOIN customer  AS cu ON cu.customer_id = r.customer_id
WHERE r.rental_date < :as_of
  AND (r.return_date IS NULL OR r.return_date >= :as_of)
ORDER BY r.rental_date;
