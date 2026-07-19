from datetime import datetime, timezone


def normalize_datetime(dt: datetime) -> datetime:
    """
    Вспомогательная функция для нормализации времени, чтобы не указывать часовые пояса вручную
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt
