"""
test_db.py — нормализация имён и защита от дублей (UNIQUE).
"""
import pytest
import db


def test_normalize_name():
    assert db.normalize_name("  Иванов   Иван ") == "иванов иван"
    assert db.normalize_name(None) == ""


def test_group_duplicate_blocked():
    db.add_group("ИС-01")
    with pytest.raises(ValueError):
        db.add_group("  ис-01 ")  # тот же нормализованный ключ


def test_student_duplicate_blocked():
    gid = db.add_group("ИС-01")
    db.add_student(gid, "Иванов Иван")
    with pytest.raises(ValueError):
        db.add_student(gid, " иванов  иван ")


def test_subject_duplicate_blocked():
    gid = db.add_group("ИС-01")
    db.add_subject(gid, "Математика", 10)
    with pytest.raises(ValueError):
        db.add_subject(gid, "математика", 5)


def test_bulk_add_skips_duplicates():
    gid = db.add_group("ИС-01")
    text = "Иванов Иван\nПетров Пётр\nиванов иван\n\n  \nПетров Пётр"
    res = db.add_students_bulk(gid, text)
    assert res["added"] == 2
    assert res["skipped"] == 2
