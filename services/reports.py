"""
services/reports.py — расчёты ведомости, учёта занятий и экспорт (CSV/PDF).

Назначение:
    * пофамильная ведомость со средним баллом;
    * отчёт учёта занятий (план/факт/осталось/процент);
    * экспорт отчётов в CSV и PDF.
Кто вызывает: экран отчётов (ui/screen_reports).

Все величины учёта — в ЗАНЯТИЯХ, не в часах.
"""
import csv
import io
import os

import db


def gradebook(subject_id, group_id):
    """Пофамильная ведомость по предмету.

    Возврат: список dict со столбцами:
        full_name, avg_grade (float|None), grades_count, presences_no_grade.
    Средний балл считается только по выставленным оценкам (grade IS NOT NULL).
    "Посещений без оценки" — present=1 и grade IS NULL.
    """
    students = db.list_students(group_id)
    lesson_ids = [l["id"] for l in db.list_lessons(subject_id) if l["conducted"] == 1]

    # Собираем посещаемость по всем проведённым занятиям предмета.
    per_student = {s["id"]: {"grades": [], "pres_no_grade": 0} for s in students}
    for lid in lesson_ids:
        for a in db.get_attendance(lid):
            st = per_student.get(a["student_id"])
            if st is None:
                continue
            if a["grade"] is not None:
                st["grades"].append(a["grade"])
            elif a["present"] == 1:
                st["pres_no_grade"] += 1

    result = []
    for s in students:
        st = per_student[s["id"]]
        grades = st["grades"]
        avg = round(sum(grades) / len(grades), 2) if grades else None
        result.append({
            "full_name": s["full_name"],
            "avg_grade": avg,
            "grades_count": len(grades),
            "presences_no_grade": st["pres_no_grade"],
        })
    return result


def lesson_accounting(group_id=None):
    """Отчёт учёта занятий по предметам.

    Возврат: список dict со столбцами:
        subject, planned, conducted, remaining, percent.
    remaining = max(planned - conducted, 0); percent = conducted/planned*100.
    """
    subjects = db.list_subjects(group_id)
    rows = []
    for s in subjects:
        planned = s["planned_lessons"]
        conducted = db.count_conducted(s["id"])
        remaining = max(planned - conducted, 0)
        percent = round(conducted / planned * 100, 1) if planned > 0 else 0.0
        rows.append({
            "subject": s["name"],
            "planned": planned,
            "conducted": conducted,
            "remaining": remaining,
            "percent": percent,
        })
    return rows


def export_csv(rows, path):
    """Экспортирует список dict в CSV-файл. Возврат: путь к файлу.
    Пустой список — создаёт файл только с BOM (безопасно для пустых состояний).
    """
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        if not rows:
            f.write("")
            return path
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return path


def export_pdf(title, rows, path):
    """Экспортирует таблицу в PDF (reportlab, если доступен).

    Если reportlab недоступен (не в requirements по умолчанию) — падает назад
    к текстовому .txt рядом с указанным путём и возвращает его путь.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import cm
    except Exception:
        alt = os.path.splitext(path)[0] + ".txt"
        with open(alt, "w", encoding="utf-8") as f:
            f.write(title + "\n\n")
            for r in rows:
                f.write("; ".join(f"{k}={v}" for k, v in r.items()) + "\n")
        return alt

    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4
    y = height - 2 * cm
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2 * cm, y, title)
    y -= 1 * cm
    c.setFont("Helvetica", 10)
    if rows:
        headers = list(rows[0].keys())
        c.drawString(2 * cm, y, " | ".join(headers))
        y -= 0.6 * cm
        for r in rows:
            if y < 2 * cm:
                c.showPage()
                y = height - 2 * cm
                c.setFont("Helvetica", 10)
            line = " | ".join(str(r[h]) for h in headers)
            c.drawString(2 * cm, y, line)
            y -= 0.5 * cm
    c.save()
    return path
