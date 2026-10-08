"""Reporting queries. Each function runs one SQL file and returns plain Python data or a DataFrame."""
from __future__ import annotations

from datetime import date, datetime, time, timedelta

import pandas as pd
from sqlalchemy import DateTime, Engine, bindparam, text

from .db import sql

PAGE_SIZE = 25


def _query(name: str, **datetimes):
    """Bind datetime parameters with an explicit type, so SQLite and PostgreSQL compare them the same way."""
    return text(sql(name)).bindparams(*(bindparam(k, type_=DateTime) for k in datetimes))


def _frame(engine: Engine, name: str, params: dict) -> pd.DataFrame:
    stmt = _query(name, **{k: v for k, v in params.items() if isinstance(v, datetime)})
    with engine.connect() as conn:
        return pd.read_sql(stmt, conn, params=params)


def _day_range(day: date, days: int = 1) -> dict:
    start = datetime.combine(day, time.min)
    return {"start": start, "end": start + timedelta(days=days)}


def trading_days(engine: Engine) -> list[date]:
    """Days that had rentals, newest first."""
    df = _frame(engine, "trading_days", {})
    return [pd.Timestamp(d).date() for d in df["day"]]


def day_kpis(engine: Engine, day: date) -> dict:
    row = _frame(engine, "day_kpis", _day_range(day)).iloc[0]
    rentals, revenue = int(row["rentals"]), float(row["revenue"])
    return {"day": day.isoformat(), "rentals": rentals, "revenue": round(revenue, 2),
            "active_customers": int(row["active_customers"]), "returns": int(row["returns"]),
            "revenue_per_rental": round(revenue / rentals, 2) if rentals else 0.0}


def kpis_with_comparison(engine: Engine, day: date, compare_days: int = 7) -> dict:
    """KPIs for `day` plus the average of the previous `compare_days` trading days and the % change."""
    today = day_kpis(engine, day)
    earlier = [d for d in trading_days(engine) if d < day][:compare_days]
    if not earlier:
        return {**today, "baseline": None, "change_pct": {}}
    past = [day_kpis(engine, d) for d in earlier]
    keys = ("rentals", "revenue", "active_customers", "returns", "revenue_per_rental")
    baseline = {k: round(sum(p[k] for p in past) / len(past), 2) for k in keys}
    change = {k: round(100 * (today[k] / baseline[k] - 1), 1) for k in keys if baseline[k]}
    return {**today, "baseline": baseline, "baseline_days": len(past), "change_pct": change}


def revenue_by_day(engine: Engine, start: date, end: date) -> pd.DataFrame:
    df = _frame(engine, "revenue_by_day", {**_day_range(start, (end - start).days + 1)})
    df["day"] = pd.to_datetime(df["day"]).dt.date
    return df.astype({"revenue": float, "rentals": int})


def top_films(engine: Engine, day: date, days: int = 1, limit: int = 5) -> pd.DataFrame:
    return _frame(engine, "top_films", {**_day_range(day, days), "limit": limit})


def category_revenue(engine: Engine, day: date, days: int = 1) -> pd.DataFrame:
    return _frame(engine, "category_revenue", _day_range(day, days)).astype({"revenue": float, "share": float})


def store_comparison(engine: Engine, day: date, days: int = 1) -> pd.DataFrame:
    return _frame(engine, "store_comparison", _day_range(day, days)).astype({"revenue": float})


def overdue_rentals(engine: Engine, as_of: datetime) -> pd.DataFrame:
    """Rentals still out at `as_of` whose allowed rental period has passed, most overdue first."""
    df = _frame(engine, "open_rentals", {"as_of": as_of})
    df["rental_date"] = pd.to_datetime(df["rental_date"])
    df["due"] = df["rental_date"] + pd.to_timedelta(df["rental_duration"], unit="D")
    df["days_overdue"] = (pd.Timestamp(as_of) - df["due"]).dt.days
    return df[df["days_overdue"] > 0].sort_values("days_overdue", ascending=False).reset_index(drop=True)


def search_rentals(engine: Engine, q: str = "", page: int = 1, size: int = PAGE_SIZE) -> tuple[pd.DataFrame, int]:
    """One page of rentals (newest first) matching a customer name or film title, plus the total count."""
    q = q.strip().lower()
    params = {"q": q, "pattern": f"%{q}%"}
    total = int(_frame(engine, "rentals_count", params)["total"].iloc[0])
    rows = _frame(engine, "rentals_search", {**params, "limit": size, "offset": (max(page, 1) - 1) * size})
    return rows, total
