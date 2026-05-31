import sys
from pathlib import Path

from db_utils import (
    find_pg_binary,
    get_db_parts,
    get_pg_env,
    load_settings,
    require_docker_container,
    run_command,
)


def recreate_public_schema_local(db: dict, psql: str) -> None:
    db_user = db["username"]

    commands = [
        "DROP SCHEMA IF EXISTS public CASCADE;",
        f"CREATE SCHEMA public AUTHORIZATION {db_user};",
        f"GRANT ALL ON SCHEMA public TO {db_user};",
        "GRANT ALL ON SCHEMA public TO public;",
    ]

    for sql in commands:
        run_command([
            psql,
            "-h", db["host"],
            "-p", db["port"],
            "-U", db["username"],
            "-d", db["database"],
            "-c", sql,
        ], env=get_pg_env(db))


def recreate_public_schema_docker(container: str, db: dict) -> None:
    db_user = db["username"]

    commands = [
        "DROP SCHEMA IF EXISTS public CASCADE;",
        f"CREATE SCHEMA public AUTHORIZATION {db_user};",
        f"GRANT ALL ON SCHEMA public TO {db_user};",
        "GRANT ALL ON SCHEMA public TO public;",
    ]

    for sql in commands:
        run_command([
            "docker", "exec", container,
            "psql",
            "-U", db["username"],
            "-d", db["database"],
            "-c", sql,
        ])


def restore_via_local_pg_restore(settings: dict, db: dict, backup_file: str) -> None:
    pg_restore = find_pg_binary("pg_restore", settings["pg_bin_dir"])
    psql = find_pg_binary("psql", settings["pg_bin_dir"])

    print("Очистка текущей схемы...")
    recreate_public_schema_local(db, psql)

    print("Восстановление через локальный pg_restore...")
    run_command([
        pg_restore,
        "-h", db["host"],
        "-p", db["port"],
        "-U", db["username"],
        "-d", db["database"],
        "--no-owner",
        "--no-privileges",
        backup_file,
    ], env=get_pg_env(db))


def restore_via_docker(settings: dict, db: dict, backup_file: str) -> None:
    container = require_docker_container(settings["postgres_container"])
    temp_path = f"/tmp/{Path(backup_file).name}"

    print("Копирование резервной копии в контейнер...")
    run_command([
        "docker", "cp",
        backup_file,
        f"{container}:{temp_path}",
    ])

    print("Очистка текущей схемы...")
    recreate_public_schema_docker(container, db)

    print("Восстановление через Docker...")
    run_command([
        "docker", "exec", container,
        "pg_restore",
        "-U", db["username"],
        "-d", db["database"],
        "--no-owner",
        "--no-privileges",
        temp_path,
    ])

    run_command([
        "docker", "exec", container,
        "rm", "-f", temp_path,
    ])


def main():
    if len(sys.argv) < 2:
        print("Использование:")
        print("python scripts/restore_db.py backups/имя_файла.dump")
        raise SystemExit(1)

    backup_file = Path(sys.argv[1])
    if not backup_file.exists():
        raise SystemExit(f"Файл не найден: {backup_file}")

    settings = load_settings()
    db = get_db_parts(settings["database_url"])

    print("ВНИМАНИЕ: текущая база будет очищена и восстановлена из резервной копии.")
    confirm = input(f"Продолжить восстановление базы '{db['database']}'? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("Восстановление отменено.")
        return

    if settings["db_in_docker"]:
        restore_via_docker(settings, db, str(backup_file))
    else:
        restore_via_local_pg_restore(settings, db, str(backup_file))

    print("Восстановление успешно завершено.")


if __name__ == "__main__":
    main()
