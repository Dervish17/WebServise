import os
import shutil
import subprocess
from contextlib import contextmanager
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import make_url


def load_settings():
    load_dotenv()

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")

    backup_dir = os.getenv("BACKUP_DIR", "backups")
    pg_bin_dir = os.getenv("PG_BIN_DIR", "").strip()
    db_in_docker = os.getenv("DB_IN_DOCKER", "false").strip().lower() == "true"
    postgres_container = os.getenv("POSTGRES_CONTAINER", "").strip()

    return {
        "database_url": database_url,
        "backup_dir": backup_dir,
        "pg_bin_dir": pg_bin_dir,
        "db_in_docker": db_in_docker,
        "postgres_container": postgres_container,
    }


def get_db_parts(database_url: str) -> dict:
    url = make_url(database_url)

    return {
        "drivername": url.drivername,
        "username": url.username or "",
        "password": url.password or "",
        "host": url.host or "localhost",
        "port": str(url.port or 5432),
        "database": url.database or "",
    }


def ensure_backup_dir(path: str) -> Path:
    backup_path = Path(path)
    backup_path.mkdir(parents=True, exist_ok=True)
    return backup_path


def find_pg_binary(binary_name: str, pg_bin_dir: str = "") -> str:
    if pg_bin_dir:
        candidate = Path(pg_bin_dir) / binary_name
        if os.name == "nt":
            candidate_exe = candidate.with_suffix(".exe")
            if candidate_exe.exists():
                return str(candidate_exe)
        if candidate.exists():
            return str(candidate)

    from_path = shutil.which(binary_name)
    if from_path:
        return from_path

    if os.name == "nt":
        common_roots = [
            Path("C:/Program Files/PostgreSQL"),
            Path("C:/Program Files (x86)/PostgreSQL"),
        ]
        for root in common_roots:
            if root.exists():
                for version_dir in sorted(root.iterdir(), reverse=True):
                    candidate = version_dir / "bin" / f"{binary_name}.exe"
                    if candidate.exists():
                        return str(candidate)

    raise RuntimeError(
        f"Не удалось найти {binary_name}. Укажи PG_BIN_DIR в .env "
        f"или добавь PostgreSQL bin в PATH."
    )


def require_docker_container(container_name: str) -> str:
    if not container_name:
        raise RuntimeError(
            "POSTGRES_CONTAINER не задан в .env. "
            "Укажи имя контейнера PostgreSQL."
        )
    return container_name


def get_pg_env(db: dict) -> dict[str, str]:
    env = os.environ.copy()
    if db["password"]:
        env["PGPASSWORD"] = db["password"]
    return env


@contextmanager
def backup_lock(backup_dir: Path):
    lock_file = backup_dir / ".backup.lock"
    file = lock_file.open("a+", encoding="utf-8")

    try:
        if os.name == "nt":
            import msvcrt

            file.seek(0)
            if not file.read(1):
                file.seek(0)
                file.write(" ")
                file.flush()
            file.seek(0)
            msvcrt.locking(file.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        file.close()
        raise RuntimeError(
            "Резервное копирование уже выполняется."
        )

    try:
        yield
    finally:
        if os.name == "nt":
            file.seek(0)
            msvcrt.locking(file.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            fcntl.flock(file.fileno(), fcntl.LOCK_UN)
        file.close()


def run_command(cmd: list[str], *, env: dict[str, str] | None = None) -> None:
    result = subprocess.run(cmd, text=True, env=env)
    if result.returncode != 0:
        raise SystemExit(f"Ошибка выполнения команды: {' '.join(cmd)}")
