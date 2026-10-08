# Database Reporting Platform

[![CI](https://github.com/shubham-italiya/database-reporting-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/shubham-italiya/database-reporting-platform/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![SQLite | PostgreSQL](https://img.shields.io/badge/database-SQLite%20%7C%20PostgreSQL-336791)
![License](https://img.shields.io/badge/license-MIT-green)

Connects to a relational database, shows the records and KPIs in a **web dashboard**, and produces an
**automated daily report** (HTML email + CSV files). All numbers come from **plain SQL files** - joins,
aggregates and window functions - and the same queries run on **SQLite and PostgreSQL** (both tested in CI).

The data is **Sakila**, the classic sample database of a DVD-rental business: 16 tables, 16,044 rentals,
16,049 payments, 599 customers, two stores.

![Dashboard](docs/dashboard.png)

## What it does

- **Dashboard** (`python -m reportkit serve`): pick a day and see rentals, revenue, active customers, returns and
  revenue per rental, each compared with the average of the previous 7 trading days; a 30-day revenue/rentals chart;
  a store comparison; and a searchable, paged table of every rental (by customer name or film title).
- **Daily report** (`python -m reportkit report`): the same KPIs plus top films, revenue by category, a store table
  and the **overdue rentals** list (who to chase, with e-mail addresses). Saved as HTML and CSV; with `--email` it is
  sent as an HTML e-mail with the overdue list attached.
- **JSON API**: `/api/kpis`, `/api/revenue`, `/api/rentals`, `/reports/{day}`, `/health` (OpenAPI docs at `/docs`).

<img src="docs/daily_report.png" width="520" alt="The daily HTML report">

## The SQL

Each query is a file in [`sql/`](sql). Examples:

```sql
-- top_films.sql: ranking with a window function (ties share a place)
SELECT RANK() OVER (ORDER BY COUNT(*) DESC) AS place, f.title, c.name AS category, COUNT(*) AS rentals
FROM rental r JOIN inventory i ON ... JOIN film f ON ... JOIN film_category fc ON ... JOIN category c ON ...
WHERE r.rental_date >= :start AND r.rental_date < :end
GROUP BY f.film_id, f.title, c.name ORDER BY rentals DESC, f.title LIMIT :limit;

-- category_revenue.sql: each category's share of the day's revenue
ROUND(CAST(SUM(p.amount) / SUM(SUM(p.amount)) OVER () AS NUMERIC), 4) AS share
```

Portability between SQLite and PostgreSQL: dates are bound as typed `DateTime` parameters; days are grouped with
`date(...)`, which both support; date arithmetic (when is a rental overdue?) is done in Python because the two
databases do it differently; and every query is checked against both in CI.

**Tests check the numbers, not just that code runs:** store revenues and category revenues must add up to the day's
revenue, category shares must sum to 100%, the KPI rental count must match an independent count, the comparison must
use only earlier trading days, and the overdue list may only contain rentals past their due date.

## Run it

```bash
pip install -e ".[dev,postgres]"
make load      # downloads Sakila (~8.5 MB) and builds data/sakila.db
make serve     # http://127.0.0.1:8000
make report    # reports/daily/<day>/report.html + CSV files
make test      # 22 tests (SQLite); CI runs them on PostgreSQL 16 too
```

**Use your own PostgreSQL database:** set `DATABASE_URL=postgresql+psycopg://user:password@host/sakila`.

**Automate the daily e-mail** (e.g. every morning at 7:00 with cron), with your SMTP server in
`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` and `SMTP_FROM`:

```
0 7 * * *  cd /path/to/database-reporting-platform && python -m reportkit report --email ops@example.com
```

With a live database the default report day would be yesterday; Sakila's data ends in 2006, so the default is the
latest day with rentals.

## Project structure

```
sql/                        one file per query (KPIs, trends, top films, categories, stores, overdue, search)
src/reportkit/db.py         connection (DATABASE_URL), builds the SQLite sample, reads the SQL files
src/reportkit/queries.py    runs the queries, returns Python data / DataFrames
src/reportkit/report.py     daily report: HTML (Jinja2) + chart (matplotlib) + CSV + e-mail (smtplib)
src/reportkit/web.py        FastAPI dashboard and JSON API (Chart.js in the browser)
tests/                      queries, report, e-mail (fake SMTP) and web endpoints
```

## Data

Sakila sample database (MySQL AB), as ported to SQLite and PostgreSQL by jOOQ: https://github.com/jOOQ/sakila,
BSD 2-Clause licence. Downloaded by `make load`; not stored here. Amounts are in US dollars.

## Background

This is a 2026 rebuild of an earlier personal project of mine that connected to a database, showed its records and
sent automated daily reports. The original code was lost, so I rebuilt it with a public sample database.
