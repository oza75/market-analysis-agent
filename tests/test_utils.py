from __future__ import annotations

from datetime import date

import pytest

from analyst_agent.utils import iso_week_label, load_prompt


def test_load_prompt_missing_file_raises():
    """A missing prompt name must raise FileNotFoundError — not return empty string.

    load_prompt is called at module import time, so a wrong name crashes the
    agent on startup. An explicit error is the only acceptable failure mode.
    """
    with pytest.raises(FileNotFoundError):
        load_prompt("this_prompt_does_not_exist")


def test_iso_week_label_crosses_year_boundary():
    """An offset that crosses a year boundary must produce a label with the prior year.

    date(2026-01-05) is in ISO week 2 of 2026.
    Subtracting 4 weeks lands on 2025-12-08, which is ISO week 50 of 2025.
    This is the classic year-rollover path in isocalendar().
    """
    result = iso_week_label(date(2026, 1, 5), weeks_ago=4)
    assert result == "2025-W50"
