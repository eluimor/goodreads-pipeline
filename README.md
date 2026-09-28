# Goodreads Books — SQL + Python ETL Pipeline

A small end-to-end data pipeline: cleans a public Goodreads books dataset in Python,
loads it into a normalized PostgreSQL database, and runs analytical SQL queries.

## Dataset
Source: Source: [Goodreads-books by JealousLeopard on Kaggle](https://www.kaggle.com/datasets/jealousleopard/goodreadsbooks).
File: `books.csv` — 11,127 records before cleaning; 11,123 after skipping four malformed CSV rows.

## Schema
Normalized into 4 tables to avoid data duplication and support relational queries:
- `books` — one row per book
- `authors` — unique authors
- `publishers` — unique publishers
- `book_authors` — many-to-many link (a book can have multiple authors)

## Data quality decisions
Real-world data required several cleaning decisions, documented here rather than
silently handled:

- **4 malformed CSV rows** (unescaped commas in author/publisher names) were skipped
  during loading (`on_bad_lines='skip'`).
- **2 invalid dates** in the source data (e.g. `11/31/2000` — no such date) were kept
  as `NULL` rather than guessing the intended value.
- **Inconsistent internal whitespace** in author/publisher names (e.g. `"Nick  Webb"`
  vs `"Nick Webb"`) was collapsed before deduplication, merging 30+ author records
  and 9 publisher records that would otherwise have been treated as different entities.
- **32 books** listed the same author twice in the source `authors` field; the
  `book_authors` composite primary key silently and correctly rejects the duplicate.

## Tech stack
Python (pandas, psycopg2), PostgreSQL, SQL

## How to run
1. Create a PostgreSQL database and run `schema.sql`
2. Copy `.env.example` to `.env` and fill in your DB credentials
3. Place `books.csv` in `data/`
4. `pip install -r requirements.txt`
5. `python main.py`

## Example analysis
See `queries.sql` for analytical queries, including:
- Top-rated books (1000+ ratings)
- Books per publisher
- Authors with 5+ books
- Average rating by language
- Highest-rated authors (3+ books)
