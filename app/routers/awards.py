"""Награды песен: просмотр, добавление, изменение, удаление.

По ограничению предметной области награда принадлежит только песне,
поэтому поле «песня» обязательно, а одна песня может иметь несколько наград.
"""

from typing import Annotated

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app import db
from app.schemas import AwardForm
from app.templating import templates

router = APIRouter(prefix="/awards", tags=["awards"])

LIST_SQL = """
    SELECT aw.award_id, aw.title, aw.year,
           s.title  AS song_title,
           ar.name  AS artist_name
      FROM awards aw
      JOIN songs   s  ON s.song_id    = aw.song_id
      JOIN artists ar ON ar.artist_id = s.artist_id
     ORDER BY aw.year DESC, ar.name, aw.title
"""

SONGS_SQL = """
    SELECT s.song_id, s.title, ar.name AS artist_name
      FROM songs s
      JOIN artists ar ON ar.artist_id = s.artist_id
     ORDER BY ar.name, s.title
"""


@router.get("", response_class=HTMLResponse)
async def list_awards(request: Request):
    rows = await db.fetch(LIST_SQL)
    return templates.TemplateResponse(
        request=request,
        name="awards/list.html",
        context={"rows": rows},
    )


@router.get("/new", response_class=HTMLResponse)
async def new_award(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="awards/form.html",
        context={"award": None, "songs": await db.fetch(SONGS_SQL)},
    )


@router.post("")
async def create_award(form: Annotated[AwardForm, Form()]):
    await db.execute(
        "INSERT INTO awards (song_id, title, year) VALUES ($1, $2, $3)",
        form.song_id,
        form.title,
        form.year,
    )
    return RedirectResponse(url="/awards", status_code=303)


@router.get("/{award_id}/edit", response_class=HTMLResponse)
async def edit_award(request: Request, award_id: int):
    award = await db.fetchrow(
        "SELECT award_id, song_id, title, year FROM awards WHERE award_id = $1",
        award_id,
    )
    return templates.TemplateResponse(
        request=request,
        name="awards/form.html",
        context={"award": award, "songs": await db.fetch(SONGS_SQL)},
    )


@router.post("/{award_id}")
async def update_award(award_id: int, form: Annotated[AwardForm, Form()]):
    await db.execute(
        "UPDATE awards SET song_id = $2, title = $3, year = $4 WHERE award_id = $1",
        award_id,
        form.song_id,
        form.title,
        form.year,
    )
    return RedirectResponse(url="/awards", status_code=303)


@router.post("/{award_id}/delete")
async def delete_award(award_id: int):
    await db.execute("DELETE FROM awards WHERE award_id = $1", award_id)
    return RedirectResponse(url="/awards", status_code=303)
