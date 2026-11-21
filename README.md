# Game Analytics: Unlocking Tennis Data with SportRadar API

An executive-grade **sports data analytics & visualization** platform covering the
world's tennis calendar — ATP, WTA, Challenger, ITF and all four Grand Slams —
built with **Python**, **SQL** and **Streamlit**.

Explore tournament hierarchies, global venue networks and live doubles rankings
through interactive dashboards, scouting profiles and curated business reports.

---

## What's Inside

- **Executive Dashboard** — headline KPIs, competition mix, global venue
  footprint map and the top doubles pairs by ranking points.
- **Tournament Hierarchy** — browse how every tournament breaks down into
  singles, doubles and mixed events, by category and gender.
- **Global Venues** — an interactive world map of tournament venues and
  complexes, multi-court venue analysis, and a searchable venue directory with
  local-timezone filtering.
- **Player Rankings & Profiler** — scout any doubles pair with rank, weekly
  movement, points and events played, benchmarked against the world #1, plus
  nation-by-nation depth analysis and leaderboards.
- **Executive Insights & Reports** — twenty curated, filterable reports with
  one-click CSV export.

## Coverage

| Area | Contents |
|---|---|
| Competitions | 150+ tournaments & events across 6 categories with parent → sub-event relationships |
| Venues | 40 tournament complexes / 66 venues across 19 countries, with cities and timezones |
| Players | 66 ranked doubles pairs with weekly movement, points and events played |

Notable coverage includes **Nacional (Chile)**, the **All England Club**,
**Melbourne Park**, **Stade Roland Garros**, the **USTA National Tennis Center**
and every Grand Slam draw.

## Quick Start

```bash
# 1. Create and activate a virtual environment (Python 3.14)
python -m venv .venv
.venv\Scripts\activate            # Windows
# source .venv/bin/activate       # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch the application
streamlit run app.py
```

Open **http://localhost:8501**. The application prepares its data warehouse
automatically on first launch — no API key or external service is required.

## Deploy to Streamlit Community Cloud

1. Push this repository to GitHub.
2. In [share.streamlit.io](https://share.streamlit.io), choose **New app**, select
   the repository, branch and `app.py`.
3. Select **Python 3.14** (or the closest available) and deploy.
   Dependencies install automatically from `requirements.txt`; the data
   warehouse is built on first boot.

## Keeping Data Fresh

Use **Sync Latest Tour Data** in the sidebar to refresh the feed at any time,
or from the command line:

```bash
python etl_pipeline.py --reset
```

## Data Model

```
Categories ──< Competitions >── parent ──> Competitions (self-join)
Complexes  ──< Venues
Competitors ──< Rankings
```

- **Categories** — ATP, WTA, Challenger, ITF Men, ITF Women, Grand Slam
- **Competitions** — tournaments and events with type (singles / doubles /
  mixed), gender and parent-child hierarchy
- **Complexes & Venues** — venue groups with city, country and IANA timezone
- **Competitors & Rankings** — doubles pairs with rank, weekly movement,
  points and events played

## Optional: MySQL Backend

The application runs fully on a local SQLite warehouse by default. To use MySQL
instead, provide credentials via environment variables, `.env` or
`.streamlit/secrets.toml`:

```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=tennis
MYSQL_PASSWORD=your-password
MYSQL_DATABASE=tennis_analytics
```

## Verification

```bash
python test_queries.py     # validates all tables & 20 reports return data
streamlit run app.py       # launches the application on :8501
```
