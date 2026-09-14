# Курсовая работа №10. База данных «Плейлист»

PostgreSQL 18 + FastAPI + Jinja2 + asyncpg (чистый SQL, без ORM).

## Запуск

```bash
cp .env.example .env      # при необходимости поменяйте пароль и порт
docker compose up -d      # контейнер сам создаёт схему и контрольный пример
python -m venv .venv    # создать виртуальное окружение
.\.venv\Scripts\activate # активировать виртуальное окружение
pip install -r requirements.txt # установить зависимости в виртуальное окружение
uvicorn app.main:app --reload # запустить приложение
```

Приложение отвечает по адресу <http://127.0.0.1:8000>.

Пересоздать базу с нуля:

```bash
docker compose down -v && docker compose up -d
```

## Что где лежит

| Путь | Содержание |
|---|---|
| `sql/01_schema.sql` | таблицы, ограничения, индексы |
| `sql/02_seed.sql` | контрольный пример: 12 исполнителей, 35 песен, 32 награды |
| `app/routers/` | формы ввода и редактирования, четыре отчёта, тексты SQL-запросов |
| `app/templates/` | HTML-шаблоны |
| `docs/zapiska.docx` | пояснительная записка |
| `docs/er-diagram.png` | ER-диаграмма картинкой |

## Отчёты

1. Топ-10 исполнителей по количеству наград: `/reports/top-artists`
2. Количество песен по жанрам за заданный год: `/reports/genre-year`
3. Альбом с наивысшим средним рейтингом в выбранных жанрах: `/reports/best-album`
4. Исполнители, выпустившие альбом за период: `/reports/artists-period`

## Прямой доступ к базе

```bash
docker compose exec db psql -U playlist -d playlist
```
