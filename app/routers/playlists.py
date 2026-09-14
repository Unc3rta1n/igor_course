"""Плейлисты и их состав (связь «многие-ко-многим» с песнями)."""

from typing import Annotated

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app import db
from app.schemas import PlaylistForm, PlaylistSongForm
from app.templating import templates

router = APIRouter(prefix="/playlists", tags=["playlists"])

LIST_SQL = """
    SELECT p.playlist_id, p.name, p.created_at,
           count(ps.song_id)       AS songs_count,
           round(avg(s.rating), 2) AS avg_rating
      FROM playlists p
      LEFT JOIN playlist_songs ps ON ps.playlist_id = p.playlist_id
      LEFT JOIN songs s ON s.song_id = ps.song_id
     GROUP BY p.playlist_id, p.name, p.created_at
     ORDER BY p.name
"""

CONTENT_SQL = """
    SELECT ps.position, s.song_id, s.title AS song_title,
           ar.name AS artist_name, g.name AS genre_name, s.rating
      FROM playlist_songs ps
      JOIN songs   s  ON s.song_id    = ps.song_id
      JOIN artists ar ON ar.artist_id = s.artist_id
      JOIN genres  g  ON g.genre_id   = s.genre_id
     WHERE ps.playlist_id = $1
     ORDER BY ps.position
"""

FREE_SONGS_SQL = """
    SELECT s.song_id, s.title, ar.name AS artist_name
      FROM songs s
      JOIN artists ar ON ar.artist_id = s.artist_id
     WHERE NOT EXISTS (SELECT 1 FROM playlist_songs ps
                        WHERE ps.playlist_id = $1 AND ps.song_id = s.song_id)
     ORDER BY ar.name, s.title
"""


@router.get("", response_class=HTMLResponse)
async def list_playlists(request: Request):
    rows = await db.fetch(LIST_SQL)
    return templates.TemplateResponse(
        request=request,
        name="playlists/list.html",
        context={"rows": rows},
    )


@router.get("/new", response_class=HTMLResponse)
async def new_playlist(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="playlists/form.html",
        context={"playlist": None},
    )


@router.post("")
async def create_playlist(form: Annotated[PlaylistForm, Form()]):
    await db.execute("INSERT INTO playlists (name) VALUES ($1)", form.name)
    return RedirectResponse(url="/playlists", status_code=303)


@router.get("/{playlist_id}", response_class=HTMLResponse)
async def show_playlist(request: Request, playlist_id: int):
    """Состав плейлиста и форма добавления новой песни."""
    playlist = await db.fetchrow(
        "SELECT playlist_id, name, created_at FROM playlists WHERE playlist_id = $1",
        playlist_id,
    )
    return templates.TemplateResponse(
        request=request,
        name="playlists/detail.html",
        context={
            "playlist": playlist,
            "content": await db.fetch(CONTENT_SQL, playlist_id),
            "free_songs": await db.fetch(FREE_SONGS_SQL, playlist_id),
        },
    )


@router.get("/{playlist_id}/edit", response_class=HTMLResponse)
async def edit_playlist(request: Request, playlist_id: int):
    playlist = await db.fetchrow(
        "SELECT playlist_id, name FROM playlists WHERE playlist_id = $1",
        playlist_id,
    )
    return templates.TemplateResponse(
        request=request,
        name="playlists/form.html",
        context={"playlist": playlist},
    )


@router.post("/{playlist_id}")
async def update_playlist(playlist_id: int, form: Annotated[PlaylistForm, Form()]):
    await db.execute(
        "UPDATE playlists SET name = $2 WHERE playlist_id = $1",
        playlist_id,
        form.name,
    )
    return RedirectResponse(url="/playlists", status_code=303)


@router.post("/{playlist_id}/delete")
async def delete_playlist(playlist_id: int):
    await db.execute("DELETE FROM playlists WHERE playlist_id = $1", playlist_id)
    return RedirectResponse(url="/playlists", status_code=303)


@router.post("/{playlist_id}/songs")
async def add_song(playlist_id: int, form: Annotated[PlaylistSongForm, Form()]):
    """Добавить песню в конец плейлиста."""
    last = await db.fetchval(
        "SELECT max(position) FROM playlist_songs WHERE playlist_id = $1",
        playlist_id,
    )
    await db.execute(
        "INSERT INTO playlist_songs (playlist_id, song_id, position) VALUES ($1, $2, $3)",
        playlist_id,
        form.song_id,
        (last or 0) + 1,
    )
    return RedirectResponse(url=f"/playlists/{playlist_id}", status_code=303)


@router.post("/{playlist_id}/songs/{song_id}/delete")
async def remove_song(playlist_id: int, song_id: int):
    await db.execute(
        "DELETE FROM playlist_songs WHERE playlist_id = $1 AND song_id = $2",
        playlist_id,
        song_id,
    )
    return RedirectResponse(url=f"/playlists/{playlist_id}", status_code=303)
