-- ============================================================
-- All 20 Required SQL Queries — Tennis Analytics
-- ============================================================

-- Q1: List all competitions along with their category name.
SELECT c.competition_id, c.competition_name, c.parent_id, c.type, c.gender,
       cat.category_name
FROM Competitions c
JOIN Categories cat ON c.category_id = cat.category_id
ORDER BY cat.category_name, c.competition_name;

-- Q2: Count the number of competitions in each category.
SELECT cat.category_name, COUNT(c.competition_id) AS competition_count
FROM Categories cat
LEFT JOIN Competitions c ON c.category_id = cat.category_id
GROUP BY cat.category_id, cat.category_name
ORDER BY competition_count DESC;

-- Q3: Find all competitions of type 'doubles'.
SELECT competition_id, competition_name, parent_id, gender, category_id
FROM Competitions
WHERE type = 'doubles'
ORDER BY category_id, competition_name;

-- Q4: Get competitions that belong to a specific category (default 'ITF Men').
SELECT competition_id, competition_name, parent_id, type, gender
FROM Competitions c
JOIN Categories cat ON c.category_id = cat.category_id
WHERE cat.category_name = :category_name
ORDER BY c.competition_name;

-- Q5: Identify parent competitions and their sub-competitions (self-join).
SELECT p.competition_name AS parent_competition,
       s.competition_name AS sub_competition,
       s.type AS sub_type,
       s.gender AS sub_gender
FROM Competitions p
JOIN Competitions s ON s.parent_id = p.competition_id
ORDER BY p.competition_name, s.competition_name;

-- Q6: Analyze the distribution of competition types by category.
SELECT cat.category_name, c.type, COUNT(*) AS type_count
FROM Competitions c
JOIN Categories cat ON c.category_id = cat.category_id
GROUP BY cat.category_name, c.type
ORDER BY cat.category_name, c.type;

-- Q7: List all competitions with no parent (top-level competitions).
SELECT competition_id, competition_name, type, gender, category_id
FROM Competitions
WHERE parent_id IS NULL
ORDER BY category_id, competition_name;

-- Q8: List all venues along with their associated complex name.
SELECT v.venue_id, v.venue_name, v.city_name, v.country_name, v.country_code,
       v.timezone, cx.complex_name
FROM Venues v
JOIN Complexes cx ON v.complex_id = cx.complex_id
ORDER BY cx.complex_name, v.venue_name;

-- Q9: Count the number of venues in each complex.
SELECT cx.complex_name, COUNT(v.venue_id) AS venue_count
FROM Complexes cx
LEFT JOIN Venues v ON v.complex_id = cx.complex_id
GROUP BY cx.complex_id, cx.complex_name
ORDER BY venue_count DESC, cx.complex_name;

-- Q10: Get details of venues in a specific country (default 'Chile').
SELECT v.venue_id, v.venue_name, v.city_name, v.country_name, v.country_code,
       v.timezone, cx.complex_name
FROM Venues v
JOIN Complexes cx ON v.complex_id = cx.complex_id
WHERE v.country_name = :country_name
ORDER BY v.city_name, v.venue_name;

-- Q11: Identify all venues and their timezones.
SELECT v.venue_name, v.city_name, v.country_name, v.timezone
FROM Venues v
ORDER BY v.timezone, v.country_name, v.venue_name;

-- Q12: Find complexes that have more than one venue.
SELECT cx.complex_name, COUNT(v.venue_id) AS venue_count
FROM Complexes cx
JOIN Venues v ON v.complex_id = cx.complex_id
GROUP BY cx.complex_id, cx.complex_name
HAVING COUNT(v.venue_id) > 1
ORDER BY venue_count DESC, cx.complex_name;

-- Q13: List venues grouped by country.
SELECT v.country_name, v.country_code,
       COUNT(v.venue_id) AS venue_count,
       COUNT(DISTINCT v.city_name) AS city_count,
       COUNT(DISTINCT cx.complex_id) AS complex_count
FROM Venues v
JOIN Complexes cx ON v.complex_id = cx.complex_id
GROUP BY v.country_name, v.country_code
ORDER BY venue_count DESC, v.country_name;

-- Q14: Find all venues for a specific complex (default 'Nacional').
SELECT v.venue_id, v.venue_name, v.city_name, v.country_name, v.country_code,
       v.timezone, cx.complex_name
FROM Venues v
JOIN Complexes cx ON v.complex_id = cx.complex_id
WHERE cx.complex_name = :complex_name
ORDER BY v.venue_name;

-- Q15: Get all competitors with their rank and points.
SELECT co.competitor_id, co.name, co.country, co.country_code, co.abbreviation,
       r.rank, r.points, r.movement, r.competitions_played
FROM Competitors co
JOIN Competitor_Rankings r ON r.competitor_id = co.competitor_id
ORDER BY r.rank;

-- Q16: Find competitors ranked in the top 5.
SELECT co.name, co.country, r.rank, r.points, r.movement
FROM Competitor_Rankings r
JOIN Competitors co ON co.competitor_id = r.competitor_id
WHERE r.rank <= 5
ORDER BY r.rank;

-- Q17: List competitors with no rank movement.
SELECT co.name, co.country, r.rank, r.points, r.competitions_played
FROM Competitor_Rankings r
JOIN Competitors co ON co.competitor_id = r.competitor_id
WHERE r.movement = 0
ORDER BY r.rank;

-- Q18: Get the total points of competitors from a specific country (default 'Croatia').
SELECT co.country, COUNT(*) AS competitor_count,
       SUM(r.points) AS total_points,
       ROUND(AVG(r.points), 1) AS avg_points,
       MAX(r.rank) AS best_rank
FROM Competitors co
JOIN Competitor_Rankings r ON r.competitor_id = co.competitor_id
WHERE co.country = :country_name
GROUP BY co.country;

-- Q19: Count the number of competitors per country.
SELECT co.country, co.country_code, COUNT(*) AS competitor_count,
       SUM(r.points) AS total_points,
       ROUND(AVG(r.points), 1) AS avg_points
FROM Competitors co
JOIN Competitor_Rankings r ON r.competitor_id = co.competitor_id
GROUP BY co.country, co.country_code
ORDER BY competitor_count DESC, co.country;

-- Q20: Find competitors with the highest points in the current week.
SELECT co.name, co.country, r.rank, r.points, r.movement, r.competitions_played
FROM Competitor_Rankings r
JOIN Competitors co ON co.competitor_id = r.competitor_id
ORDER BY r.points DESC, r.rank ASC
LIMIT :top_n;
