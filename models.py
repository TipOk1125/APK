"""
models.py — dataclass-модели сущностей предметной области.

Назначение: типизированное представление строк БД для передачи между слоями.
Кто вызывает: сервисы и UI (по желанию; БД возвращает sqlite3.Row, модели —
удобная типизированная обёртка).
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Group:
    """Группа студентов."""
    id: int
    name: str
    name_norm: str


@dataclass
class Student:
    """Студент, привязанный к группе."""
    id: int
    group_id: int
    full_name: str
    name_norm: str


@dataclass
class Subject:
    """Предмет, ведётся в конкретной группе. planned_lessons — план в занятиях."""
    id: int
    name: str
    name_norm: str
    group_id: int
    planned_lessons: int


@dataclass
class Lesson:
    """Конкретное занятие (дата+время). conducted/filled — статусы."""
    id: int
    subject_id: int
    lesson_date: str
    start_time: str
    conducted: int
    filled: int


@dataclass
class Attendance:
    """Посещаемость и оценка одного студента на одном занятии."""
    id: Optional[int]
    lesson_id: int
    student_id: int
    present: int
    grade: Optional[int]
