-- Payments and rentals per day in [:start, :end), for charts.
SELECT d.day,
       COALESCE(p.revenue, 0) AS revenue,
       COALESCE(r.rentals, 0) AS rentals
FROM (SELECT date(payment_date) AS day FROM payment WHERE payment_date >= :start AND payment_date < :end
      UNION
      SELECT date(rental_date)  AS day FROM rental  WHERE rental_date  >= :start AND rental_date  < :end) AS d
LEFT JOIN (SELECT date(payment_date) AS day, ROUND(CAST(SUM(amount) AS NUMERIC), 2) AS revenue
           FROM payment WHERE payment_date >= :start AND payment_date < :end
           GROUP BY date(payment_date)) AS p ON p.day = d.day
LEFT JOIN (SELECT date(rental_date) AS day, COUNT(*) AS rentals
           FROM rental WHERE rental_date >= :start AND rental_date < :end
           GROUP BY date(rental_date)) AS r ON r.day = d.day
ORDER BY d.day;
