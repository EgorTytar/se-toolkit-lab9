-- F1 Assistant V2 Database Schema
-- PostgreSQL 16+
-- This file can be used to manually initialize the database.
-- SQLAlchemy models in db/models.py will auto-create these via init_db().

CREATE TABLE IF NOT EXISTS users (
    id              SERIAL PRIMARY KEY,
    email           VARCHAR(255)    NOT NULL UNIQUE,
    password_hash   VARCHAR(255)    NOT NULL,
    display_name    VARCHAR(100)    NOT NULL,
    created_at      TIMESTAMP       NOT NULL DEFAULT NOW(),
    last_login      TIMESTAMP
);

CREATE INDEX idx_users_email ON users (email);

CREATE TABLE IF NOT EXISTS user_favorites (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER         NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    driver_id       VARCHAR(50),
    constructor_id  VARCHAR(50),
    created_at      TIMESTAMP       NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_favorites_user ON user_favorites (user_id);

CREATE TABLE IF NOT EXISTS reminders (
    id                  SERIAL PRIMARY KEY,
    user_id             INTEGER         NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    race_round          INTEGER         NOT NULL,
    race_year           INTEGER         NOT NULL,
    notify_before_hours INTEGER         NOT NULL DEFAULT 2,
    enabled             BOOLEAN         NOT NULL DEFAULT TRUE,
    method              VARCHAR(20)     NOT NULL DEFAULT 'email',
    created_at          TIMESTAMP       NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_reminders_user ON reminders (user_id);
CREATE INDEX idx_reminders_race ON reminders (race_year, race_round);

CREATE TABLE IF NOT EXISTS race_cache (
    year            INTEGER         NOT NULL,
    round           INTEGER         NOT NULL,
    race_name       VARCHAR(200)    NOT NULL,
    circuit         VARCHAR(200)    NOT NULL,
    date            VARCHAR(20)     NOT NULL,
    results_json    TEXT,
    ai_summary_json TEXT,
    cached_at       TIMESTAMP       NOT NULL DEFAULT NOW(),
    PRIMARY KEY (year, round)
);
