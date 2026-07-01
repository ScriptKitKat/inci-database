from datetime import datetime

import pytest
import typer

from inci_pipeline.cli import _parse_datetime_input


def test_parse_datetime_input_accepts_iso_with_offset():
    parsed = _parse_datetime_input("2026-06-30T00:00:00-04:00")
    assert parsed.isoformat() == "2026-06-30T00:00:00-04:00"


def test_parse_datetime_input_accepts_date_only():
    parsed = _parse_datetime_input("2026-06-30")
    assert parsed == datetime(2026, 6, 30, 0, 0, 0)


def test_parse_datetime_input_end_of_day_advances_one_day():
    parsed = _parse_datetime_input("2026-06-30", end_of_day=True)
    assert parsed == datetime(2026, 7, 1, 0, 0, 0)


def test_parse_datetime_input_rejects_garbage():
    with pytest.raises(typer.BadParameter):
        _parse_datetime_input("banana")

