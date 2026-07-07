# Сборка APK

## Вариант A (рекомендуется): GitHub Actions — без Linux на вашем ПК
Вы не ставите ни Linux, ни Android Studio, ни buildozer — всё делает облачный
раннер GitHub.

1. Создайте бесплатный аккаунт и **новый репозиторий** на GitHub.
2. Загрузите туда содержимое папки `teacher_journal/` (включая
   `.github/workflows/build-apk.yml` и `buildozer.spec`). Через git:
   ```bash
   git init
   git add .
   git commit -m "init"
   git branch -M main
   git remote add origin https://github.com/USERNAME/REPO.git
   git push -u origin main
   ```
   (или загрузите файлы через кнопку «Add file» → «Upload files» в вебе).
3. Откройте вкладку **Actions** в репозитории → дождитесь завершения
   workflow **Build APK** (зелёная галочка). Первая сборка ~20–40 мин
   (качаются Android SDK/NDK), последующие быстрее.
4. Откройте завершённый запуск → блок **Artifacts** → скачайте
   **teacher-journal-apk** (zip с файлом `.apk` внутри).
5. Скопируйте `.apk` на телефон и установите (разрешите установку из
   неизвестных источников).

> Запустить сборку вручную можно кнопкой **Run workflow** (событие
> `workflow_dispatch`).

## Вариант B (запасной): WSL2 на Windows
1. В PowerShell (админ): `wsl --install` → перезагрузка → создайте пользователя Ubuntu.
2. В Ubuntu:
   ```bash
   sudo apt update && sudo apt install -y git zip openjdk-17-jdk python3-pip \
       autoconf libtool pkg-config zlib1g-dev libncurses5-dev libffi-dev libssl-dev
   pip3 install --user buildozer cython
   cd /path/to/teacher_journal
   buildozer -v android debug
   ```
3. Готовый `.apk` появится в каталоге `bin/`.

## Файлы сборки
- `.github/workflows/build-apk.yml` — облачный workflow.
- `buildozer.spec` — конфиг p4a/buildozer (requirements, permissions, api).
