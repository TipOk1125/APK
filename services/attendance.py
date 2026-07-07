"""
services/attendance.py — логика отметки присутствия.

Назначение: собрать записи посещаемости из состояния UI, применив правило
"неотмеченный = отсутствовал", и сохранить их.
Кто вызывает: экран отметки (ui/screen_mark).
"""
import db


def build_records(all_student_ids, marked):
    """Строит полный список записей посещаемости.

    Аргументы:
        all_student_ids: список id всех студентов группы;
        marked: dict {student_id: {"present": bool, "grade": int|None}} —
                только те, кого преподаватель отметил.
    Возврат: список dict, готовый для db.save_attendance. Все неотмеченные
    студенты попадают как present=0 (отсутствовал) — это состояние по умолчанию.
    Правило: наличие оценки автоматически означает присутствие.
    """
    records = []
    for sid in all_student_ids:
        state = marked.get(sid)
        if state is None:
            # Неотмеченный студент = отсутствовал (по умолчанию).
            records.append({"student_id": sid, "present": 0, "grade": None})
            continue
        grade = state.get("grade")
        # Если есть оценка — считаем присутствовавшим независимо от флага.
        present = 1 if (state.get("present") or grade is not None) else 0
        records.append({"student_id": sid, "present": present, "grade": grade})
    return records


def save_lesson_attendance(lesson_id, all_student_ids, marked):
    """Сохраняет посещаемость занятия. Возврат: число сохранённых записей."""
    records = build_records(all_student_ids, marked)
    db.save_attendance(lesson_id, records)
    return len(records)
