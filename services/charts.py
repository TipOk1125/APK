"""
services/charts.py — построение диаграмм на чистом Kivy Canvas.

Назначение: столбчатая диаграмма средних баллов и диаграмма посещаемости
без внешних зависимостей (без matplotlib) — это уменьшает размер APK и
делает облачную сборку надёжной. Обоснование см. docs/ARCHITECTURE.md.
Кто вызывает: экран отчётов (ui/screen_reports).
"""
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Line
from kivy.core.text import Label as CoreLabel


class BarChart(Widget):
    """Простая столбчатая диаграмма.

    data: список кортежей (подпись:str, значение:float). Значения None → 0.
    """

    def __init__(self, data=None, **kwargs):
        super().__init__(**kwargs)
        self.data = data or []
        self.bind(pos=self._redraw, size=self._redraw)

    def set_data(self, data):
        """Задаёт новые данные и перерисовывает."""
        self.data = data or []
        self._redraw()

    def _redraw(self, *args):
        """Перерисовывает столбцы по текущим размерам виджета."""
        self.canvas.clear()
        if not self.data:
            return
        values = [float(v or 0) for _, v in self.data]
        max_v = max(values) if values else 0
        max_v = max_v if max_v > 0 else 1
        n = len(self.data)
        pad = 10
        gap = 8
        base_y = self.y + 24  # место под подписи снизу
        avail_w = self.width - 2 * pad
        bar_w = max((avail_w - gap * (n - 1)) / n, 1)
        avail_h = self.height - 40
        with self.canvas:
            for i, (label, val) in enumerate(self.data):
                v = float(val or 0)
                h = (v / max_v) * avail_h
                x = self.x + pad + i * (bar_w + gap)
                Color(0.2, 0.5, 0.9, 1)
                Rectangle(pos=(x, base_y), size=(bar_w, h))
                # Подпись значения над столбцом.
                self._text(f"{v:g}", x, base_y + h + 2, bar_w)
                # Подпись категории под столбцом (обрезаем длинное).
                self._text(str(label)[:8], x, self.y, bar_w)

    def _text(self, text, x, y, w):
        """Рисует текстовую метку через CoreLabel как текстуру."""
        lbl = CoreLabel(text=text, font_size=12)
        lbl.refresh()
        tex = lbl.texture
        Color(0, 0, 0, 1)
        Rectangle(texture=tex, pos=(x, y), size=tex.size)


class AttendanceChart(Widget):
    """Диаграмма посещаемости: две полосы — присутствовал / отсутствовал."""

    def __init__(self, present=0, absent=0, **kwargs):
        super().__init__(**kwargs)
        self.present = present
        self.absent = absent
        self.bind(pos=self._redraw, size=self._redraw)

    def set_data(self, present, absent):
        """Задаёт количества и перерисовывает."""
        self.present = present
        self.absent = absent
        self._redraw()

    def _redraw(self, *args):
        """Перерисовывает две полосы посещаемости."""
        self.canvas.clear()
        total = self.present + self.absent
        if total <= 0:
            return
        with self.canvas:
            # Присутствовал — зелёная полоса.
            w_pres = self.width * (self.present / total)
            Color(0.2, 0.7, 0.3, 1)
            Rectangle(pos=(self.x, self.y + self.height / 2),
                      size=(w_pres, self.height / 3))
            # Отсутствовал — красная полоса.
            w_abs = self.width * (self.absent / total)
            Color(0.85, 0.3, 0.3, 1)
            Rectangle(pos=(self.x, self.y),
                      size=(w_abs, self.height / 3))
