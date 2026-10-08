from datetime import date, datetime

import pytest
from sqlalchemy import text

from reportkit import queries as q

DAY = date(2005, 8, 1)


def scalar(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar()


def test_trading_days_are_newest_first(engine):
    days = q.trading_days(engine)
    assert len(days) == 41 and days == sorted(days, reverse=True)
    assert days[-1] == date(2005, 5, 24)


def test_day_kpis_match_independent_counts(engine):
    k = q.day_kpis(engine, DAY)
    start, end = datetime(2005, 8, 1), datetime(2005, 8, 2)
    assert k["rentals"] == 671
    assert k["revenue"] == pytest.approx(2817.29)
    rentals_by_python = sum(1 for (d,) in _all(engine, "SELECT rental_date FROM rental") if start <= _ts(d) < end)
    assert k["rentals"] == rentals_by_python
    assert k["revenue_per_rental"] == pytest.approx(round(k["revenue"] / k["rentals"], 2))


def test_comparison_uses_previous_trading_days_only(engine):
    k = q.kpis_with_comparison(engine, DAY, compare_days=7)
    earlier = [d for d in q.trading_days(engine) if d < DAY][:7]
    expected = sum(q.day_kpis(engine, d)["rentals"] for d in earlier) / 7
    assert k["baseline_days"] == 7 and k["baseline"]["rentals"] == pytest.approx(expected, abs=0.01)
    assert k["change_pct"]["rentals"] == pytest.approx(100 * (671 / expected - 1), abs=0.1)


def test_first_day_has_no_baseline(engine):
    assert q.kpis_with_comparison(engine, date(2005, 5, 24))["baseline"] is None


def test_stores_and_categories_add_up_to_the_day(engine):
    total = q.day_kpis(engine, DAY)["revenue"]
    assert q.store_comparison(engine, DAY)["revenue"].sum() == pytest.approx(total, abs=0.01)
    cats = q.category_revenue(engine, DAY)
    assert cats["revenue"].sum() == pytest.approx(total, abs=0.01)
    assert cats["share"].sum() == pytest.approx(1.0, abs=0.001)
    assert list(cats["revenue"]) == sorted(cats["revenue"], reverse=True)


def test_top_films_are_ranked(engine):
    top = q.top_films(engine, DAY, limit=10)
    assert len(top) == 10 and list(top["rentals"]) == sorted(top["rentals"], reverse=True)
    assert top["place"].iloc[0] == 1


def test_overdue_rentals_are_past_their_due_date(engine):
    as_of = datetime(2005, 8, 2)
    od = q.overdue_rentals(engine, as_of)
    assert len(od) > 0 and (od["due"] < as_of).all()
    assert list(od["days_overdue"]) == sorted(od["days_overdue"], reverse=True)


def test_search_filters_and_pages(engine):
    rows, total = q.search_rentals(engine, "Academy Dinosaur")
    assert total > 0 and rows["title"].str.contains("ACADEMY DINOSAUR").all()
    everything = scalar(engine, "SELECT COUNT(*) FROM rental")
    assert q.search_rentals(engine, "")[1] == everything
    page2, _ = q.search_rentals(engine, "", page=2, size=10)
    page1, _ = q.search_rentals(engine, "", page=1, size=10)
    assert len(page2) == 10 and set(page1["rental_id"]).isdisjoint(page2["rental_id"])
    assert q.search_rentals(engine, "no such film zzz")[1] == 0


def test_revenue_by_day_covers_every_active_day(engine):
    df = q.revenue_by_day(engine, date(2005, 7, 26), date(2005, 8, 2))
    assert list(df["day"]) == sorted(df["day"]) and df["day"].iloc[-1] == date(2005, 8, 2)
    assert df.loc[df["day"] == DAY, "revenue"].iloc[0] == pytest.approx(2817.29)


def _all(engine, sql):
    with engine.connect() as conn:
        return conn.execute(text(sql)).fetchall()


def _ts(value) -> datetime:
    return value if isinstance(value, datetime) else datetime.fromisoformat(str(value).replace(" ", "T"))
