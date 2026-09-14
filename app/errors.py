"""Сообщения об ошибках на русском языке.

Ошибки формата ввода приходят от схем Pydantic (app/schemas.py),
ошибки целостности приходят от PostgreSQL.
"""

import asyncpg
from fastapi.exceptions import RequestValidationError

# Ключ словаря повторяет имя ограничения из sql/01_schema.sql.
CONSTRAINT_MESSAGES: dict[str, str] = {
    "songs_rating_check": "Рейтинг песни должен быть целым числом от 1 до 10.",
    "songs_title_uk": "У этого исполнителя уже есть песня с таким названием.",
    "songs_genre_id_fkey": "Указан несуществующий жанр.",
    "artists_name_key": "Исполнитель с таким именем уже есть в базе.",
    "genres_name_key": "Такой жанр уже есть в справочнике.",
    "playlists_name_key": "Плейлист с таким названием уже существует.",
    "playlist_songs_pkey": "Эта песня уже добавлена в плейлист.",
}

FIELD_LABELS: dict[str, str] = {
    "name": "Название",
    "title": "Название",
    "debut_year": "Год появления исполнителя",
    "release_year": "Год выпуска",
    "year": "Год вручения",
    "rating": "Рейтинг",
    "artist_id": "Исполнитель",
    "genre_id": "Жанр",
    "album_id": "Альбом",
    "song_id": "Песня",
}

# Типы ошибок Pydantic, которые может увидеть пользователь формы.
PYDANTIC_MESSAGES: dict[str, str] = {
    "missing": "не заполнено",
    "string_too_short": "не может быть пустым",
    "string_too_long": "слишком длинное",
    "int_parsing": "должно быть целым числом",
    "greater_than_equal": "меньше допустимого значения",
    "less_than_equal": "больше допустимого значения",
}


def human_message(exc: asyncpg.PostgresError) -> str:
    """Текст ошибки базы данных."""
    # Жанр защищён правилом ON DELETE RESTRICT, для него PostgreSQL
    # поднимает отдельный класс ошибки.
    if isinstance(exc, asyncpg.RestrictViolationError):
        return "Жанр нельзя удалить: он используется в песнях."

    constraint = getattr(exc, "constraint_name", None)
    if constraint in CONSTRAINT_MESSAGES:
        return CONSTRAINT_MESSAGES[constraint]

    return f"Ошибка базы данных: {exc}"


def form_error_message(exc: RequestValidationError) -> str:
    """Текст ошибки заполнения формы по первому непройденному полю."""
    error = exc.errors()[0]
    field = str(error["loc"][-1])
    label = FIELD_LABELS.get(field, field)
    reason = PYDANTIC_MESSAGES.get(error["type"], "заполнено неверно")
    return f"Поле «{label}»: {reason}."
