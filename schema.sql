-- 1. Authors
CREATE TABLE authors (
    author_id   SERIAL PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE
);

-- 2. Publishers
CREATE TABLE publishers (
    publisher_id   SERIAL PRIMARY KEY,
    name           TEXT NOT NULL UNIQUE
);

-- 3. Books (ссылается на publishers)
CREATE TABLE books (
    book_id             INTEGER PRIMARY KEY,
    title               TEXT NOT NULL,
    isbn                TEXT,
    isbn13              TEXT,
    language_code       TEXT,
    num_pages           INTEGER,
    average_rating      NUMERIC(3,2),
    ratings_count       INTEGER,
    text_reviews_count  INTEGER,
    publication_date    DATE,
    publisher_id        INTEGER REFERENCES publishers(publisher_id)
);

-- 4. Book_authors (ссылается на books и authors)
CREATE TABLE book_authors (
    book_id     INTEGER REFERENCES books(book_id),
    author_id   INTEGER REFERENCES authors(author_id),
    PRIMARY KEY (book_id, author_id)
);