"""Court Intel — Pro Tennis Tour Analytics Platform."""
import pandas as pd
import plotly.express as px
import sqlalchemy
import streamlit as st
from sqlalchemy import text
from zoneinfo import ZoneInfo
from datetime import datetime

import database
import queries as qmod

st.set_page_config(page_title="Court Intel — Pro Tennis Tour Analytics",
                   layout="wide", initial_sidebar_state="expanded")

# ------------------------------------------------------------------ CSS
st.markdown("""
<style>
    .stApp { background: #070b14; }
    section[data-testid="stSidebar"] { background: #0a0f1c; border-right: 1px solid #1c2740; }
    h1, h2, h3 { color: #e8edf7; letter-spacing: -0.01em; }
    .block-container { padding-top: 1.6rem; max-width: 1500px; }
    header[data-testid="stHeader"] { background: transparent; }

    .brand { font-size: 1.35rem; font-weight: 800; color: #34d399; letter-spacing: .12em; }
    .brand-sub { color: #64748b; font-size: .8rem; letter-spacing: .05em; text-transform: uppercase; }

    .kpi-card {
        background: linear-gradient(160deg, rgba(30,41,59,.85), rgba(15,23,42,.9));
        border: 1px solid rgba(51,65,85,.7); border-radius: 14px;
        padding: 1rem 1.1rem; backdrop-filter: blur(6px);
        box-shadow: 0 4px 18px rgba(0,0,0,.35);
    }
    .kpi-icon { font-size: 1.3rem; }
    .kpi-label { color: #94a3b8; font-size: .78rem; text-transform: uppercase; letter-spacing: .08em; }
    .kpi-value { color: #f1f5f9; font-size: 1.7rem; font-weight: 700; line-height: 1.15; }
    .kpi-sub { color: #64748b; font-size: .78rem; }

    .season-badge {
        display: inline-block; background: rgba(16,185,129,.12); color: #34d399;
        border: 1px solid rgba(16,185,129,.35); border-radius: 999px;
        padding: .2rem .8rem; font-size: .78rem; font-weight: 600; letter-spacing: .05em;
    }
    .up { color: #34d399; font-weight: 700; }
    .down { color: #f87171; font-weight: 700; }
    .flat { color: #94a3b8; font-weight: 700; }

    div[data-testid="stMetric"] {
        background: #0f172a; border: 1px solid #1e293b; border-radius: 10px; padding: .55rem;
    }
    .draw-card {
        background: #0f172a; border: 1px solid #1e293b; border-radius: 10px;
        padding: .7rem .9rem; margin-bottom: .4rem;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------ DB
@st.cache_resource
def get_engine():
    engine = database.get_engine()
    database.ensure_database(engine)
    return engine


engine = get_engine()
counts = database.table_counts(engine)

# ------------------------------------------------------------------ Helpers
def read(sql, params=None):
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn, params=params or {})


def trend(m):
    if m > 0:
        return f"▲ +{int(m)}"
    if m < 0:
        return f"▼ {int(m)}"
    return "—"


def trend_html(m):
    if m > 0:
        return f'<span class="up">▲ +{int(m)}</span>'
    if m < 0:
        return f'<span class="down">▼ {int(m)}</span>'
    return '<span class="flat">—</span>'


CITY_COORDS = {
    "Santiago": (-33.45, -70.67), "La Serena": (-29.90, -71.25), "Vina del Mar": (-33.02, -71.55),
    "London": (51.51, -0.13), "Eastbourne": (50.77, 0.29),
    "Melbourne": (-37.81, 144.96), "Paris": (48.86, 2.35), "Villeneuve-d'Ascq": (50.62, 3.07),
    "New York": (40.71, -74.01), "Indian Wells": (33.72, -116.31),
    "Roquebrune-Cap-Martin": (43.75, 7.51), "Monte Carlo": (43.74, 7.42),
    "Rome": (41.90, 12.50), "Madrid": (40.42, -3.70), "Barcelona": (41.39, 2.17),
    "Halle": (51.48, 11.97), "Santa Ponsa": (39.58, 2.65), "Geneva": (46.20, 6.14),
    "Shanghai": (31.23, 121.47), "Tokyo": (35.68, 139.69), "Mason": (39.39, -84.31),
    "Montreal": (45.50, -73.57), "Toronto": (43.65, -79.38), "Dubai": (25.20, 55.27),
    "Doha": (25.29, 51.53), "Miami Gardens": (25.96, -80.24), "Yerevan": (40.18, 44.51),
    "Gstaad": (46.48, 7.28), "Palma de Mallorca": (39.57, 2.65), "Berlin": (52.52, 13.40),
    "Unterhaching": (48.06, 11.61), "Basel": (47.56, 7.59), "Hong Kong": (22.32, 114.17),
    "Seoul": (37.57, 126.98), "Hangzhou": (30.27, 120.16),
}
COUNTRY_COORDS = {
    "Chile": (-33.0, -71.0), "United Kingdom": (54.0, -2.0), "Australia": (-25.0, 133.0),
    "France": (47.0, 2.0), "United States": (39.8, -98.6), "Monaco": (43.7, 7.4),
    "Italy": (42.8, 12.8), "Spain": (40.4, -3.7), "Germany": (51.2, 10.4),
    "Switzerland": (46.8, 8.2), "Canada": (56.1, -106.3), "United Arab Emirates": (24.0, 54.0),
    "Qatar": (25.3, 51.2), "Armenia": (40.1, 45.0), "China": (35.9, 104.2),
    "Japan": (36.2, 138.3), "Hong Kong": (22.3, 114.2), "South Korea": (36.5, 127.9),
}
DARK = dict(paper_bgcolor="#070b14", plot_bgcolor="#0b1220", font_color="#e8edf7",
            margin=dict(l=10, r=10, t=45, b=10))


def venues_with_coords():
    df = read("""
        SELECT v.venue_id, v.venue_name, v.city_name, v.country_name, v.country_code,
               v.timezone, cx.complex_name
        FROM Venues v JOIN Complexes cx ON v.complex_id = cx.complex_id
    """)
    coords = df["city_name"].map(lambda c: CITY_COORDS.get(c)).apply(
        lambda p: p if p is not None else (None, None))
    df["lat"] = coords.apply(lambda t: t[0])
    df["lon"] = coords.apply(lambda t: t[1])
    for idx in df.index[df["lat"].isna()]:
        cc = COUNTRY_COORDS.get(df.loc[idx, "country_name"])
        if cc:
            df.loc[idx, ["lat", "lon"]] = cc
    df = df.dropna(subset=["lat", "lon"]).copy()
    try:
        df["local_time"] = df["timezone"].map(
            lambda tz: datetime.now(ZoneInfo(tz)).strftime("%H:%M"))
        df["utc_offset"] = df["timezone"].map(
            lambda tz: datetime.now(ZoneInfo(tz)).strftime("UTC%z")[:3] + ":" +
                       datetime.now(ZoneInfo(tz)).strftime("%z")[3:])
    except Exception:
        df["local_time"] = ""
        df["utc_offset"] = ""
    return df


# ------------------------------------------------------------------ Session state
def _epoch():
    return st.session_state.get("filter_epoch", 0)


def wk(name):
    return f"{name}_{_epoch()}"


def reset_filters():
    st.session_state["filter_epoch"] = st.session_state.get("filter_epoch", 0) + 1
    st.rerun()


# ------------------------------------------------------------------ Sidebar
with st.sidebar:
    st.markdown('<div class="brand">🎾 COURT INTEL</div>'
                '<div class="brand-sub">Pro Tennis Tour Analytics</div>',
                unsafe_allow_html=True)

    if st.button("Sync Latest Tour Data", width="stretch"):
        with st.spinner("Synchronizing tour data…"):
            database.run_etl(engine)
            get_engine.clear()
            st.cache_resource.clear()
        st.rerun()

    st.divider()
    st.markdown("**Filters**")

    def _options(table, col, order=""):
        with engine.connect() as conn:
            return [r[0] for r in conn.execute(text(f"SELECT DISTINCT {col} FROM {table} {order}"))]

    categories = _options("Categories", "category_name", "ORDER BY category_name")
    comp_types = _options("Competitions", "type", "ORDER BY type")
    genders = _options("Competitions", "gender", "ORDER BY gender")
    countries = _options("Competitors", "country", "ORDER BY country")
    venue_countries = _options("Venues", "country_name", "ORDER BY country_name")

    f_category = st.selectbox("Category", ["All"] + categories, key=wk("cat"))
    f_type = st.selectbox("Competition Type", ["All"] + comp_types, key=wk("ctype"))
    f_gender = st.selectbox("Gender", ["All"] + genders, key=wk("gender"))
    f_country = st.selectbox("Country", ["All"] + countries, key=wk("country"))
    st.markdown("**Rank Range**")
    f_rank = st.slider("Rank Range", 1, 66, (1, 66), format="%d", key=wk("rank"),
                       label_visibility="collapsed")

    if st.button("Reset All Filters", width="stretch"):
        reset_filters()

# ------------------------------------------------------------------ Filtered data
def filtered_competitions():
    return read("""
        SELECT c.*, cat.category_name
        FROM Competitions c JOIN Categories cat ON c.category_id = cat.category_id
        WHERE (:cat = 'All' OR cat.category_name = :cat)
          AND (:typ = 'All' OR c.type = :typ)
          AND (:gen = 'All' OR c.gender = :gen)
        ORDER BY cat.category_name, c.competition_name
    """, {"cat": f_category, "typ": f_type, "gen": f_gender})


def filtered_rankings():
    return read("""
        SELECT co.*, r.rank, r.movement, r.points, r.competitions_played
        FROM Competitors co
        JOIN Competitor_Rankings r ON r.competitor_id = co.competitor_id
        WHERE (:country = 'All' OR co.country = :country)
          AND r.rank BETWEEN :rmin AND :rmax
        ORDER BY r.rank
    """, {"country": f_country, "rmin": f_rank[0], "rmax": f_rank[1]})


comp_df = filtered_competitions()
rdf = filtered_rankings()

# ------------------------------------------------------------------ Header
st.markdown("# Global Tennis Tour Analytics")
st.markdown('<span class="season-badge">2025–26 TOUR SEASON</span>',
            unsafe_allow_html=True)

hq1, hq2, hq3, hq4 = st.columns(4)
hq1.metric("Tournaments", counts["Competitions"])
hq2.metric("Stadiums & Courts", counts["Venues"])
hq3.metric("Ranked Nations", read("SELECT COUNT(DISTINCT country) n FROM Competitors").iloc[0, 0])
hq4.metric("Tour Points Leader", f"{read('SELECT MAX(points) p FROM Competitor_Rankings').iloc[0,0]:,}")

# ------------------------------------------------------------------ Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Tour Overview",
    "Tournaments & Draws",
    "Stadiums & Venues",
    "Player Scouting & Rankings",
    "Tour Reports",
])

# ================================================================ TAB 1
with tab1:
    st.subheader("Tour Overview")

    top_points = int(rdf["points"].max()) if not rdf.empty else 0
    kpis = [
        ("🏆", "Active Tournaments", len(comp_df), "matching current filters"),
        ("🎾", "Ranked Pros", len(rdf), "in the current view"),
        ("🌍", "Nations Represented", int(rdf["country"].nunique()) if not rdf.empty else 0,
         "countries across the rankings"),
        ("⭐", "Top Seed", f"{top_points:,} pts", "highest points in view"),
        ("🏟️", "Global Stadiums", counts["Venues"], "venues & courts worldwide"),
    ]
    cols = st.columns(5)
    for col, (icon, label, val, sub) in zip(cols, kpis):
        col.markdown(
            f'<div class="kpi-card"><div class="kpi-icon">{icon}</div>'
            f'<div class="kpi-label">{label}</div><div class="kpi-value">{val}</div>'
            f'<div class="kpi-sub">{sub}</div></div>', unsafe_allow_html=True)

    g1, g2 = st.columns(2)
    with g1:
        sun = comp_df.groupby(["category_name", "type"]).size().reset_index(name="Events")
        fig = px.sunburst(sun, path=["category_name", "type"], values="Events",
                          color="Events", color_continuous_scale="Emrld",
                          title="Tournament Breakdown by Tour & Format")
        fig.update_layout(height=400, **DARK)
        st.plotly_chart(fig, width="stretch")
    with g2:
        vdf = venues_with_coords()
        agg = vdf.groupby(["lat", "lon", "country_name"]).size().reset_index(name="venues")
        fig = px.scatter_geo(agg, lat="lat", lon="lon", size="venues",
                             color="country_name", hover_name="country_name",
                             hover_data={"venues": True, "lat": False, "lon": False},
                             size_max=28, projection="natural earth",
                             title="Global Stadium & Venue Map",
                             labels={"venues": "Venues", "country_name": "Country"})
        fig.update_layout(height=400, **DARK,
                          geo=dict(bgcolor="#070b14", landcolor="#111a2e", lakecolor="#070b14",
                                   oceancolor="#070b14", showland=True, showcountries=True,
                                   countrycolor="#1c2740", coastlinecolor="#1c2740"))
        st.plotly_chart(fig, width="stretch")

    g3, g4 = st.columns(2)
    with g3:
        top10 = rdf.nsmallest(10, "rank").copy()
        top10["trend"] = top10["movement"].map(lambda m: str(trend(m)))
        fig = px.bar(top10.sort_values("points"), x="points", y="name", orientation="h",
                     color="points", color_continuous_scale="Viridis",
                     hover_data={"rank": True, "trend": True, "competitions_played": True},
                     text="trend", title="Top 10 Ranked Doubles Pros",
                     labels={"points": "Ranking Points", "name": "Pair"})
        fig.update_layout(height=400, **DARK, yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig, width="stretch")
    with g4:
        fig = px.scatter(rdf, x="competitions_played", y="points", size="points",
                         color="country", hover_name="name", size_max=16,
                         labels={"competitions_played": "Events Played",
                                 "points": "Ranking Points", "country": "Nation"},
                         title="Points vs Events Played — Efficiency")
        fig.update_layout(height=400, **DARK)
        st.plotly_chart(fig, width="stretch")

# ================================================================ TAB 2
with tab2:
    st.subheader("Tournaments & Draws")

    tcat = st.selectbox("Tour", categories, key=wk("tcat"))
    parents = read("""
        SELECT competition_id, competition_name, type, gender
        FROM Competitions
        WHERE parent_id IS NULL
          AND category_id = (SELECT category_id FROM Categories WHERE category_name = :cat)
        ORDER BY competition_name
    """, {"cat": tcat})

    if parents.empty:
        st.info("No tournaments in this tour.")
    else:
        sel = st.selectbox("Parent Event", parents["competition_name"].tolist(),
                           key=wk("tparent"))
        prow = parents[parents["competition_name"] == sel].iloc[0]
        children = read("""
            SELECT competition_name, type, gender
            FROM Competitions WHERE parent_id = :pid ORDER BY type, competition_name
        """, {"pid": prow["competition_id"]})

        st.markdown(f"### {sel}")
        st.caption(f"{tcat} · {prow['type'].title()} · {prow['gender'].title()} division")

        draw_rows = ([{"competition_name": sel, "type": prow["type"], "gender": prow["gender"]}]
                     if children.empty else children.to_dict("records"))
        for d in draw_rows:
            st.markdown(
                f'<div class="draw-card"><b>{d["competition_name"]}</b><br>'
                f'<span style="color:#64748b;font-size:.85rem">'
                f'{d["type"].title()} draw · {d["gender"].title()}</span></div>',
                unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            g = read("""
                SELECT gender, COUNT(*) AS n FROM Competitions
                WHERE category_id = (SELECT category_id FROM Categories WHERE category_name = :cat)
                GROUP BY gender ORDER BY gender
            """, {"cat": tcat})
            fig = px.pie(g, names="gender", values="n", hole=0.55,
                         color_discrete_sequence=px.colors.sequential.Emrld,
                         title=f"{tcat} — Gender Split")
            fig.update_layout(height=300, **DARK)
            st.plotly_chart(fig, width="stretch")
        with c2:
            t = read("""
                SELECT type, COUNT(*) AS n FROM Competitions
                WHERE category_id = (SELECT category_id FROM Categories WHERE category_name = :cat)
                GROUP BY type ORDER BY type
            """, {"cat": tcat})
            fig = px.bar(t, x="type", y="n", color="type",
                         color_discrete_sequence=px.colors.sequential.Emrld,
                         title=f"{tcat} — Draw Format Mix",
                         labels={"type": "Draw Format", "n": "Events"})
            fig.update_layout(height=300, **DARK)
            st.plotly_chart(fig, width="stretch")

    st.markdown("**Draw Divisions Across the Selected Tour**")
    rel = read("""
        SELECT p.competition_name AS parent_event, s.competition_name AS division,
               s.type AS format, s.gender
        FROM Competitions p JOIN Competitions s ON s.parent_id = p.competition_id
        WHERE p.category_id = (SELECT category_id FROM Categories WHERE category_name = :cat)
        ORDER BY p.competition_name, s.competition_name
    """, {"cat": tcat})
    if rel.empty:
        st.caption("Standalone events without sub-draws in this tour.")
    else:
        st.dataframe(rel, width="stretch", hide_index=True)

# ================================================================ TAB 3
with tab3:
    st.subheader("Stadiums & Venues")
    vdf = venues_with_coords()

    mcol, rcol = st.columns([2, 1])
    with mcol:
        st.markdown("**Tournament Venue Map**")
        fig = px.scatter_map(vdf, lat="lat", lon="lon", color="country_name",
                             size_max=18, hover_name="venue_name",
                             hover_data={"city_name": True, "complex_name": True,
                                         "country_name": True, "timezone": True,
                                         "local_time": True},
                             zoom=1, height=470,
                             title="Venues Across the Tennis World")
        fig.update_layout(**DARK)
        st.plotly_chart(fig, width="stretch")
    with rcol:
        multi = read("""
            SELECT cx.complex_name, COUNT(v.venue_id) AS courts
            FROM Complexes cx JOIN Venues v ON v.complex_id = cx.complex_id
            GROUP BY cx.complex_id, cx.complex_name
            HAVING COUNT(v.venue_id) > 1 ORDER BY courts DESC
        """)
        fig = px.bar(multi, x="courts", y="complex_name", orientation="h",
                     color="courts", color_continuous_scale="Teal",
                     title="Multi-Court Tournament Complexes",
                     labels={"courts": "Courts", "complex_name": "Complex"})
        fig.update_layout(height=470, **DARK, yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig, width="stretch")

    st.markdown("**Global Venue Directory — Local Times**")
    d1, d2 = st.columns([2, 1])
    search = d1.text_input("Search venue, city, complex or country", "", key=wk("vsearch"))
    tz_sel = d2.multiselect("Timezone", sorted(vdf["timezone"].unique()), key=wk("vtz"))
    mask = pd.Series(True, index=vdf.index)
    if search:
        s = search.lower()
        mask &= vdf.apply(lambda r: s in " ".join(str(x).lower() for x in
                     [r["venue_name"], r["city_name"], r["country_name"], r["complex_name"]]), axis=1)
    if tz_sel:
        mask &= vdf["timezone"].isin(tz_sel)
    show = vdf[mask].sort_values(["country_name", "city_name", "venue_name"])
    st.dataframe(show[["venue_name", "complex_name", "city_name", "country_name",
                       "timezone", "utc_offset", "local_time"]],
                 width="stretch", hide_index=True)

# ================================================================ TAB 4
with tab4:
    st.subheader("Player Scouting & Rankings")

    if rdf.empty:
        st.warning("No players match the current filters.")
    else:
        names = rdf.sort_values("rank")["name"].tolist()
        pick = st.selectbox("Scout a Player / Doubles Pair", names, key=wk("comp_pick"))
        prow = rdf[rdf["name"] == pick].iloc[0]

        st.markdown(f"### {prow['name']}")
        st.caption(f"{prow['country']} ({prow['country_code']})")
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("World Rank", int(prow["rank"]))
        m2.markdown(f"**Weekly Movement**<br>{trend_html(int(prow['movement']))}",
                    unsafe_allow_html=True)
        m3.metric("Ranking Points", f"{int(prow['points']):,}")
        m4.metric("Events Played", int(prow["competitions_played"]))
        m5.metric("Points / Event", f"{int(prow['points']) / max(int(prow['competitions_played']), 1):.0f}")

        leader = rdf.loc[rdf["rank"].idxmin()]
        if prow["name"] != leader["name"]:
            b1, b2, b3 = st.columns(3)
            b1.metric("Gap to #1 — Points", f"{int(leader['points']) - int(prow['points']):,}")
            b2.metric("Gap to #1 — Rank", int(prow["rank"]) - int(leader["rank"]))
            b3.metric("Benchmark Pair", leader["name"].split(" /")[0])

        st.divider()
        st.markdown("**Head-to-Head Comparison**")
        h1, h2 = st.columns(2)
        pa = h1.selectbox("Player A", names, index=names.index(pick), key=wk("h2h_a"))
        remaining = [n for n in names if n != pa]
        pb = h2.selectbox("Player B", remaining,
                          index=min(1, len(remaining) - 1), key=wk("h2h_b"))
        A = rdf[rdf["name"] == pa].iloc[0]
        B = rdf[rdf["name"] == pb].iloc[0]
        def _row(p):
            return [str(int(p["rank"])), f"{int(p['points']):,}", trend(int(p["movement"])),
                    str(int(p["competitions_played"])),
                    f"{int(p['points']) / max(int(p['competitions_played']), 1):.1f}",
                    str(p["country"])]
        cmp_df = pd.DataFrame({
            "Metric": ["World Rank", "Ranking Points", "Weekly Trend", "Events Played",
                       "Points / Event", "Nation"],
            pa.split(" /")[0]: _row(A),
            pb.split(" /")[0]: _row(B),
        }).astype(str)
        st.dataframe(cmp_df, width="stretch", hide_index=True)
        winner = pa if int(A["points"]) >= int(B["points"]) else pb
        st.caption(f"Points edge: **{winner}**")

        st.divider()
        st.markdown("**Leaderboard & Nation Dominance**")
        l1, l2 = st.columns(2)
        with l1:
            st.markdown("Top Ranked")
            lb = rdf.nsmallest(10, "rank")[["rank", "name", "country", "points", "movement"]].copy()
            lb["trend"] = lb["movement"].map(lambda m: str(trend(m)))
            st.dataframe(lb[["rank", "name", "country", "points", "trend"]],
                         width="stretch", hide_index=True)
        with l2:
            st.markdown("Highest Points")
            hp = rdf.nlargest(10, "points")[["rank", "name", "country", "points", "movement"]].copy()
            hp["trend"] = hp["movement"].map(lambda m: str(trend(m)))
            st.dataframe(hp[["rank", "name", "country", "points", "trend"]],
                         width="stretch", hide_index=True)

        ctry = read("""
            SELECT co.country, COUNT(*) AS players,
                   SUM(r.points) AS total_points, ROUND(AVG(r.points),1) AS avg_points,
                   MIN(r.rank) AS best_rank
            FROM Competitors co JOIN Competitor_Rankings r ON r.competitor_id = co.competitor_id
            GROUP BY co.country ORDER BY players DESC, co.country
        """)
        fig = px.bar(ctry.sort_values("players", ascending=True),
                     x="players", y="country", orientation="h",
                     color="avg_points", color_continuous_scale="Emrld",
                     hover_data={"total_points": True, "best_rank": True},
                     title="Nation Dominance — Players & Average Strength",
                     labels={"players": "Players", "country": "Nation"})
        fig.update_layout(height=380, **DARK, yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig, width="stretch")

# ================================================================ TAB 5
with tab5:
    st.subheader("Tour Reports")
    st.caption("Twenty curated analytical views across tournaments, venues and player rankings. "
               "Adjust the filters and export any report as CSV.")

    all_q = qmod.load_queries()
    labels = [f"Report {q['num']}: {q['label']}" for q in all_q]
    sel_label = st.selectbox("Choose a report", labels, key=wk("sql_pick"))
    sel = all_q[labels.index(sel_label)]

    params = {}
    if ":category_name" in sel["sql"]:
        params["category_name"] = st.selectbox("Tour", categories, key=wk("p_cat"))
    if ":country_name" in sel["sql"] and sel["num"] in (10, 18):
        opts = venue_countries if sel["num"] == 10 else countries
        params["country_name"] = st.selectbox("Country", opts, key=wk(f"p_ctry_{sel['num']}"))
    if ":complex_name" in sel["sql"]:
        with engine.connect() as conn:
            cx_names = [r[0] for r in conn.execute(
                text("SELECT complex_name FROM Complexes ORDER BY complex_name"))]
        params["complex_name"] = st.selectbox("Tournament Complex", cx_names, key=wk("p_cx"))
    if ":top_n" in sel["sql"]:
        params["top_n"] = st.slider("Records", 5, 66, 20, key=wk("p_topn"))

    try:
        df = qmod.run_query(engine, sel["num"], params)
        st.metric("Records", len(df))

        # Visual summary: bar of first numeric measure by first text dimension.
        num_cols = df.select_dtypes(include="number").columns.tolist()
        txt_cols = df.select_dtypes(include="object").columns.tolist()
        if num_cols and txt_cols and len(df) > 1:
            dim, meas = txt_cols[0], num_cols[0]
            summ = (df.groupby(dim, dropna=False)[meas].sum()
                    .sort_values(ascending=False).head(15).reset_index())
            fig = px.bar(summ, x=dim, y=meas,
                         title=f"{sel['label']} — {meas} by {dim}",
                         labels={dim: dim.replace("_", " ").title(), meas: meas.replace("_", " ").title()})
            fig.update_layout(height=320, **{k: v for k, v in DARK.items() if k != "margin"},
                              margin=dict(l=10, r=10, t=45, b=80),
                              xaxis_tickangle=-35)
            st.plotly_chart(fig, width="stretch")

        st.dataframe(df, width="stretch", hide_index=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, file_name=f"report_{sel['num']:02d}.csv",
                           mime="text/csv")
    except Exception as e:
        st.error(f"Unable to generate this report right now: {e}")

    with st.expander("Data Definition"):
        st.code(sel["sql"], language="sql")
