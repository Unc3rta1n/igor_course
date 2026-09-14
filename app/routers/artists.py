"""Исполнители: просмотр, добавление, изменение, удаление."""

from typing import Annotated

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app import db
from app.schemas import ArtistForm
from app.templating import templates

router = APIRouter(prefix="/artists", tags=["artists"])

LIST_SQL = """
    SELECT ar.artist_id,
           ar.name,
           ar.debut_year,
           count(DISTINCT s.song_id)   AS songs_count,
           count(DISTINCT al.album_id) AS albums_count
      FROM artists ar
      LEFT JOIN songs  s  ON s.artist_id  = ar.artist_id
      LEFT JOIN albums al ON al.artist_id = ar.artist_id
     GROUP BY ar.artist_id, ar.name, ar.debut_year
     ORDER BY ar.name
"""


@router.get("", response_class=HTMLResponse)
async def list_artists(request: Request):
    rows = await db.fetch(LIST_SQL)
    return templates.TemplateResponse(
        request=request, name="artists/list.html", context={"rows": rows}
    )


@router.get("/new", response_class=HTMLResponse)
async def new_artist(request: Request):
    return templates.TemplateResponse(
        request=request, name="artists/form.html", context={"artist": None}
    )


@router.post("")
async def create_artist(form: Annotated[ArtistForm, Form()]):
    await db.execute(
        "INSERT INTO artists (name, debut_year) VALUES ($1, $2)",
        form.name,
        form.debut_year,
    )
    return RedirectResponse(url="/artists", status_code=303)


@router.get("/{artist_id}/edit", response_class=HTMLResponse)
async def edit_artist(request: Request, artist_id: int):
    artist = await db.fetchrow(
        "SELECT artist_id, name, debut_year FROM artists WHERE artist_id = $1",
        artist_id,
    )
    return templates.TemplateResponse(
        request=request, name="artists/form.html", context={"artist": artist}
    )


@router.post("/{artist_id}")
async def update_artist(artist_id: int, form: Annotated[ArtistForm, Form()]):
    await db.execute(
        "UPDATE artists SET name = $2, debut_year = $3 WHERE artist_id = $1",
        artist_id,
        form.name,
        form.debut_year,
    )
    return RedirectResponse(url="/artists", status_code=303)


@router.post("/{artist_id}/delete")
async def delete_artist(artist_id: int):
    # ON DELETE CASCADE: СУБД удалит вместе с исполнителем его альбомы,
    # песни и награды этих песен.
    await db.execute("DELETE FROM artists WHERE artist_id = $1", artist_id)
    return RedirectResponse(url="/artists", status_code=303)
