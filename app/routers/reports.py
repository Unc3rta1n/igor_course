"""Отчёты (запросы) по заданию курсовой работы.

Все четыре запроса написаны на чистом SQL. Драйвер подставляет введённые
пользователем значения через параметры $1, $2, поэтому SQL-инъекция невозможна.
"""

from datetime import date

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse

from app import db
from app.templating import templates

router = APIRouter(prefix="/reports", tags=["reports"])

# --- Отчёт №1: топ-10 исполнителей по количеству наград ---------------
TOP_ARTISTS_SQL = """
    SELECT ar.artist_id,
           ar.name        AS artist_name,
           count(*)       AS awards_count,
           count(DISTINCT s.song_id) AS awarded_songs
      FROM awards aw
      JOIN songs   s  ON s.song_id    = aw.song_id
      JOIN artists ar ON ar.artist_id = s.artist_id
     GROUP BY ar.artist_id, ar.name
     ORDER BY awards_count DESC, ar.name
     LIMIT 10
"""

# --- Отчёт №2: количество песен каждого жанра за указанный год --------
# LEFT JOIN с условием по году внутри ON: жанры без песен тоже попадают
# в отчёт со значением 0.
GENRE_YEAR_SQL = """
    SELECT g.genre_id,
           g.name            AS genre_name,
           count(s.song_id)  AS songs_count
      FROM genres g
      LEFT JOIN songs s
             ON s.genre_id = g.genre_id
            AND s.release_year = $1
     GROUP BY g.genre_id, g.name
     ORDER BY songs_count DESC, g.name
"""

# --- Отчёт №3: альбом с наивысшим средним рейтингом песен --------------
# Пользователь может выбрать сразу несколько жанров: приложение передаёт
# их список одним параметром-массивом. WITH TIES выводит все альбомы, если
# у нескольких из них средний балл одинаково максимальный.
BEST_ALBUM_SQL = """
    SELECT al.album_id,
           al.title                AS album_title,
           ar.name                 AS artist_name,
           al.release_year,
           round(avg(s.rating), 2) AS avg_rating,
           count(*)                AS songs_count
      FROM songs s
      JOIN albums  al ON al.album_id  = s.album_id
      JOIN artists ar ON ar.artist_id = al.artist_id
     WHERE s.genre_id = ANY($1::int[])
     GROUP BY al.album_id, al.title, ar.name, al.release_year
     ORDER BY avg_rating DESC
     FETCH FIRST 1 ROWS WITH TIES
"""

# --- Отчёт №4: исполнители, выпустившие альбом за период --------------
# Внутреннее соединение оставляет только исполнителей, у которых за период
# есть хотя бы один альбом; группировка убирает дубликаты и попутно даёт
# количество выпущенных за период альбомов.
ARTISTS_PERIOD_SQL = """
    SELECT ar.artist_id,
           ar.name        AS artist_name,
           ar.debut_year,
           count(*)       AS albums_count
      FROM artists ar
      JOIN albums al ON al.artist_id = ar.artist_id
     WHERE al.release_year BETWEEN $1 AND $2
     GROUP BY ar.artist_id, ar.name, ar.debut_year
     ORDER BY ar.name
"""


@router.get("", response_class=HTMLResponse)
async def reports_index(request: Request):
    return templates.TemplateResponse(request=request, name="reports/index.html")


@router.get("/top-artists", response_class=HTMLResponse)
async def top_artists(request: Request):
    """Отчёт №1. Топ-10 исполнителей, заработавших больше всего наград."""
    rows = await db.fetch(TOP_ARTISTS_SQL)
    return templates.TemplateResponse(
        request=request,
        name="reports/top_artists.html",
        context={"rows": rows, "sql": TOP_ARTISTS_SQL},
    )


@router.get("/genre-year", response_class=HTMLResponse)
async def genre_year(request: Request, year: int | None = Query(None)):
    """Отчёт №2. Количество песен по жанрам за заданный пользователем год."""
    rows = await db.fetch(GENRE_YEAR_SQL, year) if year is not None else []
    return templates.TemplateResponse(
        request=request,
        name="reports/genre_year.html",
        context={
            "rows": rows,
            "year": year,
            "current_year": date.today().year,
            "sql": GENRE_YEAR_SQL,
        },
    )


@router.get("/best-album", response_class=HTMLResponse)
async def best_album(request: Request, genre_ids: list[int] = Query(default=[])):
    """Отчёт №3. Альбом с самыми популярными песнями в выбранных жанрах."""
    rows = await db.fetch(BEST_ALBUM_SQL, genre_ids) if genre_ids else []
    genres = await db.fetch("SELECT genre_id, name FROM genres ORDER BY name")
    return templates.TemplateResponse(
        request=request,
        name="reports/best_album.html",
        context={
            "rows": rows,
            "genres": genres,
            "selected": set(genre_ids),
            "sql": BEST_ALBUM_SQL,
        },
    )


@router.get("/artists-period", response_class=HTMLResponse)
async def artists_period(
    request: Request,
    year_from: int | None = Query(None),
    year_to: int | None = Query(None),
):
    """Отчёт №4. Исполнители, выпустившие хотя бы один альбом за период."""
    rows = []
    if year_from is not None and year_to is not None:
        rows = await db.fetch(ARTISTS_PERIOD_SQL, year_from, year_to)
    return templates.TemplateResponse(
        request=request,
        name="reports/artists_period.html",
        context={
            "rows": rows,
            "year_from": year_from,
            "year_to": year_to,
            "current_year": date.today().year,
            "sql": ARTISTS_PERIOD_SQL,
        },
    )
