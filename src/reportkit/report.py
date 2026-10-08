"""The automated daily report: HTML (safe to send as an email) plus CSV files of the tables.

  python -m reportkit report                    # latest trading day (in a live database: yesterday)
  python -m reportkit report --date 2005-08-01 --email ops@example.com
"""
from __future__ import annotations

import base64
import io
import os
import smtplib
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from email.message import EmailMessage
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from jinja2 import Environment, FileSystemLoader, select_autoescape  # noqa: E402
from sqlalchemy import Engine  # noqa: E402

from . import queries as q  # noqa: E402
from .paths import REPORTS_DIR, TEMPLATES_DIR  # noqa: E402

_templates = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=select_autoescape())


@dataclass
class DailyReport:
    day: date
    kpis: dict
    tables: dict[str, pd.DataFrame]
    chart_png: bytes
    html: str


def build_report(engine: Engine, day: date | None = None) -> DailyReport:
    day = day or q.trading_days(engine)[0]
    end_of_day = datetime.combine(day + timedelta(days=1), time.min)
    kpis = q.kpis_with_comparison(engine, day)
    trend = q.revenue_by_day(engine, day - timedelta(days=29), day)
    tables = {
        "top_films": q.top_films(engine, day, limit=10),
        "categories": q.category_revenue(engine, day),
        "stores": q.store_comparison(engine, day),
        "overdue": q.overdue_rentals(engine, end_of_day),
    }
    chart = _trend_chart(trend, day)
    html = _templates.get_template("report.html").render(
        day=day, kpis=kpis, tables=tables, chart=base64.b64encode(chart).decode(),
        overdue_top=tables["overdue"].head(15), generated=datetime.now().strftime("%Y-%m-%d %H:%M"))
    return DailyReport(day, kpis, tables, chart, html)


def _trend_chart(trend: pd.DataFrame, day: date) -> bytes:
    fig, ax = plt.subplots(figsize=(7, 2.6))
    ax.bar(pd.to_datetime(trend["day"]), trend["revenue"], color="#2563eb", width=0.8)
    ax.bar(pd.Timestamp(day), trend.loc[trend["day"] == day, "revenue"].sum(), color="#f59e0b", width=0.8)
    ax.set_ylabel("Revenue ($)")
    ax.set_title("Revenue per day, last 30 days (report day in orange)", fontsize=10)
    ax.tick_params(axis="x", labelsize=8)
    fig.autofmt_xdate()
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120)
    plt.close(fig)
    return buf.getvalue()


def save_report(report: DailyReport, folder: Path = REPORTS_DIR / "daily") -> Path:
    out = folder / report.day.isoformat()
    out.mkdir(parents=True, exist_ok=True)
    (out / "report.html").write_text(report.html, encoding="utf-8")
    for name, df in report.tables.items():
        df.to_csv(out / f"{name}.csv", index=False)
    return out / "report.html"


def send_email(report: DailyReport, to: str) -> None:
    """Send with the SMTP server in SMTP_HOST / SMTP_PORT / SMTP_USER / SMTP_PASSWORD / SMTP_FROM."""
    msg = EmailMessage()
    msg["Subject"] = (f"Daily rental report {report.day:%d %b %Y}: {report.kpis['rentals']} rentals, "
                      f"${report.kpis['revenue']:,.2f}")
    msg["From"] = os.environ.get("SMTP_FROM", os.environ.get("SMTP_USER", "reports@localhost"))
    msg["To"] = to
    msg.set_content("This report is HTML. Open it in an email program that shows HTML.")
    msg.add_alternative(report.html, subtype="html")
    msg.add_attachment(report.tables["overdue"].to_csv(index=False).encode(), maintype="text", subtype="csv",
                       filename=f"overdue_{report.day}.csv")
    with smtplib.SMTP(os.environ["SMTP_HOST"], int(os.environ.get("SMTP_PORT", "587"))) as smtp:
        if os.environ.get("SMTP_USER"):
            smtp.starttls()
            smtp.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
        smtp.send_message(msg)
