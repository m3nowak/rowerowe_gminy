from datetime import UTC, datetime, timedelta

from rg_app.db.models import User

BACKLOG_TRIGGER_TIMEOUT = timedelta(days=14)

AUTH_COOKIE_NAME = "rg-auth"


def user_check_last_trigger(user: User) -> bool:
    """
    Check if the user is eligible for backlog trigger
    """
    return user.last_backlog_sync is None or user.last_backlog_sync + BACKLOG_TRIGGER_TIMEOUT < datetime.now(UTC)
