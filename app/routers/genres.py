"""Справочник жанров: просмотр, добавление, изменение, удаление."""

from typing import Annotated

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app import db
from app.schemas import GenreForm
from app.templating import templates

router = APIRouter(prefix="/genres", tags=["genres"])

LIST_SQL = """
    SELECT g.genre_id, g.name, count(s.song_id) AS songs_count
      FROM genres g
      LEFT JOIN songs s ON s.genre_id = g.genre_id
     GROUP BY g.genre_id, g.name
     ORDER BY g.name
"""


@router.get("", response_class=HTMLResponse)
async def list_genres(request: Request):
    rows = await db.fetch(LIST_SQL)
    return templates.TemplateResponse(
        request=request, name="genres/list.html", context={"rows": rows}
    )


@router.get("/new", response_class=HTMLResponse)
async def new_genre(request: Request):
    return templates.TemplateResponse(
        request=request, name="genres/form.html", context={"genre": None}
    )


@router.post("")
async def create_genre(form: Annotated[GenreForm, Form()]):
    await db.execute("INSERT INTO genres (name) VALUES ($1)", form.name)
    return RedirectResponse(url="/genres", status_code=303)


@router.get("/{genre_id}/edit", response_class=HTMLResponse)
async def edit_genre(request: Request, genre_id: int):
    genre = await db.fetchrow(
        "SELECT genre_id, name FROM genres WHERE genre_id = $1", genre_id
    )
    return templates.TemplateResponse(
        request=request, name="genres/form.html", context={"genre": genre}
    )


@router.post("/{genre_id}")
async def update_genre(genre_id: int, form: Annotated[GenreForm, Form()]):
    await db.execute(
        "UPDATE genres SET name = $2 WHERE genre_id = $1", genre_id, form.name
    )
    return RedirectResponse(url="/genres", status_code=303)


@router.post("/{genre_id}/delete")
async def delete_genre(genre_id: int):
    # Правило ON DELETE RESTRICT защищает жанр: если на него ссылаются
    # песни, база данных отклонит удаление и пользователь увидит сообщение.
    await db.execute("DELETE FROM genres WHERE genre_id = $1", genre_id)
    return RedirectResponse(url="/genres", status_code=303)
