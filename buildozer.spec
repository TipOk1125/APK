[app]
title = Учет занятий
package.name = teacherjournal
package.domain = org.teacher
source.dir = .
source.include_exts = py,kv,png,jpg,ttf,ics
version = 1.0
requirements = python3,kivy,plyer,pillow
orientation = portrait
android.permissions = POST_NOTIFICATIONS
android.api = 34
android.minapi = 24
android.archs = arm64-v8a, armeabi-v7a
# Если добавите matplotlib/KivyMD/reportlab — впишите их в requirements выше.

[buildozer]
log_level = 2
