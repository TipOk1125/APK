"""
conftest.py — общая настройка тестов: временная БД в отдельном файле.
Подменяем путь к БД, чтобы тесты не трогали рабочий файл.
"""
import os
import tempfile
import pytest

import db


@pytest.fixture(autouse=True)
def temp_db(monkeypatch):
    """Каждый тест — на свежей временной БД."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    monkeypatch.setattr(db, "get_db_path", lambda: path)
    db.init_db()
    yield
    os.remove(path)
