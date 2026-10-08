from datetime import date

import pytest

from reportkit import report as rp


def test_report_contains_the_numbers(engine):
    r = rp.build_report(engine, date(2005, 8, 1))
    assert r.day == date(2005, 8, 1) and r.kpis["rentals"] == 671
    for text in ("Daily rental report", "671", "$2,817.29", "Top films", "Overdue rentals", "data:image/png;base64,"):
        assert text in r.html
    assert r.chart_png.startswith(b"\x89PNG")


def test_default_day_is_the_latest_trading_day(engine):
    assert rp.build_report(engine).day == date(2006, 2, 14)


def test_save_writes_html_and_csvs(engine, tmp_path):
    path = rp.save_report(rp.build_report(engine, date(2005, 8, 1)), tmp_path)
    assert path.read_text().startswith("<!doctype html>")
    assert {p.name for p in path.parent.glob("*.csv")} == {"top_films.csv", "categories.csv", "stores.csv",
                                                          "overdue.csv"}


def test_email_is_sent_with_the_csv_attached(engine, monkeypatch):
    sent = []

    class FakeSMTP:
        def __init__(self, host, port):
            self.host, self.port = host, port
        def __enter__(self):
            return self
        def __exit__(self, *exc):
            return False
        def starttls(self):
            pass
        def login(self, user, password):
            pass
        def send_message(self, msg):
            sent.append(msg)

    monkeypatch.setattr(rp.smtplib, "SMTP", FakeSMTP)
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    rp.send_email(rp.build_report(engine, date(2005, 8, 1)), "ops@example.com")
    [msg] = sent
    assert msg["To"] == "ops@example.com" and "671 rentals" in msg["Subject"]
    assert [p.get_filename() for p in msg.iter_attachments()] == ["overdue_2005-08-01.csv"]


def test_unknown_day_has_empty_tables_not_an_error(engine):
    r = rp.build_report(engine, date(2005, 6, 1))   # the shop had no rentals that day
    assert r.kpis["rentals"] == 0 and "Nothing on this day." in r.html


@pytest.mark.parametrize("days", [1])
def test_chart_is_a_png(engine, days):
    assert rp.build_report(engine, date(2005, 7, 31)).chart_png[:4] == b"\x89PNG"
