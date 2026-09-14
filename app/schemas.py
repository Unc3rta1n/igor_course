"""Схемы форм. Pydantic проверяет формат данных до обращения к базе.

База данных проверяет только ограничения предметной области из задания:
рейтинг от 1 до 10, уникальность песни внутри исполнителя, наличие ссылок.
Пустые названия, нечисловые годы и прочий разбор ввода остаются здесь.
"""

from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field


def _empty_to_none(value: object) -> object:
    """Пустой <select> и незаполненное поле приходят как пустая строка."""
    return None if value == "" else value


# Общие типы полей.
Name = Annotated[str, Field(min_length=1, max_length=120)]
Year = Annotated[int, Field(ge=1900, le=2100)]
Rating = Annotated[int, Field(ge=1, le=10)]
OptionalId = Annotated[int | None, BeforeValidator(_empty_to_none)]


class Form(BaseModel):
    """Общие правила: убрать краевые пробелы, отвергнуть лишние поля."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")


class GenreForm(Form):
    name: Name


class ArtistForm(Form):
    name: Name
    debut_year: Year


class AlbumForm(Form):
    artist_id: int
    title: Name
    release_year: Year


class SongForm(Form):
    artist_id: int
    genre_id: int
    album_id: OptionalId = None
    title: Name
    release_year: Year
    rating: Rating


class AwardForm(Form):
    song_id: int
    title: Name
    year: Year


class PlaylistForm(Form):
    name: Name


class PlaylistSongForm(Form):
    song_id: int
