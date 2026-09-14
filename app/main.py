"""Курсовая работа №10. Приложение для работы с базой данных «Плейлист».

FastAPI + Jinja2 + asyncpg, запросы к БД написаны на чистом SQL.
"""

from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app import db
from app.errors import form_error_message, human_message
from app.routers import albums, artists, awards, genres, playlists, reports, songs
from app.templating import TEMPLATES_DIR, templates


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    yield
    await db.disconnect()


app = FastAPI(title="База данных «Плейлист»", lifespan=lifespan)

app.mount(
    "/static",
    StaticFiles(directory=str(TEMPLATES_DIR.parent / "static")),
    name="static",
)

app.include_router(songs.router)
app.include_router(artists.router)
app.include_router(albums.router)
app.include_router(genres.router)
app.include_router(awards.router)
app.include_router(playlists.router)
app.include_router(reports.router)


def _error_page(request: Request, message: str, status_code: int) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="error.html",
        context={"message": message, "back_url": request.headers.get("referer", "/")},
        status_code=status_code,
    )


@app.exception_handler(asyncpg.PostgresError)
async def postgres_error_handler(request: Request, exc: asyncpg.PostgresError):
    """Нарушение ограничений целостности показываем пользователю, а не как 500."""
    return _error_page(request, human_message(exc), status_code=400)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Ошибку схемы Pydantic показываем как понятный текст о конкретном поле."""
    return _error_page(request, form_error_message(exc), status_code=400)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Главная страница: сводка по содержимому базы данных."""
    stats = await db.fetchrow(
        """
        SELECT (SELECT count(*) FROM songs)     AS songs,
               (SELECT count(*) FROM artists)   AS artists,
               (SELECT count(*) FROM albums)    AS albums,
               (SELECT count(*) FROM genres)    AS genres,
               (SELECT count(*) FROM awards)    AS awards,
               (SELECT count(*) FROM playlists) AS playlists
        """
    )
    top_rated = await db.fetch(
        """
        SELECT s.title AS song_title,
               ar.name AS artist_name,
               g.name  AS genre_name,
               s.rating
          FROM songs s
          JOIN artists ar ON ar.artist_id = s.artist_id
          JOIN genres  g  ON g.genre_id   = s.genre_id
         ORDER BY s.rating DESC, s.title
         LIMIT 5
        """
    )
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"stats": stats, "top_rated": top_rated},
    )
