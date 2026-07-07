"""
ui/screen_subjects.py — создание предметов (план в занятиях) и слотов расписания.
"""
import os

from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty, ListProperty

import db

Builder.load_file(os.path.join(os.path.dirname(__file__), "screen_subjects.kv"))

# Дни недели для Spinner (индекс = weekday 0..6).
WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]


class SubjectsScreen(Screen):
    """Экран предметов и расписания."""

    message = StringProperty("")
    groups = ListProperty([])
    subjects = ListProperty([])
    weekdays = ListProperty(WEEKDAYS)
    selected_group_id = None
    selected_subject_id = None

    def on_pre_enter(self, *args):
        rows = db.list_groups()
        self._group_map = {r["name"]: r["id"] for r in rows}
        self.groups = list(self._group_map.keys())

    def select_group(self, name):
        """Выбор группы; обновляет список её предметов."""
        self.selected_group_id = self._group_map.get(name)
        self.refresh_subjects()

    def refresh_subjects(self):
        """Перечитывает предметы выбранной группы."""
        if not self.selected_group_id:
            self.subjects = []
            return
        rows = db.list_subjects(self.selected_group_id)
        self._subject_map = {r["name"]: r["id"] for r in rows}
        self.subjects = list(self._subject_map.keys())

    def create_subject(self, name, planned):
        """Создаёт предмет с плановым числом ЗАНЯТИЙ."""
        if not self.selected_group_id:
            self.message = "Сначала выберите группу"
            return
        try:
            db.add_subject(self.selected_group_id, name, planned or 0)
            self.message = f"Предмет '{name}' создан"
            self.refresh_subjects()
        except ValueError as e:
            self.message = str(e)

    def select_subject(self, name):
        """Выбор предмета из списка."""
        self.selected_subject_id = getattr(self, "_subject_map", {}).get(name)

    def add_slot(self, weekday_label, start_time):
        """Добавляет слот расписания к выбранному предмету."""
        if not self.selected_subject_id:
            self.message = "Сначала выберите предмет"
            return
        try:
            weekday = WEEKDAYS.index(weekday_label)
        except ValueError:
            self.message = "Выберите день недели"
            return
        if not start_time or ":" not in start_time:
            self.message = "Время в формате HH:MM"
            return
        db.add_schedule_slot(self.selected_subject_id, weekday, start_time)
        self.message = f"Слот добавлен: {weekday_label} {start_time}"
