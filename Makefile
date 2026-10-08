.PHONY: setup load serve report test lint

setup:    ## install the package, dev tools and the PostgreSQL driver
	pip install -e ".[dev,postgres]"

load:     ## download the Sakila sample database and build data/sakila.db (SQLite)
	python -m reportkit load

serve:    ## web dashboard on http://127.0.0.1:8000
	python -m reportkit serve

report:   ## daily report for the latest trading day -> reports/daily/<day>/
	python -m reportkit report

test:
	pytest -q

lint:
	ruff check .
