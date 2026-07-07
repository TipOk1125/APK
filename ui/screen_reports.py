"""
ui/screen_reports.py — ведомость, отчёт учёта занятий, диаграммы, экспорт.
"""
import os

from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.uix.label import Label
from kivy.properties import StringProperty, ListProperty

import db
from services import reports
from services.charts import BarChart, AttendanceChart

Builder.load_file(os.path.join(os.path.dirname(__file__), "screen_reports.kv"))


class ReportsScreen(Screen):
    """Экран отчётов и ведомости."""

    message = StringProperty("")
    groups = ListProperty([])
    subjects = ListProperty([])
    selected_group_id = None
    selected_subject_id = None

    def on_pre_enter(self, *args):
        rows = db.list_groups()
        self._group_map = {r["name"]: r["id"] for r in rows}
        self.groups = list(self._group_map.keys())

    def select_group(self, name):
        self.selected_group_id = self._group_map.get(name)
        rows = db.list_subjects(self.selected_group_id) if self.selected_group_id else []
        self._subject_map = {r["name"]: r["id"] for r in rows}
        self.subjects = list(self._subject_map.keys())

    def select_subject(self, name):
        self.selected_subject_id = getattr(self, "_subject_map", {}).get(name)

    def show_gradebook(self):
        """Показывает пофамильную ведомость + диаграмму средних баллов."""
        if not (self.selected_group_id and self.selected_subject_id):
            self.message = "Выберите группу и предмет"
            return
        rows = reports.gradebook(self.selected_subject_id, self.selected_group_id)
        box = self.ids.report_box
        box.clear_widgets()
        if not rows:
            box.add_widget(Label(text="Нет данных", size_hint_y=None, height=30))
            return
        # Текстовая ведомость.
        for r in rows:
            avg = r["avg_grade"] if r["avg_grade"] is not None else "—"
            txt = (f"{r['full_name']}: ср.балл {avg}, "
                   f"оценок {r['grades_count']}, "
                   f"посещ. без оценки {r['presences_no_grade']}")
            box.add_widget(Label(text=txt, size_hint_y=None, height=28))
        # Диаграмма средних баллов.
        chart = BarChart(data=[(r["full_name"], r["avg_grade"] or 0) for r in rows],
                         size_hint_y=None, height=220)
        box.add_widget(chart)
        self.message = "Ведомость построена"

    def show_accounting(self):
        """Показывает отчёт учёта занятий (план/факт/осталось)."""
        rows = reports.lesson_accounting(self.selected_group_id)
        box = self.ids.report_box
        box.clear_widgets()
        if not rows:
            box.add_widget(Label(text="Нет предметов", size_hint_y=None, height=30))
            return
        for r in rows:
            txt = (f"{r['subject']}: план {r['planned']}, проведено {r['conducted']}, "
                   f"осталось {r['remaining']} ({r['percent']}%)")
            box.add_widget(Label(text=txt, size_hint_y=None, height=28))
        self.message = "Отчёт учёта занятий построен (в занятиях)"

    def export(self, fmt):
        """Экспорт текущего отчёта учёта занятий в CSV или PDF."""
        rows = reports.lesson_accounting(self.selected_group_id)
        out_dir = _export_dir()
        if fmt == "csv":
            path = reports.export_csv(rows, os.path.join(out_dir, "accounting.csv"))
        else:
            path = reports.export_pdf("Отчёт учёта занятий", rows,
                                      os.path.join(out_dir, "accounting.pdf"))
        self.message = f"Экспортировано: {path}"


def _export_dir():
    """Каталог для экспортируемых файлов."""
    try:
        from android.storage import primary_external_storage_path  # type: ignore
        out = os.path.join(primary_external_storage_path(), "TeacherJournal")
    except Exception:
        out = os.path.join(os.path.dirname(os.path.dirname(__file__)), "exports")
    os.makedirs(out, exist_ok=True)
    return out
