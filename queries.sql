SELECT title, average_rating, ratings_count
FROM books
WHERE ratings_count > 1000
ORDER BY average_rating DESC
LIMIT 10;

SELECT p.name, COUNT(*) AS book_count
FROM books b
JOIN publishers p ON b.publisher_id = p.publisher_id
GROUP BY p.name
ORDER BY book_count DESC
LIMIT 15;

SELECT a.name, COUNT(*) AS book_count
FROM book_authors ba
JOIN authors a ON ba.author_id = a.author_id
GROUP BY a.name
HAVING COUNT(*) > 5
ORDER BY book_count DESC;

SELECT language_code, ROUND(AVG(average_rating), 2) AS avg_rating, COUNT(*) AS book_count
FROM books
GROUP BY language_code
ORDER BY book_count DESC;

SELECT book_id, title
FROM books
WHERE publisher_id IS NULL;

SELECT a.name, ROUND(AVG(b.average_rating), 2) AS avg_rating, COUNT(*) AS book_count
FROM book_authors ba
JOIN authors a ON ba.author_id = a.author_id
JOIN books b ON ba.book_id = b.book_id
GROUP BY a.name
HAVING COUNT(*) >= 3
ORDER BY avg_rating DESC
LIMIT 10;