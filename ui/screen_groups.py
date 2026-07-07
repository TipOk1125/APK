"""
ui/screen_groups.py — создание групп и добавление студентов по одному.
Демонстрирует принцип "сначала выбор из списка, создание — отдельным действием".
"""
import os

from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty, ListProperty

import db

Builder.load_file(os.path.join(os.path.dirname(__file__), "screen_groups.kv"))


class GroupsScreen(Screen):
    """Экран управления группами и студентами."""

    message = StringProperty("")
    groups = ListProperty([])
    selected_group_id = None

    def on_pre_enter(self, *args):
        """Обновляем список групп при входе."""
        self.refresh_groups()

    def refresh_groups(self):
        """Перечитывает группы из БД в список для Spinner."""
        rows = db.list_groups()
        self._group_map = {r["name"]: r["id"] for r in rows}
        self.groups = list(self._group_map.keys())

    def create_group(self, name):
        """Создаёт новую группу (создание — отдельное действие)."""
        try:
            db.add_group(name)
            self.message = f"Группа '{name}' создана"
            self.refresh_groups()
        except ValueError as e:
            self.message = str(e)  # дубль или пустое имя

    def select_group(self, name):
        """Выбор существующей группы из списка."""
        self.selected_group_id = self._group_map.get(name)

    def add_one_student(self, full_name):
        """Добавляет одного студента в выбранную группу."""
        if not self.selected_group_id:
            self.message = "Сначала выберите группу"
            return
        try:
            db.add_student(self.selected_group_id, full_name)
            self.message = f"Студент '{full_name}' добавлен"
        except ValueError as e:
            self.message = str(e)  # дубль или пустое имя
