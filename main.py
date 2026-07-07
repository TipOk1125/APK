"""
main.py — точка входа Kivy-приложения "Учёт занятий".

Назначение: инициализация БД, регистрация экранов, запуск ScreenManager.
При старте проверяет незаполненные занятия и показывает уведомление.
Запуск на ПК: python main.py
"""
import os
import sys

# Гарантируем, что корень пакета в sys.path (для запуска и как скрипт, и как модуль).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window

import db
from services import reminders

# Импортируем классы экранов (регистрируют себя в ScreenManager через .kv).
from ui.screen_home import HomeScreen
from ui.screen_groups import GroupsScreen
from ui.screen_students_bulk import StudentsBulkScreen
from ui.screen_subjects import SubjectsScreen
from ui.screen_mark import MarkScreen
from ui.screen_reports import ReportsScreen


class TeacherJournalApp(App):
    """Главный класс приложения."""

    title = "Учёт занятий"

    def build(self):
        """Собирает ScreenManager и регистрирует все экраны."""
        db.init_db()  # идемпотентная инициализация схемы
        sm = ScreenManager()
        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(GroupsScreen(name="groups"))
        sm.add_widget(StudentsBulkScreen(name="students_bulk"))
        sm.add_widget(SubjectsScreen(name="subjects"))
        sm.add_widget(MarkScreen(name="mark"))
        sm.add_widget(ReportsScreen(name="reports"))
        return sm

    def on_start(self):
        """При запуске — проверяем незаполненные занятия и уведомляем."""
        try:
            reminders.notify_unfilled()
        except Exception as e:
            print("Проверка напоминаний не удалась:", e)


def main():
    """Точка входа для запуска на ПК."""
    TeacherJournalApp().run()


if __name__ == "__main__":
    main()
