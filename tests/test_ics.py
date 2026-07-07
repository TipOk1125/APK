"""
test_ics.py — корректность генерации .ics (RFC 5545).
"""
from services import ics_export


def test_ics_structure():
    items = [{"subject": "Математика", "slots": [(0, "09:00")]}]  # Пн 09:00
    content = ics_export.build_ics(items, count_weeks=10)
    assert content.startswith("BEGIN:VCALENDAR")
    assert "END:VCALENDAR" in content
    assert "BEGIN:VEVENT" in content
    assert "SUMMARY:Математика" in content
    assert "RRULE:FREQ=WEEKLY;BYDAY=MO;COUNT=10" in content
    assert "VERSION:2.0" in content
