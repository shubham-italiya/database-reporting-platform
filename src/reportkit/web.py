"""Web dashboard and JSON API:  python -m reportkit serve   then open http://127.0.0.1:8000"""
from __future__ import annotations

import json
from datetime import date, timedelta
from functools import lru_cache

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import Engine

from . import queries as q
from .db import get_engine
from .paths import TEMPLATES_DIR
from .report import build_report

app = FastAPI(title="Rental reporting", description="KPIs, rentals search and daily reports from a SQL database.")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@lru_cache
def engine() -> Engine:
    """One connection pool per process. Tests point the app at their own database with app.state.engine."""
    return get_engine()


def _engine() -> Engine:
    return app.state.engine if getattr(app.state, "engine", None) is not None else engine()


def _pick_day(day: date | None) -> date:
    days = q.trading_days(_engine())
    if day is None:
        return days[0]
    if day not in days:
        raise HTTPException(404, f"no rentals on {day}; try one of the last trading days, e.g. {days[0]}")
    return day


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, day: date | None = None, q_: str = Query("", alias="q"), page: int = Query(1, ge=1)):
    eng, day = _engine(), _pick_day(day)
    kpis = q.kpis_with_comparison(eng, day)
    trend = q.revenue_by_day(eng, day - timedelta(days=29), day)
    rows, total = q.search_rentals(eng, q_, page)
    rows = rows.astype(object).where(rows.notna(), None)   # missing payment -> None, not NaN
    return templates.TemplateResponse(request, "dashboard.html", {
        "day": day, "kpis": kpis, "days": q.trading_days(eng)[:41], "search": q_, "page": page,
        "pages": max(1, -(-total // q.PAGE_SIZE)), "total": total, "rows": rows.to_dict("records"),
        "trend": json.dumps({"labels": [d.isoformat() for d in trend["day"]], "revenue": trend["revenue"].tolist(),
                             "rentals": trend["rentals"].tolist()}),
        "stores": q.store_comparison(eng, day).to_dict("records"),
    })


@app.get("/api/kpis")
def api_kpis(day: date | None = None) -> dict:
    return q.kpis_with_comparison(_engine(), _pick_day(day))


@app.get("/api/revenue")
def api_revenue(start: date, end: date) -> list[dict]:
    if end < start or (end - start).days > 366:
        raise HTTPException(422, "end must be after start, at most one year apart")
    df = q.revenue_by_day(_engine(), start, end)
    return [{"day": r.day.isoformat(), "revenue": r.revenue, "rentals": r.rentals} for r in df.itertuples()]


@app.get("/api/rentals")
def api_rentals(q_: str = Query("", alias="q", max_length=100), page: int = Query(1, ge=1)) -> dict:
    rows, total = q.search_rentals(_engine(), q_, page)
    rows = rows.astype(object).where(rows.notna(), None)
    out = []
    for r in rows.to_dict("records"):
        r["rental_date"] = str(r["rental_date"])
        r["return_date"] = str(r["return_date"]) if r["return_date"] is not None else None
        out.append(r)
    return {"total": total, "page": page, "page_size": q.PAGE_SIZE, "rows": out}


@app.get("/reports/{day}", response_class=HTMLResponse)
def daily_report(day: date) -> HTMLResponse:
    return HTMLResponse(build_report(_engine(), _pick_day(day)).html)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "trading_days": len(q.trading_days(_engine()))}
