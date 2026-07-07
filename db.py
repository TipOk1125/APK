"""
db.py — слой доступа к данным (SQLite).

Назначение:
    * инициализация схемы БД;
    * нормализация имён (защита от дублей);
    * низкоуровневые CRUD-операции.

Кто вызывает: сервисы (services/*) и экраны UI (ui/*).

Все SQL-запросы параметризованы. Внешние ключи включаются на каждом
соединении (PRAGMA foreign_keys = ON).
"""
import os
import re
import sqlite3
from contextlib import contextmanager

# Имя файла БД. Файл лежит в приватном каталоге приложения.
DB_FILENAME = "teacher_journal.db"


def get_db_path():
    """Возвращает абсолютный путь к файлу БД.

    На Android используем приватный каталог приложения (android.storage),
    на ПК — каталог рядом с модулем. Каталог при необходимости создаётся.
    """
    try:
        # На Android доступен модуль android.storage (внутри APK).
        from android.storage import app_storage_path  # type: ignore
        base = app_storage_path()
    except Exception:
        # На ПК — каталог текущего модуля.
        base = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, DB_FILENAME)


def normalize_name(name):
    """Нормализует имя для сравнения на дубли.

    Аргументы:
        name: исходная строка (может быть None).
    Возврат:
        строка в нижнем регистре с обрезанными краями и схлопнутыми пробелами.
    """
    return re.sub(r"\s+", " ", (name or "").strip()).lower()


@contextmanager
def get_connection():
    """Контекстный менеджер соединения с БД.

    Побочные эффекты: открывает соединение, включает внешние ключи,
    коммитит при успешном выходе, всегда закрывает соединение.
    """
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row  # доступ к колонкам по имени
    conn.execute("PRAGMA foreign_keys = ON;")  # каскадные удаления/FK
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


# --- DDL: определение схемы. Точно по спецификации из супер-промта. ---
SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS groups (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        name      TEXT NOT NULL,
        name_norm TEXT NOT NULL UNIQUE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS students (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id  INTEGER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
        full_name TEXT NOT NULL,
        name_norm TEXT NOT NULL,
        UNIQUE(group_id, name_norm)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS subjects (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        name            TEXT NOT NULL,
        name_norm       TEXT NOT NULL,
        group_id        INTEGER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
        planned_lessons INTEGER NOT NULL DEFAULT 0,
        UNIQUE(group_id, name_norm)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS schedule_slots (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
        weekday    INTEGER NOT NULL,
        start_time TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS lessons (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_id  INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
        lesson_date TEXT NOT NULL,
        start_time  TEXT NOT NULL,
        conducted   INTEGER NOT NULL DEFAULT 0,
        filled      INTEGER NOT NULL DEFAULT 0,
        UNIQUE(subject_id, lesson_date, start_time)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS attendance (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        lesson_id  INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
        student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
        present    INTEGER NOT NULL DEFAULT 0,
        grade      INTEGER,
        UNIQUE(lesson_id, student_id)
    );
    """,
]


def init_db():
    """Создаёт все таблицы, если их ещё нет. Идемпотентно."""
    with get_connection() as conn:
        for ddl in SCHEMA:
            conn.execute(ddl)


# ----------------------------- Группы --------------------------------
def add_group(name):
    """Добавляет группу. Возврат: id.
    Бросает ValueError, если группа с таким нормализованным именем уже есть.
    """
    norm = normalize_name(name)
    if not norm:
        raise ValueError("Название группы не может быть пустым")
    with get_connection() as conn:
        try:
            cur = conn.execute(
                "INSERT INTO groups(name, name_norm) VALUES(?, ?)",
                (name.strip(), norm),
            )
            return cur.lastrowid
        except sqlite3.IntegrityError:
            raise ValueError("Такая группа уже существует")


def list_groups():
    """Возвращает список групп (Row: id, name, name_norm)."""
    with get_connection() as conn:
        return conn.execute(
            "SELECT id, name, name_norm FROM groups ORDER BY name"
        ).fetchall()


# ---------------------------- Студенты -------------------------------
def add_student(group_id, full_name):
    """Добавляет одного студента в группу. Возврат: id.
    Бросает ValueError при дубле или пустом имени.
    """
    norm = normalize_name(full_name)
    if not norm:
        raise ValueError("ФИО не может быть пустым")
    with get_connection() as conn:
        try:
            cur = conn.execute(
                "INSERT INTO students(group_id, full_name, name_norm) "
                "VALUES(?, ?, ?)",
                (group_id, full_name.strip(), norm),
            )
            return cur.lastrowid
        except sqlite3.IntegrityError:
            raise ValueError("Такой студент уже есть в этой группе")


def add_students_bulk(group_id, raw_text):
    """Массовое добавление студентов из многострочного текста.

    Аргументы:
        group_id: id группы;
        raw_text: текст, где каждая строка = одно ФИО.
    Возврат: dict {"added": N, "skipped": M} — добавлено и пропущено дублей.
    Побочные эффекты: пишет в таблицу students; дубли пропускаются.
    """
    added = 0
    skipped = 0
    seen = set()  # нормализованные имена, встреченные в этом же вводе
    with get_connection() as conn:
        for line in (raw_text or "").splitlines():
            name = line.strip()
            if not name:
                continue  # пустые строки пропускаем
            norm = normalize_name(name)
            if norm in seen:
                skipped += 1  # дубль внутри самого ввода
                continue
            seen.add(norm)
            try:
                conn.execute(
                    "INSERT INTO students(group_id, full_name, name_norm) "
                    "VALUES(?, ?, ?)",
                    (group_id, name, norm),
                )
                added += 1
            except sqlite3.IntegrityError:
                skipped += 1  # дубль относительно уже сохранённых в БД
    return {"added": added, "skipped": skipped}


def list_students(group_id):
    """Список студентов группы (Row: id, full_name)."""
    with get_connection() as conn:
        return conn.execute(
            "SELECT id, full_name FROM students WHERE group_id=? "
            "ORDER BY full_name",
            (group_id,),
        ).fetchall()


# ---------------------------- Предметы -------------------------------
def add_subject(group_id, name, planned_lessons):
    """Добавляет предмет в группу. Возврат: id.
    planned_lessons — плановое число ЗАНЯТИЙ (не часов).
    """
    norm = normalize_name(name)
    if not norm:
        raise ValueError("Название предмета не может быть пустым")
    try:
        planned = int(planned_lessons)
    except (TypeError, ValueError):
        raise ValueError("Плановое число занятий должно быть целым")
    with get_connection() as conn:
        try:
            cur = conn.execute(
                "INSERT INTO subjects(name, name_norm, group_id, planned_lessons) "
                "VALUES(?, ?, ?, ?)",
                (name.strip(), norm, group_id, planned),
            )
            return cur.lastrowid
        except sqlite3.IntegrityError:
            raise ValueError("Такой предмет уже есть в этой группе")


def list_subjects(group_id=None):
    """Список предметов. Если group_id задан — только для этой группы."""
    with get_connection() as conn:
        if group_id is None:
            return conn.execute(
                "SELECT s.id, s.name, s.group_id, s.planned_lessons, g.name AS group_name "
                "FROM subjects s JOIN groups g ON g.id=s.group_id ORDER BY s.name"
            ).fetchall()
        return conn.execute(
            "SELECT id, name, group_id, planned_lessons FROM subjects "
            "WHERE group_id=? ORDER BY name",
            (group_id,),
        ).fetchall()


# --------------------------- Расписание ------------------------------
def add_schedule_slot(subject_id, weekday, start_time):
    """Добавляет слот расписания (шаблон). weekday: 0=Пн..6=Вс, time='HH:MM'."""
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO schedule_slots(subject_id, weekday, start_time) "
            "VALUES(?, ?, ?)",
            (subject_id, int(weekday), start_time),
        )
        return cur.lastrowid


def list_schedule_slots(subject_id=None):
    """Список слотов расписания (опц. для одного предмета)."""
    with get_connection() as conn:
        if subject_id is None:
            return conn.execute(
                "SELECT id, subject_id, weekday, start_time FROM schedule_slots"
            ).fetchall()
        return conn.execute(
            "SELECT id, subject_id, weekday, start_time FROM schedule_slots "
            "WHERE subject_id=?",
            (subject_id,),
        ).fetchall()


# ----------------------------- Занятия -------------------------------
def get_or_create_lesson(subject_id, lesson_date, start_time):
    """Возвращает id занятия по (subject, date, time), создаёт при отсутствии.

    UNIQUE(subject_id, lesson_date, start_time) гарантирует неповторяемость.
    """
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM lessons WHERE subject_id=? AND lesson_date=? "
            "AND start_time=?",
            (subject_id, lesson_date, start_time),
        ).fetchone()
        if row:
            return row["id"]
        cur = conn.execute(
            "INSERT INTO lessons(subject_id, lesson_date, start_time, "
            "conducted, filled) VALUES(?, ?, ?, 0, 0)",
            (subject_id, lesson_date, start_time),
        )
        return cur.lastrowid


def set_lesson_conducted(lesson_id, conducted):
    """Помечает занятие проведённым/непроведённым и как заполненное (filled=1)."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE lessons SET conducted=?, filled=1 WHERE id=?",
            (1 if conducted else 0, lesson_id),
        )


def list_lessons(subject_id):
    """Список занятий предмета (Row: id, lesson_date, start_time, conducted, filled)."""
    with get_connection() as conn:
        return conn.execute(
            "SELECT id, lesson_date, start_time, conducted, filled FROM lessons "
            "WHERE subject_id=? ORDER BY lesson_date, start_time",
            (subject_id,),
        ).fetchall()


def count_conducted(subject_id):
    """Число фактически проведённых занятий (conducted=1) по предмету."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COUNT(1) AS c FROM lessons WHERE subject_id=? AND conducted=1",
            (subject_id,),
        ).fetchone()
        return row["c"]


# --------------------------- Посещаемость ----------------------------
def save_attendance(lesson_id, records):
    """Сохраняет посещаемость занятия.

    Аргументы:
        lesson_id: id занятия;
        records: список dict {"student_id": int, "present": 0/1, "grade": int|None}.
    Побочные эффекты: перезаписывает записи attendance для этого занятия
    (UPSERT по UNIQUE(lesson_id, student_id)).
    """
    with get_connection() as conn:
        for r in records:
            conn.execute(
                "INSERT INTO attendance(lesson_id, student_id, present, grade) "
                "VALUES(?, ?, ?, ?) "
                "ON CONFLICT(lesson_id, student_id) DO UPDATE SET "
                "present=excluded.present, grade=excluded.grade",
                (lesson_id, r["student_id"], 1 if r.get("present") else 0,
                 r.get("grade")),
            )


def get_attendance(lesson_id):
    """Записи посещаемости занятия (Row: student_id, present, grade)."""
    with get_connection() as conn:
        return conn.execute(
            "SELECT student_id, present, grade FROM attendance WHERE lesson_id=?",
            (lesson_id,),
        ).fetchall()
