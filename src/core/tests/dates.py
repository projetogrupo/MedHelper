"""Date helpers shared by the booking tests.

Booking refuses slots in the past, so any test that books one needs a date
ahead of today. Hardcoding one works until that date arrives and then fails
forever — which is exactly what happened to the previous `2026-07-27`.
"""
import datetime


def next_weekday(weekday):
    """The next future date falling on ``weekday`` (0 = Monday)."""
    today = datetime.date.today()
    return today + datetime.timedelta(days=(weekday - today.weekday()) % 7 or 7)
