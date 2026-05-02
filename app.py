import requests
import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()


# =============================
# CONFIG
# =============================
API_BASE = os.getenv("API_BASE")
TMDB_IMG = "https://image.tmdb.org/t/p/w500"

st.set_page_config(
    page_title="Movie Recommender",
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="🎬"
)

# =============================
# STATE
# =============================
if "view" not in st.session_state:
    st.session_state.view = "home"

if "selected_tmdb_id" not in st.session_state:
    st.session_state.selected_tmdb_id = None


def goto_home():
    st.session_state.view = "home"
    st.rerun()


def goto_details(tmdb_id):
    st.session_state.view = "details"
    st.session_state.selected_tmdb_id = tmdb_id
    st.rerun()


# =============================
# STYLES
# =============================
st.markdown("""
<style>
.block-container {
    max-width: 1200px;
    padding-top: 1.5rem;
}

/* Cards */
.movie-card {
    position: relative;
    border-radius: 14px;
    overflow: hidden;
    cursor: pointer;
    transition: transform 0.2s ease;
}

.movie-card:hover {
    transform: scale(1.03);
}

.movie-img {
    width: 100%;
    display: block;
}

/* Overlay */
.overlay {
    position: absolute;
    inset: 0;
    background: linear-gradient(to top, rgba(0,0,0,0.75), rgba(0,0,0,0.2));
    opacity: 0;
    transition: opacity 0.25s ease;
    display: flex;
    align-items: flex-end;
    padding: 10px;
}

.movie-card:hover .overlay {
    opacity: 1;
}

.overlay-title {
    color: white;
    font-size: 0.9rem;
    font-weight: 500;
}

/* Buttons (works in dark + light) */
.stButton > button {
    width: 100%;
    border-radius: 8px;
    padding: 8px 0;
    font-size: 0.85rem;
    font-weight: 500;
    border: 1px solid rgba(128,128,128,0.2);
    background-color: rgba(128,128,128,0.15);
    color: inherit;
}

.stButton > button:hover {
    background-color: rgba(128,128,128,0.3);
}

/* Back button */
.back-btn button {
    width: auto !important;
    font-size: 0.95rem;
    font-weight: 500;
    padding: 6px 2px;
    margin-bottom: 10px;
    border: none;
    background: transparent;
    color: inherit;
}

.back-btn button:hover {
    text-decoration: underline;
}

/* Backdrop */
.backdrop-container {
    width: 100%;
    height: 600px;
    overflow: hidden;
    border-radius: 16px;
    margin-bottom: 20px;
}

.backdrop-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    filter: brightness(0.75);
}
</style>
""", unsafe_allow_html=True)


# =============================
# API
# =============================
@st.cache_data(ttl=60)
def api_get(path, params=None):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=20)
        return r.json()
    except:
        return None


# =============================
# GRID
# =============================
def poster_grid(cards, cols=6):
    rows = (len(cards) + cols - 1) // cols
    idx = 0

    for _ in range(rows):
        colset = st.columns(cols)

        for c in colset:
            if idx >= len(cards):
                break

            m = cards[idx]
            idx += 1

            with c:
                st.markdown(f"""
                <div class="movie-card">
                    <img class="movie-img" src="{m.get('poster_url') or ''}">
                    <div class="overlay">
                        <div class="overlay-title">{m.get('title')}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if st.button("View", key=f"view_{m['tmdb_id']}", use_container_width=True):
                    goto_details(m["tmdb_id"])


# =============================
# SIDEBAR
# =============================
with st.sidebar:
    st.markdown("### Browse")

    category_map = {
        "Trending": "trending",
        "Popular": "popular",
        "Top Rated": "top_rated",
        "Now Playing": "now_playing",
        "Upcoming": "upcoming"
    }

    selected_label = st.selectbox("Category", list(category_map.keys()))
    home_category = category_map[selected_label]
    grid_cols = st.slider("Columns", 4, 8, 6)


# =============================
# HEADER
# =============================
st.markdown("## Movie Recommender")

# =============================
# HOME
# =============================
if st.session_state.view == "home":

    query = st.text_input("", placeholder="Search movies...")

    if query:
        data = api_get("/tmdb/search", {"query": query})

        if data:
            cards = [
                {
                    "tmdb_id": m.get("id"),
                    "title": m.get("title"),
                    "poster_url": f"{TMDB_IMG}{m.get('poster_path')}" if m.get("poster_path") else None
                }
                for m in data.get("results", [])
            ]

            st.markdown("### Results")
            poster_grid(cards, grid_cols)

        st.stop()

    data = api_get("/home", {"category": home_category, "limit": 24})

    if data:
        st.markdown(f"### {home_category.title()}")
        poster_grid(data, grid_cols)


# =============================
# DETAILS
# =============================
elif st.session_state.view == "details":

    st.markdown('<div class="back-btn">', unsafe_allow_html=True)
    if st.button("← Back"):
        goto_home()
    st.markdown('</div>', unsafe_allow_html=True)

    data = api_get(f"/movie/id/{st.session_state.selected_tmdb_id}")

    if not data:
        st.stop()

    left, right = st.columns([1, 2])

    with left:
        if data.get("poster_url"):
            st.image(data["poster_url"], use_column_width=True)

    with right:
        st.markdown(f"### {data.get('title')}")

        release = data.get("release_date", "")
        genres = ", ".join([g["name"] for g in data.get("genres", [])])

        st.markdown(f"<div style='color:gray'>{release} • {genres}</div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.write(data.get("overview"))

    # Backdrop (top hero)
    if data.get("backdrop_url"):
        st.markdown(f"""
        <div class="backdrop-container">
            <img src="{data['backdrop_url']}" class="backdrop-img">
        </div>
        """, unsafe_allow_html=True)

    # =============================
    # RECOMMENDATIONS
    # =============================
    st.markdown("### You may also like")

    bundle = api_get("/movie/search", {
        "query": data.get("title"),
        "tfidf_top_n": 12,
        "genre_limit": 12
    })

    if bundle:
        tfidf_cards = []

        for x in bundle.get("tfidf_recommendations", []):
            if x.get("tmdb"):
                tfidf_cards.append({
                    "tmdb_id": x["tmdb"]["tmdb_id"],
                    "title": x["tmdb"]["title"],
                    "poster_url": x["tmdb"]["poster_url"],
                })

        poster_grid(tfidf_cards, grid_cols)

        st.markdown("### More from the same genre")
        poster_grid(bundle.get("genre_recommendations", []), grid_cols)