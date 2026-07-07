"""
test_attendance.py — авто-простановка "отсутствовал" для неотмеченных.
"""
from services import attendance


def test_unmarked_are_absent():
    records = attendance.build_records([1, 2, 3], {2: {"present": True, "grade": None}})
    by_id = {r["student_id"]: r for r in records}
    assert by_id[1]["present"] == 0   # не отмечен -> отсутствовал
    assert by_id[2]["present"] == 1   # отмечен
    assert by_id[3]["present"] == 0


def test_grade_implies_present():
    records = attendance.build_records([1], {1: {"present": False, "grade": 5}})
    assert records[0]["present"] == 1   # оценка => присутствовал
    assert records[0]["grade"] == 5
