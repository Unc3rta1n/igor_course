"""Альбомы: просмотр, добавление, изменение, удаление."""

from typing import Annotated

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app import db
from app.schemas import AlbumForm
from app.templating import templates

router = APIRouter(prefix="/albums", tags=["albums"])

LIST_SQL = """
    SELECT al.album_id,
           al.title,
           al.release_year,
           ar.name                 AS artist_name,
           count(s.song_id)        AS songs_count,
           round(avg(s.rating), 2) AS avg_rating
      FROM albums al
      JOIN artists ar ON ar.artist_id = al.artist_id
      LEFT JOIN songs s ON s.album_id = al.album_id
     GROUP BY al.album_id, al.title, al.release_year, ar.name
     ORDER BY ar.name, al.release_year
"""

ARTISTS_SQL = "SELECT artist_id, name FROM artists ORDER BY name"


@router.get("", response_class=HTMLResponse)
async def list_albums(request: Request):
    rows = await db.fetch(LIST_SQL)
    return templates.TemplateResponse(
        request=request,
        name="albums/list.html",
        context={"rows": rows},
    )


@router.get("/new", response_class=HTMLResponse)
async def new_album(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="albums/form.html",
        context={"album": None, "artists": await db.fetch(ARTISTS_SQL)},
    )


@router.post("")
async def create_album(form: Annotated[AlbumForm, Form()]):
    await db.execute(
        "INSERT INTO albums (artist_id, title, release_year) VALUES ($1, $2, $3)",
        form.artist_id,
        form.title,
        form.release_year,
    )
    return RedirectResponse(url="/albums", status_code=303)


@router.get("/{album_id}/edit", response_class=HTMLResponse)
async def edit_album(request: Request, album_id: int):
    album = await db.fetchrow(
        "SELECT album_id, artist_id, title, release_year FROM albums WHERE album_id = $1",
        album_id,
    )
    return templates.TemplateResponse(
        request=request,
        name="albums/form.html",
        context={"album": album, "artists": await db.fetch(ARTISTS_SQL)},
    )


@router.post("/{album_id}")
async def update_album(album_id: int, form: Annotated[AlbumForm, Form()]):
    await db.execute(
        """
        UPDATE albums
           SET artist_id = $2, title = $3, release_year = $4
         WHERE album_id = $1
        """,
        album_id,
        form.artist_id,
        form.title,
        form.release_year,
    )
    return RedirectResponse(url="/albums", status_code=303)


@router.post("/{album_id}/delete")
async def delete_album(album_id: int):
    # ON DELETE SET NULL: песни удалённого альбома остаются в базе
    # и теряют привязку к альбому.
    await db.execute("DELETE FROM albums WHERE album_id = $1", album_id)
    return RedirectResponse(url="/albums", status_code=303)
