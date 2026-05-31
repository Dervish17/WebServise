import os
import subprocess
import sys
import threading
from datetime import datetime, timedelta
from pathlib import Path


_scheduler_thread: threading.Thread | None = None
_stop_event = threading.Event()


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _get_next_run_time(backup_time: str) -> datetime:
    hour, minute = map(int, backup_time.split(":"))

    now = datetime.now()
    next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

    if next_run <= now:
        next_run += timedelta(days=1)

    return next_run


def _cleanup_old_backups(backup_dir: Path, keep_last: int) -> None:
    if keep_last <= 0 or not backup_dir.exists():
        return

    backup_files = sorted(
        backup_dir.glob("*.dump"),
        key=lambda file: file.stat().st_mtime,
        reverse=True,
    )

    for old_backup in backup_files[keep_last:]:
        old_backup.unlink(missing_ok=True)


def _get_keep_last() -> int:
    keep_last = int(os.getenv("BACKUP_KEEP_LAST", "10"))
    if keep_last <= 0:
        raise ValueError("BACKUP_KEEP_LAST must be greater than zero")
    return keep_last


def _run_backup() -> None:
    root = _project_root()
    script_path = root / "scripts" / "backup_db.py"

    if not script_path.exists():
        print("[backup] Скрипт backup_db.py не найден")
        return

    print("[backup] Запуск автоматического резервного копирования")

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(root),
            text=True,
            capture_output=True,
        )
    except Exception as error:
        print(f"[backup] Не удалось запустить резервное копирование: {error}")
        return

    if result.returncode == 0:
        print("[backup] Резервная копия успешно создана")

        backup_dir_name = os.getenv("BACKUP_DIR", "backups")
        try:
            _cleanup_old_backups(root / backup_dir_name, _get_keep_last())
        except (OSError, ValueError) as error:
            print(f"[backup] Не удалось удалить старые резервные копии: {error}")
    else:
        print("[backup] Ошибка при создании резервной копии")
        print(result.stderr)


def _scheduler_loop() -> None:
    backup_time = os.getenv("AUTO_BACKUP_TIME", "02:00")

    while not _stop_event.is_set():
        try:
            next_run = _get_next_run_time(backup_time)
        except ValueError as error:
            print(f"[backup] Некорректное значение AUTO_BACKUP_TIME={backup_time!r}: {error}")
            return
        print(f"[backup] Следующее резервное копирование: {next_run:%Y-%m-%d %H:%M}")

        while datetime.now() < next_run:
            if _stop_event.wait(timeout=30):
                return

        _run_backup()


def start_backup_scheduler() -> None:
    global _scheduler_thread

    enabled = os.getenv("AUTO_BACKUP_ENABLED", "false").lower() == "true"
    if not enabled:
        print("[backup] Автоматическое резервное копирование отключено")
        return

    if _scheduler_thread and _scheduler_thread.is_alive():
        return

    try:
        _get_next_run_time(os.getenv("AUTO_BACKUP_TIME", "02:00"))
        _get_keep_last()
    except ValueError as error:
        print(f"[backup] Некорректные настройки автоматического резервного копирования: {error}")
        return

    _stop_event.clear()

    _scheduler_thread = threading.Thread(
        target=_scheduler_loop,
        name="backup-scheduler",
        daemon=True,
    )
    _scheduler_thread.start()


def stop_backup_scheduler() -> None:
    _stop_event.set()
