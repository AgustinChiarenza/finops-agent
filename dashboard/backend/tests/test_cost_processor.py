from datetime import date

from app.processors.cost_processor import _filter_costs, _parse_row


def _row(period="2026-01-01", service_type="ECS", owner="alice", env="prod", cost=10.0):
    return {
        "date": period,
        "service_type": service_type,
        "owner": owner,
        "environment": env,
        "resource_id": "r-1",
        "resource_name": "vm",
        "billing_mode": "on-demand",
        "daily_cost_usd": cost,
        "usage_amount": 1.0,
    }


def test_parse_row_handles_missing_cost():
    parsed = _parse_row({"date": "2026-01-01", "service_type": "ECS"})
    assert parsed["cost"] == 0.0
    assert parsed["owner"] == ""
    assert parsed["period"] == "2026-01-01"


def test_filter_by_date_range():
    data = [_parse_row(_row(period="2026-01-01")), _parse_row(_row(period="2026-02-01"))]
    filtered = _filter_costs(data, start_date=date(2026, 1, 15), end_date=date(2026, 3, 1))
    assert len(filtered) == 1
    assert filtered[0]["period"] == "2026-02-01"


def test_filter_by_service_and_owner():
    data = [
        _parse_row(_row(service_type="ECS", owner="alice")),
        _parse_row(_row(service_type="RDS", owner="alice")),
        _parse_row(_row(service_type="ECS", owner="bob")),
    ]
    filtered = _filter_costs(data, service_type="ECS", owner="alice")
    assert len(filtered) == 1


def test_filter_no_filters_returns_all():
    data = [_parse_row(_row()), _parse_row(_row(period="2026-01-02"))]
    assert _filter_costs(data) == data
