def clean_required_text(value: str, field_name: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError(f"{field_name} не может быть пустым")
    return value


def clean_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def normalize_email(value: str) -> str:
    return clean_required_text(value, "Email").lower()


def normalize_optional_email(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip().lower()
    return value or None


def normalize_serial_number(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip().upper()
    return value or None