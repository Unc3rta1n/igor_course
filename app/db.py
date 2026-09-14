"""Доступ к PostgreSQL: пул соединений asyncpg и тонкие обёртки над ним.

ORM не используется: все запросы написаны на чистом SQL, как того требует
задание курсовой работы.
"""

import os
from typing import Any

import asyncpg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://playlist:playlist@localhost:5433/playlist"
)

_pool: asyncpg.Pool | None = None


async def connect() -> None:
    """Создать пул соединений. Приложение вызывает эту функцию при старте."""
    global _pool
    _pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=10)


async def disconnect() -> None:
    """Закрыть пул соединений. Приложение вызывает эту функцию при остановке."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Пул соединений не инициализирован")
    return _pool


async def fetch(sql: str, *args: Any) -> list[asyncpg.Record]:
    """Выполнить запрос и вернуть все строки."""
    return await pool().fetch(sql, *args)


async def fetchrow(sql: str, *args: Any) -> asyncpg.Record | None:
    """Выполнить запрос и вернуть первую строку или None."""
    return await pool().fetchrow(sql, *args)


async def fetchval(sql: str, *args: Any) -> Any:
    """Выполнить запрос и вернуть одно значение."""
    return await pool().fetchval(sql, *args)


async def execute(sql: str, *args: Any) -> str:
    """Выполнить команду, не возвращающую строк (INSERT/UPDATE/DELETE)."""
    return await pool().execute(sql, *args)
