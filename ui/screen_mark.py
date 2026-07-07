"""
ui/screen_mark.py — отметка занятия (F4, F5).

Сценарий:
    1. Выбор группы -> предмета -> даты/времени слота.
    2. Вопрос "Занятие было проведено?" (Да/Нет).
       Нет -> помечаем не проведено, в учёт не идёт.
       Да  -> список студентов; нажатие на имя переключает присутствие;
              долгое нажатие / кнопка оценки — ставит оценку.
    3. Сохранение фиксирует посещаемость; неотмеченные = отсутствовали.
"""
import os
from datetime import datetime

from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.properties import StringProperty, ListProperty
from kivy.uix.popup import Popup

import db
from services import attendance as attendance_service

Builder.load_file(os.path.join(os.path.dirname(__file__), "screen_mark.kv"))


class StudentRow(BoxLayout):
    """Строка студента: нажатие на имя переключает присутствие; кнопка — оценка."""

    def __init__(self, student_id, full_name, state_store, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = 44
        self.student_id = student_id
        self.state_store = state_store  # общий dict marked

        # Надпись-кнопка с именем: переключает присутствие.
        self.name_btn = Button(text=full_name, halign="left")
        self.name_btn.bind(on_release=self._toggle_present)
        self.add_widget(self.name_btn)

        # Кнопка выбора оценки.
        self.grade_btn = Button(text="Оценка", size_hint_x=None, width=110)
        self.grade_btn.bind(on_release=self._open_grade)
        self.add_widget(self.grade_btn)
        self._refresh_style()

    def _state(self):
        """Текущее состояние студента из общего хранилища."""
        return self.state_store.get(self.student_id, {"present": False, "grade": None})

    def _toggle_present(self, *args):
        """Переключает присутствие по нажатию на имя."""
        st = self._state()
        st = {"present": not st["present"], "grade": st["grade"]}
        # Если сняли присутствие — оценка тоже снимается.
        if not st["present"]:
            st["grade"] = None
        self.state_store[self.student_id] = st
        self._refresh_style()

    def _open_grade(self, *args):
        """Открывает попап выбора оценки (2..5). Оценка => присутствовал."""
        box = BoxLayout(orientation="horizontal", spacing=6, padding=6)
        popup = Popup(title="Оценка", size_hint=(0.8, 0.3))
        for g in (2, 3, 4, 5):
            b = Button(text=str(g))
            def make_cb(val):
                def cb(*a):
                    self.state_store[self.student_id] = {"present": True, "grade": val}
                    self._refresh_style()
                    popup.dismiss()
                return cb
            b.bind(on_release=make_cb(g))
            box.add_widget(b)
        clr = Button(text="Убрать")
        def clear_cb(*a):
            self.state_store[self.student_id] = {"present": True, "grade": None}
            self._refresh_style()
            popup.dismiss()
        clr.bind(on_release=clear_cb)
        box.add_widget(clr)
        popup.content = box
        popup.open()

    def _refresh_style(self):
        """Подсвечивает строку по состоянию присутствия/оценки."""
        st = self._state()
        if st["present"]:
            # Присутствовал — зелёный фон; показываем оценку, если есть.
            self.name_btn.background_color = (0.2, 0.7, 0.3, 1)
            self.grade_btn.text = f"Оценка: {st['grade']}" if st["grade"] else "Оценка"
        else:
            # Отсутствовал (по умолчанию) — серый.
            self.name_btn.background_color = (0.6, 0.6, 0.6, 1)
            self.grade_btn.text = "Оценка"


class MarkScreen(Screen):
    """Экран отметки занятия."""

    message = StringProperty("")
    groups = ListProperty([])
    subjects = ListProperty([])
    selected_group_id = None
    selected_subject_id = None

    def on_pre_enter(self, *args):
        rows = db.list_groups()
        self._group_map = {r["name"]: r["id"] for r in rows}
        self.groups = list(self._group_map.keys())
        self.marked = {}  # student_id -> {"present":bool,"grade":int|None}
        self.lesson_id = None

    def select_group(self, name):
        self.selected_group_id = self._group_map.get(name)
        rows = db.list_subjects(self.selected_group_id) if self.selected_group_id else []
        self._subject_map = {r["name"]: r["id"] for r in rows}
        self.subjects = list(self._subject_map.keys())

    def select_subject(self, name):
        self.selected_subject_id = getattr(self, "_subject_map", {}).get(name)

    def ask_conducted(self, date_str, time_str, conducted):
        """Ответ на вопрос "Занятие проведено?". Готовит занятие в БД."""
        if not self.selected_subject_id:
            self.message = "Выберите предмет"
            return
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")
        if not time_str:
            time_str = datetime.now().strftime("%H:%M")
        self.lesson_id = db.get_or_create_lesson(
            self.selected_subject_id, date_str, time_str)
        db.set_lesson_conducted(self.lesson_id, conducted)
        if not conducted:
            # Не проведено — в учёт не идёт, посещаемость не заполняем.
            self.message = "Отмечено: занятие НЕ проведено"
            self.ids.students_box.clear_widgets()
            return
        self.message = "Занятие проведено. Отметьте студентов (нажатие на имя)."
        self._build_student_rows()

    def _build_student_rows(self):
        """Строит строки студентов группы для отметки."""
        box = self.ids.students_box
        box.clear_widgets()
        self.marked = {}
        for s in db.list_students(self.selected_group_id):
            row = StudentRow(s["id"], s["full_name"], self.marked)
            box.add_widget(row)

    def save(self):
        """Сохраняет посещаемость: неотмеченные = отсутствовали."""
        if not self.lesson_id:
            self.message = "Сначала ответьте: занятие проведено?"
            return
        all_ids = [s["id"] for s in db.list_students(self.selected_group_id)]
        n = attendance_service.save_lesson_attendance(
            self.lesson_id, all_ids, self.marked)
        self.message = f"Сохранено. Записей: {n}"
