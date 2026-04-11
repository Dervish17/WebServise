from collections import defaultdict, deque
from time import monotonic

from fastapi import HTTPException, status

WINDOW_SECONDS = 300
MAX_ATTEMPTS = 5
BLOCK_SECONDS = 600

_attempts: dict[str, deque[float]] = defaultdict(deque)
_blocked_until: dict[str, float] = {}


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _make_key(ip: str, email: str) -> str:
    return f"{ip}:{_normalize_email(email)}"


def _prune_attempts(key: str, now: float) -> None:
    queue = _attempts[key]
    while queue and now - queue[0] > WINDOW_SECONDS:
        queue.popleft()

    if not queue:
        _attempts.pop(key, None)


def ensure_login_allowed(ip: str, email: str) -> None:
    now = monotonic()
    key = _make_key(ip, email)

    blocked_until = _blocked_until.get(key)
    if blocked_until and now < blocked_until:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Слишком много попыток входа. Подождите 10 минут.",
        )

    if blocked_until and now >= blocked_until:
        _blocked_until.pop(key, None)

    _prune_attempts(key, now)


def record_failed_login(ip: str, email: str) -> None:
    now = monotonic()
    key = _make_key(ip, email)

    _prune_attempts(key, now)

    queue = _attempts[key]
    queue.append(now)

    if len(queue) >= MAX_ATTEMPTS:
        _blocked_until[key] = now + BLOCK_SECONDS
        _attempts.pop(key, None)


def clear_login_failures(ip: str, email: str) -> None:
    key = _make_key(ip, email)
    _attempts.pop(key, None)
    _blocked_until.pop(key, None)