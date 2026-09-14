-- =====================================================================
-- Курсовая работа, вариант №10. Схема базы данных «Плейлист».
-- PostgreSQL 18.
--
-- Ограничения предметной области из листа задания:
--   1) награда может быть только у песни, причём наград может быть несколько;
--   2) у песни может не быть альбома;
--   3) названия песен у разных исполнителей могут совпадать.
-- =====================================================================

CREATE TABLE genres (
    genre_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name     text NOT NULL UNIQUE
);

CREATE TABLE artists (
    artist_id  integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name       text NOT NULL UNIQUE,
    debut_year smallint NOT NULL
);

CREATE TABLE albums (
    album_id     integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    artist_id    integer NOT NULL REFERENCES artists ON DELETE CASCADE,
    title        text NOT NULL,
    release_year smallint NOT NULL
);

CREATE TABLE songs (
    song_id      integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    artist_id    integer NOT NULL REFERENCES artists ON DELETE CASCADE,
    -- Ограничение №2: NULL означает, что песня не входит в альбом.
    album_id     integer REFERENCES albums ON DELETE SET NULL,
    genre_id     integer NOT NULL REFERENCES genres ON DELETE RESTRICT,
    title        text NOT NULL,
    release_year smallint NOT NULL,
    rating       smallint NOT NULL CHECK (rating BETWEEN 1 AND 10),
    -- Ограничение №3: название уникально только внутри одного исполнителя,
    -- у разных исполнителей песни могут называться одинаково.
    CONSTRAINT songs_title_uk UNIQUE (artist_id, title)
);

CREATE TABLE awards (
    award_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    -- Ограничение №1: награда всегда привязана к песне (song_id NOT NULL),
    -- а уникальности по song_id нет, поэтому наград у песни может быть много.
    song_id  integer NOT NULL REFERENCES songs ON DELETE CASCADE,
    title    text NOT NULL,
    year     smallint NOT NULL
);

CREATE TABLE playlists (
    playlist_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name        text NOT NULL UNIQUE,
    created_at  date NOT NULL DEFAULT current_date
);

-- Связь «многие-ко-многим» между плейлистами и песнями.
CREATE TABLE playlist_songs (
    playlist_id integer NOT NULL REFERENCES playlists ON DELETE CASCADE,
    song_id     integer NOT NULL REFERENCES songs ON DELETE CASCADE,
    position    integer NOT NULL,
    PRIMARY KEY (playlist_id, song_id)
);

-- Индексы по внешним ключам: PostgreSQL создаёт их только
-- для PRIMARY KEY и UNIQUE, остальные нужно объявить самому.
CREATE INDEX songs_artist_idx        ON songs (artist_id);
CREATE INDEX songs_album_idx         ON songs (album_id);
CREATE INDEX songs_genre_idx         ON songs (genre_id);
CREATE INDEX albums_artist_idx       ON albums (artist_id);
CREATE INDEX awards_song_idx         ON awards (song_id);
CREATE INDEX playlist_songs_song_idx ON playlist_songs (song_id);
