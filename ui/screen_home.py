"""
ui/screen_home.py — главный экран: навигация и очередь незаполненных занятий.
"""
import os

from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty

from services import reminders, ics_export
import db

# Загружаем разметку экрана из .kv рядом с этим файлом.
Builder.load_file(os.path.join(os.path.dirname(__file__), "screen_home.kv"))


class HomeScreen(Screen):
    """Главный экран приложения."""

    status = StringProperty("")

    def on_pre_enter(self, *args):
        """Перед показом — пересчитываем незаполненные занятия."""
        unfilled = reminders.compute_unfilled_slots()
        if unfilled:
            self.status = f"Незаполненных занятий: {len(unfilled)}"
        else:
            self.status = "Нет незаполненных занятий"

    def export_schedule(self):
        """Кнопка "Экспорт расписания в календарь" — пишет schedule.ics."""
        # Собираем предметы со слотами расписания.
        items = []
        for s in db.list_subjects():
            slots = [(sl["weekday"], sl["start_time"])
                     for sl in db.list_schedule_slots(s["id"])]
            if slots:
                items.append({"subject": s["name"], "slots": slots})
        out_dir = _export_dir()
        path = os.path.join(out_dir, "schedule.ics")
        ics_export.write_ics(items, path)
        self.status = f"Расписание сохранено: {path}"


def _export_dir():
    """Каталог для экспортируемых файлов (доступный пользователю)."""
    try:
        from android.storage import primary_external_storage_path  # type: ignore
        base = primary_external_storage_path()
        out = os.path.join(base, "TeacherJournal")
    except Exception:
        out = os.path.join(os.path.dirname(os.path.dirname(__file__)), "exports")
    os.makedirs(out, exist_ok=True)
    return out
