-- Days that had at least one rental, newest first.
SELECT date(r.rental_date) AS day, COUNT(*) AS rentals
FROM rental AS r
GROUP BY date(r.rental_date)
ORDER BY day DESC;
