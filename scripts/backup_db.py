from datetime import datetime

from db_utils import (
    ensure_backup_dir,
    find_pg_binary,
    get_db_parts,
    load_settings,
    require_docker_container,
    run_command,
)


def backup_via_local_pg_dump(settings: dict, db: dict, backup_file: str) -> None:
    pg_dump = find_pg_binary("pg_dump", settings["pg_bin_dir"])

    cmd = [
        pg_dump,
        "-h", db["host"],
        "-p", db["port"],
        "-U", db["username"],
        "-d", db["database"],
        "-F", "c",
        "-f", backup_file,
    ]

    print("Создание резервной копии через локальный pg_dump...")
    print("Файл:", backup_file)
    run_command(cmd)


def backup_via_docker(settings: dict, db: dict, backup_file: str) -> None:
    container = require_docker_container(settings["postgres_container"])
    temp_path = f"/tmp/{db['database']}.dump"

    print("Создание резервной копии через Docker...")
    print("Контейнер:", container)
    print("Файл:", backup_file)

    run_command([
        "docker", "exec", container,
        "pg_dump",
        "-U", db["username"],
        "-d", db["database"],
        "-F", "c",
        "-f", temp_path,
    ])

    run_command([
        "docker", "cp",
        f"{container}:{temp_path}",
        backup_file,
    ])

    run_command([
        "docker", "exec", container,
        "rm", "-f", temp_path,
    ])


def main():
    settings = load_settings()
    db = get_db_parts(settings["database_url"])
    backup_dir = ensure_backup_dir(settings["backup_dir"])

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = str(backup_dir / f"{db['database']}_{timestamp}.dump")

    if settings["db_in_docker"]:
        backup_via_docker(settings, db, backup_file)
    else:
        backup_via_local_pg_dump(settings, db, backup_file)

    print("Резервная копия успешно создана:")
    print(backup_file)


if __name__ == "__main__":
    main()