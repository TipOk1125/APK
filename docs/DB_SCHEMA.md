# Схема базы данных (SQLite)

Внешние ключи включаются на каждом соединении: `PRAGMA foreign_keys = ON;`

## Таблицы
### groups
- `id` PK; `name` — отображаемое имя; `name_norm` UNIQUE — нормализованное имя.

### students
- `id` PK; `group_id` FK→groups(CASCADE); `full_name`; `name_norm`.
- `UNIQUE(group_id, name_norm)` — студент уникален в рамках группы.

### subjects
- `id` PK; `name`; `name_norm`; `group_id` FK→groups(CASCADE);
  `planned_lessons` — план в **занятиях**.
- `UNIQUE(group_id, name_norm)`.

### schedule_slots
- `id` PK; `subject_id` FK→subjects(CASCADE); `weekday` (0=Пн..6=Вс);
  `start_time` 'HH:MM'. Шаблон для генерации слотов и `.ics`.

### lessons
- `id` PK; `subject_id` FK→subjects(CASCADE); `lesson_date` 'YYYY-MM-DD';
  `start_time` 'HH:MM'; `conducted` (1=идёт в учёт); `filled` (1=ответ получен).
- `UNIQUE(subject_id, lesson_date, start_time)` — занятие неповторяемо.

### attendance
- `id` PK; `lesson_id` FK→lessons(CASCADE); `student_id` FK→students(CASCADE);
  `present` (1=присутствовал); `grade` (NULL=без оценки).
- `UNIQUE(lesson_id, student_id)`.

## Правила учёта
- **Фактически проведено** = `COUNT(lessons WHERE conducted=1)`.
- **Осталось** = `max(planned_lessons − факт, 0)`.
- **Процент** = `факт / planned_lessons * 100`.
- **Средний балл студента** = `AVG(grade)` по его `attendance` с `grade IS NOT NULL`.
- **Посещений без оценки** = `present=1 AND grade IS NULL`.
