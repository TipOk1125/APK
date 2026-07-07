"""
test_reports.py — средний балл, учёт занятий (план/проведено/осталось).
"""
import db
from services import reports, attendance


def _setup():
    gid = db.add_group("ИС-01")
    s1 = db.add_student(gid, "Иванов Иван")
    s2 = db.add_student(gid, "Петров Пётр")
    subj = db.add_subject(gid, "Математика", 5)
    return gid, s1, s2, subj


def test_accounting_counts():
    gid, s1, s2, subj = _setup()
    # Проводим 2 занятия, одно не проведено.
    l1 = db.get_or_create_lesson(subj, "2026-01-10", "09:00")
    db.set_lesson_conducted(l1, True)
    l2 = db.get_or_create_lesson(subj, "2026-01-11", "09:00")
    db.set_lesson_conducted(l2, True)
    l3 = db.get_or_create_lesson(subj, "2026-01-12", "09:00")
    db.set_lesson_conducted(l3, False)  # не проведено — не в учёт

    rows = reports.lesson_accounting(gid)
    row = [r for r in rows if r["subject"] == "Математика"][0]
    assert row["planned"] == 5
    assert row["conducted"] == 2
    assert row["remaining"] == 3
    assert row["percent"] == 40.0


def test_gradebook_average():
    gid, s1, s2, subj = _setup()
    l1 = db.get_or_create_lesson(subj, "2026-01-10", "09:00")
    db.set_lesson_conducted(l1, True)
    # s1: оценки 4 и 5 -> среднее 4.5; s2: присутствовал без оценки.
    attendance.save_lesson_attendance(l1, [s1, s2], {
        s1: {"present": True, "grade": 4},
    })
    l2 = db.get_or_create_lesson(subj, "2026-01-11", "09:00")
    db.set_lesson_conducted(l2, True)
    attendance.save_lesson_attendance(l2, [s1, s2], {
        s1: {"present": True, "grade": 5},
        s2: {"present": True, "grade": None},
    })
    rows = reports.gradebook(subj, gid)
    r1 = [r for r in rows if r["full_name"] == "Иванов Иван"][0]
    r2 = [r for r in rows if r["full_name"] == "Петров Пётр"][0]
    assert r1["avg_grade"] == 4.5
    assert r1["grades_count"] == 2
    assert r2["avg_grade"] is None
    assert r2["presences_no_grade"] == 1
