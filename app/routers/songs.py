"""Песни: просмотр с фильтрами, добавление, изменение, удаление."""

from typing import Annotated

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app import db
from app.schemas import OptionalId, SongForm
from app.templating import templates

router = APIRouter(prefix="/songs", tags=["songs"])

# Фильтры необязательные: NULL-параметр отключает соответствующее условие.
LIST_SQL = """
    SELECT s.song_id,
           s.title  AS song_title,
           ar.name  AS artist_name,
           al.title AS album_title,
           g.name   AS genre_name,
           s.release_year,
           s.rating,
           (SELECT count(*) FROM awards aw WHERE aw.song_id = s.song_id) AS awards_count
      FROM songs s
      JOIN artists ar ON ar.artist_id = s.artist_id
      JOIN genres  g  ON g.genre_id   = s.genre_id
      LEFT JOIN albums al ON al.album_id = s.album_id
     WHERE ($1::int IS NULL OR s.artist_id    = $1)
       AND ($2::int IS NULL OR s.genre_id     = $2)
       AND ($3::int IS NULL OR s.release_year = $3)
     ORDER BY ar.name, s.title
"""

ARTISTS_SQL = "SELECT artist_id, name FROM artists ORDER BY name"
GENRES_SQL = "SELECT genre_id, name FROM genres ORDER BY name"
ALBUMS_SQL = """
    SELECT al.album_id, al.title, ar.name AS artist_name
      FROM albums al
      JOIN artists ar ON ar.artist_id = al.artist_id
     ORDER BY ar.name, al.title
"""


async def _form_context(song=None) -> dict:
    """Справочники для выпадающих списков формы."""
    return {
        "song": song,
        "artists": await db.fetch(ARTISTS_SQL),
        "genres": await db.fetch(GENRES_SQL),
        "albums": await db.fetch(ALBUMS_SQL),
    }


@router.get("", response_class=HTMLResponse)
async def list_songs(
    request: Request,
    artist_id: OptionalId = None,
    genre_id: OptionalId = None,
    release_year: OptionalId = None,
):
    rows = await db.fetch(LIST_SQL, artist_id, genre_id, release_year)
    return templates.TemplateResponse(
        request=request,
        name="songs/list.html",
        context={
            "rows": rows,
            "filters": {
                "artist_id": artist_id,
                "genre_id": genre_id,
                "release_year": release_year,
            },
            "artists": await db.fetch(ARTISTS_SQL),
            "genres": await db.fetch(GENRES_SQL),
        },
    )


@router.get("/new", response_class=HTMLResponse)
async def new_song(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="songs/form.html",
        context=await _form_context(),
    )


@router.post("")
async def create_song(form: Annotated[SongForm, Form()]):
    await db.execute(
        """
        INSERT INTO songs (artist_id, album_id, genre_id, title, release_year, rating)
        VALUES ($1, $2, $3, $4, $5, $6)
        """,
        form.artist_id,
        form.album_id,
        form.genre_id,
        form.title,
        form.release_year,
        form.rating,
    )
    return RedirectResponse(url="/songs", status_code=303)


@router.get("/{song_id}/edit", response_class=HTMLResponse)
async def edit_song(request: Request, song_id: int):
    song = await db.fetchrow(
        """
        SELECT song_id, artist_id, album_id, genre_id, title, release_year, rating
          FROM songs WHERE song_id = $1
        """,
        song_id,
    )
    return templates.TemplateResponse(
        request=request,
        name="songs/form.html",
        context=await _form_context(song),
    )


@router.post("/{song_id}")
async def update_song(song_id: int, form: Annotated[SongForm, Form()]):
    await db.execute(
        """
        UPDATE songs
           SET artist_id = $2, album_id = $3, genre_id = $4,
               title = $5, release_year = $6, rating = $7
         WHERE song_id = $1
        """,
        song_id,
        form.artist_id,
        form.album_id,
        form.genre_id,
        form.title,
        form.release_year,
        form.rating,
    )
    return RedirectResponse(url="/songs", status_code=303)


@router.post("/{song_id}/delete")
async def delete_song(song_id: int):
    # ON DELETE CASCADE: СУБД удалит вместе с песней её награды
    # и записи о ней в плейлистах.
    await db.execute("DELETE FROM songs WHERE song_id = $1", song_id)
    return RedirectResponse(url="/songs", status_code=303)
