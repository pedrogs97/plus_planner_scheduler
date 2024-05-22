"""Utility functions for the project."""
from typing import List, Generator
from datetime import datetime, timedelta

one_day = timedelta(days=1)

def get_week(date: datetime) -> Generator[List[datetime], None, None]:
    """Return the full week (Sunday first) of the week containing the given date.
    """
    day_idx = (date.weekday() + 1) % 7  # turn sunday into 0, monday into 1, etc.
    sunday = date - timedelta(days=day_idx)
    date = sunday
    for _ in range(7):
        yield date
        date += one_day
