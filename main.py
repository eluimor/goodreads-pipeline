import pandas as pd
import os
from dotenv import load_dotenv
import psycopg2
import re

df = pd.read_csv('data/books.csv', on_bad_lines='skip')

print(df.shape)
print(df.columns.tolist())
print(df.head())

df.columns = df.columns.str.strip()

# NOTE: 2 out of 11123 rows contain invalid dates in the source data
# (e.g., 11/31/2000 — November has no 31st day). This is not a parsing
# error but an error in the dataset itself. Decision: leave as NULL (NaT)
# rather than guessing the intended date — 2 rows out of 11,000+ don't
# meaningfully affect the overall analysis.

df['publication_date'] = pd.to_datetime(
    df['publication_date'], format='%m/%d/%Y', errors='coerce'
)

print(df.columns.tolist())
print(df['publication_date'].head())
print(df['publication_date'].isnull().sum())

print(df[df['publication_date'].isnull()][['bookID', 'title', 'publication_date']])

# NOTE: Author and publisher names contain inconsistent internal whitespace
# ("Nick  Webb" vs "Nick Webb"). Collapsing repeated whitespace before
# deduplication merges 31 duplicate author records that would otherwise
# receive separate IDs and split their books across two entities.

# --- Publishers: unique list ---
publishers = (
    df['publisher']
    .dropna()
    .str.replace(r'\s+', ' ', regex=True)
    .str.strip()
    .drop_duplicates()
    .sort_values()
    .reset_index(drop=True)
)

import re

def clean_name(x):
    if pd.isna(x):
        return None
    return re.sub(r'\s+', ' ', x).strip()

df['publisher_clean'] = df['publisher'].apply(clean_name)

print('publishers:', len(publishers))
print(publishers.head())

# --- Authors: split multi-author values on '/' ---
authors_exploded = (
    df[['bookID', 'authors']]
    .assign(author=df['authors'].str.split('/'))
    .explode('author')

)

authors_exploded['author'] = (
    authors_exploded['author']
    .str.replace(r'\s+', ' ', regex=True)
    .str.strip()
)

authors_exploded['author'] = authors_exploded['author'].str.strip()

authors = (
    authors_exploded['author']
    .dropna()
    .drop_duplicates()
    .sort_values()
    .reset_index(drop=True)
)

print('authors:', len(authors))
print('book-author pairs:', len(authors_exploded))

load_dotenv()

conn = psycopg2.connect(
    dbname=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    host=os.getenv('DB_HOST'),
    port=os.getenv('DB_PORT'),
)

print('Connected:', conn.get_dsn_parameters()['dbname'])
cur = conn.cursor()

# --- Publishers ---
for name in publishers:
    cur.execute(
        "INSERT INTO publishers (name) VALUES (%s) ON CONFLICT (name) DO NOTHING",
        (name,)
    )
conn.commit()

cur.execute("SELECT publisher_id, name FROM publishers")
publisher_map = {name: pid for pid, name in cur.fetchall()}
print('publishers in DB:', len(publisher_map))

# --- Authors ---
for name in authors:
    cur.execute(
        "INSERT INTO authors (name) VALUES (%s) ON CONFLICT (name) DO NOTHING",
        (name,)
    )
conn.commit()

cur.execute("SELECT author_id, name FROM authors")
author_map = {name: aid for aid, name in cur.fetchall()}
print('authors in DB:', len(author_map))

for _, row in df.iterrows():
    pub_id = publisher_map.get(row['publisher_clean'])
    pub_date = row['publication_date'].date() if pd.notna(row['publication_date']) else None

    cur.execute(
        """
        INSERT INTO books (
            book_id, title, isbn, isbn13, language_code,
            num_pages, average_rating, ratings_count,
            text_reviews_count, publication_date, publisher_id
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (book_id) DO NOTHING
        """,
        (
            int(row['bookID']), row['title'], row['isbn'], str(row['isbn13']),
            row['language_code'],
            int(row['num_pages']) if pd.notna(row['num_pages']) else None,
            float(row['average_rating']) if pd.notna(row['average_rating']) else None,
            int(row['ratings_count']) if pd.notna(row['ratings_count']) else None,
            int(row['text_reviews_count']) if pd.notna(row['text_reviews_count']) else None,
            pub_date, pub_id
        )
    )

conn.commit()
cur.execute("SELECT COUNT(*) FROM books")
print('books in DB:', cur.fetchone()[0])

for _, pair in authors_exploded.iterrows():
    author_id = author_map.get(pair['author'])
    cur.execute(
        "INSERT INTO book_authors (book_id, author_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
        (int(pair['bookID']), author_id)
    )

conn.commit()
cur.execute("SELECT COUNT(*) FROM book_authors")
print('book_authors in DB:', cur.fetchone()[0])

conn.close()

# NOTE: 32 rows contain the same author listed twice within a single book's
# 'authors' field (e.g. "Xavier de C./Xavier de C./Joseph Rowe") — likely
# a data entry error in the source dataset. The book_authors table's
# composite PRIMARY KEY (book_id, author_id) enforces uniqueness and
# silently rejects these duplicates via ON CONFLICT DO NOTHING, so the
# final table correctly contains 19205 distinct book-author relationships
# instead of 19237.