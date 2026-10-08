def test_dashboard_shows_kpis_chart_and_rentals(client):
    r = client.get("/", params={"day": "2005-08-01"})
    assert r.status_code == 200
    for text in ("Rental reporting", "671", "$2,817.29", "new Chart(", "Rentals (16,044)"):
        assert text in r.text


def test_dashboard_search_and_paging(client):
    r = client.get("/", params={"day": "2005-08-01", "q": "academy", "page": 2})   # 32 matches = 2 pages
    assert r.status_code == 200 and "Academy" in r.text and "Page 2 of 2" in r.text and "Newer" in r.text


def test_api_kpis(client):
    body = client.get("/api/kpis", params={"day": "2005-08-01"}).json()
    assert body["rentals"] == 671 and body["baseline_days"] == 7


def test_api_rentals_returns_a_page(client):
    body = client.get("/api/rentals", params={"q": "academy"}).json()
    assert body["total"] > 0 and len(body["rows"]) <= body["page_size"]
    assert all("ACADEMY" in row["title"] for row in body["rows"])


def test_api_revenue_and_validation(client):
    days = client.get("/api/revenue", params={"start": "2005-07-26", "end": "2005-08-02"}).json()
    assert days[-1]["day"] == "2005-08-02"
    assert client.get("/api/revenue", params={"start": "2005-08-02", "end": "2005-07-26"}).status_code == 422


def test_report_page_and_unknown_days(client):
    assert "Daily rental report" in client.get("/reports/2005-08-01").text
    assert client.get("/reports/2005-06-01").status_code == 404
    assert client.get("/reports/not-a-date").status_code == 422


def test_health(client):
    assert client.get("/health").json() == {"status": "ok", "trading_days": 41}
