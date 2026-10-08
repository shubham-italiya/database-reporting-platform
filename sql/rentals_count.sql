-- Number of rentals matching the same filter as rentals_search.sql (for paging).
SELECT COUNT(*) AS total
FROM rental AS r
JOIN inventory AS i  ON i.inventory_id = r.inventory_id
JOIN film      AS f  ON f.film_id      = i.film_id
JOIN customer  AS cu ON cu.customer_id = r.customer_id
WHERE CAST(:q AS VARCHAR) = ''
   OR LOWER(cu.first_name || ' ' || cu.last_name) LIKE :pattern
   OR LOWER(f.title) LIKE :pattern;
