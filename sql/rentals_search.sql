-- One page of rentals, newest first, optionally filtered by customer name or film title.
-- :q is the lower-case search text ('' = no filter); :pattern is '%' || :q || '%'.
SELECT r.rental_id,
       r.rental_date,
       r.return_date,
       cu.first_name || ' ' || cu.last_name AS customer,
       f.title,
       i.store_id,
       p.amount
FROM rental AS r
JOIN inventory AS i  ON i.inventory_id = r.inventory_id
JOIN film      AS f  ON f.film_id      = i.film_id
JOIN customer  AS cu ON cu.customer_id = r.customer_id
LEFT JOIN payment AS p ON p.rental_id = r.rental_id
WHERE CAST(:q AS VARCHAR) = ''
   OR LOWER(cu.first_name || ' ' || cu.last_name) LIKE :pattern
   OR LOWER(f.title) LIKE :pattern
ORDER BY r.rental_date DESC, r.rental_id DESC
LIMIT :limit OFFSET :offset;
