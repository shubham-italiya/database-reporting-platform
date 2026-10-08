"""Command line:  python -m reportkit {load,report,serve}"""
from __future__ import annotations

import argparse
from datetime import date

from .db import SQLITE_FILE, build_sqlite, get_engine


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m reportkit", description="Reporting on the Sakila rental database.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("load", help="download Sakila and build data/sakila.db (SQLite)")
    rp = sub.add_parser("report", help="build the daily report (HTML + CSV) and optionally email it")
    rp.add_argument("--date", type=date.fromisoformat, help="YYYY-MM-DD (default: latest trading day)")
    rp.add_argument("--email", help="send the report to this address (SMTP_* environment variables)")
    sp = sub.add_parser("serve", help="run the web dashboard")
    sp.add_argument("--host", default="127.0.0.1")
    sp.add_argument("--port", type=int, default=8000)
    args = ap.parse_args(argv)

    if args.cmd == "load":
        build_sqlite()
        print(f"Built {SQLITE_FILE}")
    elif args.cmd == "report":
        from .report import build_report, save_report, send_email

        report = build_report(get_engine(), args.date)
        path = save_report(report)
        k = report.kpis
        print(f"{report.day}: {k['rentals']} rentals, ${k['revenue']:,.2f} revenue, "
              f"{len(report.tables['overdue'])} overdue. Saved {path}")
        if args.email:
            send_email(report, args.email)
            print(f"Emailed to {args.email}")
    elif args.cmd == "serve":
        import uvicorn

        uvicorn.run("reportkit.web:app", host=args.host, port=args.port)
    return 0
