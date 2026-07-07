"""
services/reminders.py — локальные напоминания и очередь незаполненных занятий.

Назначение:
    * найти прошедшие слоты расписания, для которых занятие ещё не заполнено;
    * показать локальное уведомление (plyer) — на Android с оговоркой про
      ограничения фоновых будильников (см. docs/MAINTENANCE.md).
Кто вызывает: главный экран при запуске и по таймеру (раз в час).

ВАЖНО: основной механизм — проверка при ОТКРЫТИИ приложения. Фон вторичен.
"""
from datetime import datetime, timedelta

import db


def compute_unfilled_slots(days_back=14):
    """Возвращает список незаполненных прошедших слотов.

    Логика: для каждого слота расписания генерируем ожидаемые даты за последние
    days_back дней; если для (subject, date, time) нет заполненного занятия
    (filled=1) — это незаполненный слот.
    Возврат: список dict {"subject_id", "subject", "date", "time"}.
    """
    now = datetime.now()
    result = []
    subjects = {s["id"]: s["name"] for s in db.list_subjects()}
    slots = db.list_schedule_slots()
    for slot in slots:
        subject_id = slot["subject_id"]
        weekday = slot["weekday"]
        hh, mm = slot["start_time"].split(":")
        # Идём назад по дням и ищем даты нужного дня недели.
        for delta in range(days_back + 1):
            day = now - timedelta(days=delta)
            if day.weekday() != weekday:
                continue
            slot_dt = day.replace(hour=int(hh), minute=int(mm),
                                  second=0, microsecond=0)
            if slot_dt > now:
                continue  # ещё не наступил
            date_str = slot_dt.strftime("%Y-%m-%d")
            # Проверяем, заполнено ли занятие.
            filled = _is_filled(subject_id, date_str, slot["start_time"])
            if not filled:
                result.append({
                    "subject_id": subject_id,
                    "subject": subjects.get(subject_id, "?"),
                    "date": date_str,
                    "time": slot["start_time"],
                })
    return result


def _is_filled(subject_id, date_str, start_time):
    """Проверяет, существует ли заполненное занятие для слота."""
    with db.get_connection() as conn:
        row = conn.execute(
            "SELECT filled FROM lessons WHERE subject_id=? AND lesson_date=? "
            "AND start_time=?",
            (subject_id, date_str, start_time),
        ).fetchone()
        return bool(row and row["filled"] == 1)


def notify(title, message):
    """Показывает локальное уведомление через plyer, если доступно.

    На ПК без бэкенда plyer тихо игнорирует (пишем в консоль как фолбэк).
    """
    try:
        from plyer import notification  # type: ignore
        notification.notify(title=title, message=message, app_name="Учёт занятий")
    except Exception:
        print(f"[NOTIFY] {title}: {message}")


def notify_unfilled():
    """Показывает уведомление о числе незаполненных занятий (если они есть)."""
    unfilled = compute_unfilled_slots()
    if unfilled:
        notify("Незаполненные занятия",
               f"Есть {len(unfilled)} незаполненных занятий. Откройте приложение.")
    return unfilled
