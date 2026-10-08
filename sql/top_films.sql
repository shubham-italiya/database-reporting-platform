-- Most rented films in [:start, :end), with a rank (ties share a rank).
SELECT RANK() OVER (ORDER BY COUNT(*) DESC) AS place,
       f.title,
       c.name   AS category,
       COUNT(*) AS rentals
FROM rental AS r
JOIN inventory     AS i  ON i.inventory_id = r.inventory_id
JOIN film          AS f  ON f.film_id      = i.film_id
JOIN film_category AS fc ON fc.film_id     = f.film_id
JOIN category      AS c  ON c.category_id  = fc.category_id
WHERE r.rental_date >= :start AND r.rental_date < :end
GROUP BY f.film_id, f.title, c.name
ORDER BY rentals DESC, f.title
LIMIT :limit;
