"""
services/ics_export.py — генерация файла расписания в формате iCalendar (RFC 5545).

Назначение: собрать все занятия в файл .ics для ручного импорта в
Google Calendar / Яндекс.Календарь. Никаких сетевых запросов и API.
Кто вызывает: экран отчётов / главный экран (кнопка "Экспорт расписания").

Регулярные слоты расписания оформляются как VEVENT с RRULE FREQ=WEEKLY.
"""
from datetime import datetime, timedelta

# Соответствие weekday (0=Пн..6=Вс) кодам дней iCalendar.
_ICAL_DAYS = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]


def _next_date_for_weekday(weekday, base=None):
    """Возвращает ближайшую дату (>= base) с нужным днём недели."""
    base = base or datetime.now()
    delta = (weekday - base.weekday()) % 7
    return base + timedelta(days=delta)


def _fold(line):
    """Складывает длинные строки по правилу RFC 5545 (макс. 75 октетов)."""
    out = []
    while len(line.encode("utf-8")) > 75:
        # Грубое, но безопасное складывание по символам.
        cut = 74
        out.append(line[:cut])
        line = " " + line[cut:]
    out.append(line)
    return "\r\n".join(out)


def build_ics(subjects_with_slots, count_weeks=16):
    """Строит содержимое .ics.

    Аргументы:
        subjects_with_slots: список dict {
            "subject": str, "slots": [(weekday:int, "HH:MM"), ...]
        };
        count_weeks: сколько недель повторять регулярное занятие (RRULE COUNT).
    Возврат: строка с содержимым файла .ics (CRLF-переводы строк).
    """
    now = datetime.now()
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//TeacherJournal//RU",
        "CALSCALE:GREGORIAN",
    ]
    uid_counter = 0
    for item in subjects_with_slots:
        subject = item["subject"]
        for weekday, start_time in item["slots"]:
            uid_counter += 1
            hh, mm = start_time.split(":")
            first = _next_date_for_weekday(weekday, now).replace(
                hour=int(hh), minute=int(mm), second=0, microsecond=0)
            end = first + timedelta(hours=1)  # длительность занятия 1 час
            dtstamp = now.strftime("%Y%m%dT%H%M%S")
            dtstart = first.strftime("%Y%m%dT%H%M%S")
            dtend = end.strftime("%Y%m%dT%H%M%S")
            byday = _ICAL_DAYS[weekday]
            lines += [
                "BEGIN:VEVENT",
                f"UID:tj-{uid_counter}-{dtstart}@teacherjournal",
                f"DTSTAMP:{dtstamp}",
                f"DTSTART:{dtstart}",
                f"DTEND:{dtend}",
                _fold(f"SUMMARY:{subject}"),
                f"RRULE:FREQ=WEEKLY;BYDAY={byday};COUNT={count_weeks}",
                "END:VEVENT",
            ]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


def write_ics(subjects_with_slots, path, count_weeks=16):
    """Записывает .ics в файл. Возврат: путь к файлу."""
    content = build_ics(subjects_with_slots, count_weeks)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path
