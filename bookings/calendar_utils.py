"""
Centralny moduł kalendarza — jedna implementacja dla wszystkich widoków.

Zawiera:
- build_month_grid()    — buduje siatkę kalendarza z dostępnością
- get_day_details()     — szczegóły dnia (rezerwacje, blokady)
- month_nav()           — helper prev/next month
- MONTH_NAMES_PL        — polskie nazwy miesięcy
"""

from __future__ import annotations

import calendar as _cal
from collections import defaultdict
from datetime import date, timedelta

from django.utils import timezone

from .models import Booking, BlockedDate, Restaurant

# ── Stałe ─────────────────────────────────────────────────────────────────────

MONTH_NAMES_PL = [
    "",
    "Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec",
    "Lipiec", "Sierpień", "Wrzesień", "Październik", "Listopad", "Grudzień",
]

DAY_ABBR_PL = ["Pn", "Wt", "Śr", "Cz", "Pt", "Sb", "Nd"]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_month(year, month, today: date | None = None):
    """Clamp & normalise year/month params. Returns (year, month, today)."""
    if today is None:
        today = timezone.now().date()
    try:
        year = int(year)
        month = int(month)
    except (ValueError, TypeError):
        year, month = today.year, today.month
    if month < 1 or month > 12:
        year, month = today.year, today.month
    return year, month, today


def month_nav(year: int, month: int, today: date | None = None):
    """Return (prev, next) dicts with year/month keys. prev=None if before today."""
    if today is None:
        today = timezone.now().date()
    # Previous
    if month == 1:
        prev_y, prev_m = year - 1, 12
    else:
        prev_y, prev_m = year, month - 1
    prev = {"year": prev_y, "month": prev_m} if (prev_y, prev_m) >= (today.year, today.month) else None
    # Next — limit to 18 months ahead
    if month == 12:
        next_y, next_m = year + 1, 1
    else:
        next_y, next_m = year, month + 1
    limit_y = today.year + 1
    limit_m = today.month + 6
    if limit_m > 12:
        limit_m -= 12
        limit_y += 1
    nxt = {"year": next_y, "month": next_m} if (next_y, next_m) <= (limit_y, limit_m) else None
    return prev, nxt


# ── Główna funkcja budująca siatkę ────────────────────────────────────────────

def build_month_grid(
    restaurant: Restaurant,
    year,
    month,
    *,
    include_bookings: bool = False,
    date_as_iso: bool = False,
):
    """
    Build a calendar month grid for *restaurant*.

    Parameters
    ----------
    restaurant : Restaurant instance
    year, month : int-like values (clamped & validated)
    include_bookings : bool
        When True each cell includes ``bookings`` list with detail dicts
        (for the owner calendar). When False only ``booked`` bool is set.
    date_as_iso : bool
        When True cell["date"] is an ISO-8601 string instead of ``date`` object.
        Useful in templates that need ``data-date`` attributes.

    Returns
    -------
    dict with keys:
        weeks          — list of 7-element lists (None for empty cells)
        year, month    — ints
        month_name     — str (Polish)
        prev, next     — dicts or None
        today          — date
        stats          — dict (total, confirmed, pending, guests)
    """
    year, month, today = _parse_month(year, month)
    first_weekday, num_days = _cal.monthrange(year, month)
    max_per_day = restaurant.max_events_per_day or 1

    # ── Fetch bookings this month ────────────────────────────────────────
    bookings_qs = (
        Booking.objects.filter(
            restaurant=restaurant,
            event_date__year=year,
            event_date__month=month,
        )
        .exclude(status="cancelled")
        .select_related("user")
        .order_by("event_start_time", "pk")
    )

    # Group bookings by day
    bookings_by_day: dict[int, list] = defaultdict(list)
    for b in bookings_qs:
        bookings_by_day[b.event_date.day].append(b)

    # ── Fetch blocked dates this month ───────────────────────────────────
    blocked_set = set(
        BlockedDate.objects.filter(
            restaurant=restaurant,
            date__year=year,
            date__month=month,
        ).values_list("date", flat=True)
    )

    # ── Build weeks grid (Monday = 0) ────────────────────────────────────
    weeks = []
    week: list[dict | None] = [None] * first_weekday

    for day_num in range(1, num_days + 1):
        d = date(year, month, day_num)
        is_past = d < today
        is_today = d == today
        is_blocked = d in blocked_set
        is_closed = restaurant.is_day_closed(d)
        day_bookings = bookings_by_day.get(day_num, [])
        booking_count = len(day_bookings)
        is_full = booking_count >= max_per_day

        cell = {
            "day": day_num,
            "date": d.isoformat() if date_as_iso else d,
            "past": is_past,
            "today": is_today,
            "blocked": is_blocked,
            "closed": is_closed,
            "booked": is_full and not is_closed and not is_blocked,
            "free": not is_past and not is_full and not is_blocked and not is_closed,
            "booking_count": booking_count,
            "max_events": max_per_day,
        }

        if include_bookings:
            cell["bookings"] = [
                {
                    "id": b.id,
                    "type_display": b.get_event_type_display() if b.event_type else "Rezerwacja",
                    "guest_count": b.guest_count,
                    "status": b.status,
                    "client": f"{b.first_name} {b.last_name}",
                    "start_time": b.event_start_time.strftime("%H:%M") if b.event_start_time else None,
                    "end_time": b.event_end_time.strftime("%H:%M") if b.event_end_time else None,
                    "phone": b.phone,
                    "email": b.email,
                }
                for b in day_bookings
            ]

        week.append(cell)

        if len(week) == 7:
            weeks.append(week)
            week = []

    # Pad last week
    if week:
        week.extend([None] * (7 - len(week)))
        weeks.append(week)

    # ── Navigation ───────────────────────────────────────────────────────
    prev, nxt = month_nav(year, month, today)

    # ── Stats ────────────────────────────────────────────────────────────
    stats = {
        "total": bookings_qs.count(),
        "confirmed": sum(1 for b in bookings_qs if b.status == "confirmed"),
        "pending": sum(1 for b in bookings_qs if b.status == "pending"),
        "guests": sum(b.guest_count or 0 for b in bookings_qs),
        "blocked_days": len(blocked_set),
    }

    return {
        "weeks": weeks,
        "year": year,
        "month": month,
        "month_name": MONTH_NAMES_PL[month],
        "prev": prev,
        "next": nxt,
        "today": today,
        "stats": stats,
    }


# ── Day detail ────────────────────────────────────────────────────────────────

def get_day_details(restaurant: Restaurant, d: date) -> dict:
    """Return detailed information for a single day."""
    is_closed = restaurant.is_day_closed(d)
    blocked = BlockedDate.objects.filter(restaurant=restaurant, date=d).first()
    bookings = list(
        Booking.objects.filter(
            restaurant=restaurant, event_date=d,
        )
        .exclude(status="cancelled")
        .select_related("user")
        .order_by("event_start_time", "pk")
    )
    max_per_day = restaurant.max_events_per_day or 1

    return {
        "date": d,
        "date_iso": d.isoformat(),
        "day_name": MONTH_NAMES_PL[d.month],
        "closed": is_closed,
        "blocked": blocked,
        "bookings": [
            {
                "id": b.id,
                "type_display": b.get_event_type_display() if b.event_type else "Rezerwacja",
                "guest_count": b.guest_count,
                "status": b.status,
                "status_display": b.get_status_display(),
                "client": f"{b.first_name} {b.last_name}",
                "start_time": b.event_start_time,
                "end_time": b.event_end_time,
                "phone": b.phone,
                "email": b.email,
                "notes": b.notes,
                "created_at": b.created_at,
            }
            for b in bookings
        ],
        "booking_count": len(bookings),
        "max_events": max_per_day,
        "slots_left": max(0, max_per_day - len(bookings)),
        "is_full": len(bookings) >= max_per_day,
    }
