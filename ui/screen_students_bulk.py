"""
ui/screen_students_bulk.py — массовое добавление студентов списком (F2).
"""
import os

from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty, ListProperty

import db

Builder.load_file(os.path.join(os.path.dirname(__file__), "screen_students_bulk.kv"))


class StudentsBulkScreen(Screen):
    """Экран массового ввода студентов."""

    message = StringProperty("")
    groups = ListProperty([])
    selected_group_id = None

    def on_pre_enter(self, *args):
        rows = db.list_groups()
        self._group_map = {r["name"]: r["id"] for r in rows}
        self.groups = list(self._group_map.keys())

    def select_group(self, name):
        """Выбор группы из списка."""
        self.selected_group_id = self._group_map.get(name)

    def save_bulk(self, raw_text):
        """Парсит многострочный ввод и сохраняет, показывая итог."""
        if not self.selected_group_id:
            self.message = "Сначала выберите группу"
            return
        res = db.add_students_bulk(self.selected_group_id, raw_text)
        # Итог: сколько добавлено и сколько дублей пропущено.
        self.message = f"Добавлено {res['added']}, пропущено дублей {res['skipped']}"
