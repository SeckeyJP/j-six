"""EIF-002: 売上取込のテスト。"""

from datetime import datetime

import pytest

from app.billing import BillingError, BillingService
from app.importer import COLUMNS, import_sales

CLOCK = lambda: datetime(2026, 9, 1)  # noqa: E731

HEADER = ",".join(COLUMNS)


@pytest.fixture
def svc():
    s = BillingService(clock=CLOCK)
    s.register_customer(
        "C001", "アルファ", closing_day=31, payment_terms="NEXT_MONTH_END"
    )
    return s


def _csv(*rows):
    return HEADER + "\n" + "\n".join(rows) + "\n"


def test_uc001_imports_rows(svc):
    result = import_sales(svc, _csv("S1,C001,2026-08-03,事務用品,3,333,10"))
    assert (result.imported, result.skipped, result.errors) == (1, 0, [])


def test_uc001_is_idempotent(svc):
    body = _csv("S1,C001,2026-08-03,事務用品,3,333,10")
    import_sales(svc, body)
    again = import_sales(svc, body)
    assert (again.imported, again.skipped) == (0, 1)


def test_uc001_missing_columns_rejected(svc):
    with pytest.raises(BillingError, match="列が不足"):
        import_sales(svc, "record_id,customer_code\nS1,C001\n")


def test_uc001_unknown_customer_becomes_error_row(svc):
    """1行の不備で取込全体を止めない。"""
    result = import_sales(
        svc,
        _csv(
            "S1,C999,2026-08-03,事務用品,3,333,10", "S2,C001,2026-08-04,配送料,1,100,10"
        ),
    )
    assert result.imported == 1
    assert len(result.errors) == 1
    assert "2行目" in result.errors[0]


def test_uc001_invalid_number_becomes_error_row(svc):
    result = import_sales(svc, _csv("S1,C001,2026-08-03,事務用品,いくつか,333,10"))
    assert result.imported == 0
    assert len(result.errors) == 1


def test_uc001_invalid_date_becomes_error_row(svc):
    result = import_sales(svc, _csv("S1,C001,2026/08/03,事務用品,3,333,10"))
    assert result.imported == 0
    assert len(result.errors) == 1


def test_req_004_invalid_tax_rate_becomes_error_row(svc):
    result = import_sales(svc, _csv("S1,C001,2026-08-03,事務用品,3,333,5"))
    assert result.imported == 0
    assert "税率" in result.errors[0]


def test_import_result_defaults_errors_to_list():
    from app.importer import ImportResult

    assert ImportResult().errors == []
