-- ============================================================
-- Tennis Analytics Database Schema (SQLite-compatible DDL)
-- For MySQL, database.py automatically rewrites AUTOINCREMENT.
-- ============================================================

CREATE TABLE IF NOT EXISTS Categories (
    category_id   VARCHAR(50)  PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS Competitions (
    competition_id VARCHAR(50) PRIMARY KEY,
    competition_name VARCHAR(100) NOT NULL,
    parent_id      VARCHAR(50) NULL,
    type           VARCHAR(20) NOT NULL,
    gender         VARCHAR(10) NOT NULL,
    category_id    VARCHAR(50) NOT NULL,
    FOREIGN KEY (parent_id) REFERENCES Competitions(competition_id),
    FOREIGN KEY (category_id) REFERENCES Categories(category_id)
);

CREATE TABLE IF NOT EXISTS Complexes (
    complex_id   VARCHAR(50)  PRIMARY KEY,
    complex_name VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS Venues (
    venue_id      VARCHAR(50) PRIMARY KEY,
    venue_name    VARCHAR(100) NOT NULL,
    city_name     VARCHAR(100) NOT NULL,
    country_name  VARCHAR(100) NOT NULL,
    country_code  CHAR(3)      NOT NULL,
    timezone      VARCHAR(100) NOT NULL,
    complex_id    VARCHAR(50) NOT NULL,
    FOREIGN KEY (complex_id) REFERENCES Complexes(complex_id)
);

CREATE TABLE IF NOT EXISTS Competitors (
    competitor_id VARCHAR(50) PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    country       VARCHAR(100) NOT NULL,
    country_code  CHAR(3)      NOT NULL,
    abbreviation  VARCHAR(10)  NOT NULL
);

CREATE TABLE IF NOT EXISTS Competitor_Rankings (
    rank_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    rank                INT NOT NULL,
    movement            INT NOT NULL,
    points              INT NOT NULL,
    competitions_played INT NOT NULL,
    competitor_id       VARCHAR(50) NOT NULL,
    FOREIGN KEY (competitor_id) REFERENCES Competitors(competitor_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_competitions_category   ON Competitions(category_id);
CREATE INDEX IF NOT EXISTS idx_competitions_parent     ON Competitions(parent_id);
CREATE INDEX IF NOT EXISTS idx_competitions_type       ON Competitions(type);
CREATE INDEX IF NOT EXISTS idx_competitions_gender     ON Competitions(gender);
CREATE INDEX IF NOT EXISTS idx_venues_complex          ON Venues(complex_id);
CREATE INDEX IF NOT EXISTS idx_venues_country          ON Venues(country_name);
CREATE INDEX IF NOT EXISTS idx_rankings_competitor     ON Competitor_Rankings(competitor_id);
CREATE INDEX IF NOT EXISTS idx_rankings_rank           ON Competitor_Rankings(rank);
CREATE INDEX IF NOT EXISTS idx_rankings_points         ON Competitor_Rankings(points);
CREATE INDEX IF NOT EXISTS idx_competitors_country     ON Competitors(country);
