import html
import os
import sys

import pandas as pd
import streamlit as st

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from database import add_user, init_db, verify_user
from engine import ResourceEngine
from utils import generate_maps_link


st.set_page_config(
    page_title="Community Resource Finder",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()


STYLE = """
<style>
:root {
    --ink: #10212b;
    --muted: #5d6f78;
    --line: rgba(16, 33, 43, 0.12);
    --panel: rgba(255, 255, 255, 0.88);
    --teal: #0f766e;
    --coral: #e85d4f;
    --gold: #f2b84b;
}

[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(circle at 8% 8%, rgba(15, 118, 110, 0.18), transparent 32%),
        radial-gradient(circle at 95% 12%, rgba(232, 93, 79, 0.16), transparent 28%),
        linear-gradient(135deg, #f7fbfa 0%, #eef7f3 48%, #f8f5ed 100%);
}

[data-testid="stHeader"] {
    background: transparent;
}

.block-container {
    max-width: 1220px;
    padding-top: 1.4rem;
    padding-bottom: 2rem;
}

[data-testid="stSidebar"] {
    background: rgba(255, 255, 255, 0.72);
    border-right: 1px solid var(--line);
}

h1, h2, h3 {
    color: var(--ink);
    letter-spacing: 0;
}

.app-hero {
    border: 1px solid var(--line);
    border-radius: 8px;
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.92), rgba(239, 249, 246, 0.88));
    padding: 1.05rem 1.15rem;
    box-shadow: 0 18px 42px rgba(17, 50, 50, 0.08);
}

.app-title {
    font-size: clamp(1.85rem, 3vw, 3.05rem);
    line-height: 1.05;
    font-weight: 800;
    margin: 0 0 0.35rem;
}

.app-subtitle {
    color: var(--muted);
    font-size: 1rem;
    margin: 0;
    max-width: 760px;
}

.auth-panel {
    max-width: 760px;
    margin: 2.25rem auto 0;
    border: 1px solid var(--line);
    border-radius: 8px;
    background: rgba(255, 255, 255, 0.9);
    padding: 1.25rem;
    box-shadow: 0 24px 60px rgba(18, 40, 45, 0.12);
}

.metric-row {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.75rem;
    margin-top: 0.8rem;
}

.metric-card {
    border: 1px solid var(--line);
    border-radius: 8px;
    background: rgba(255, 255, 255, 0.82);
    padding: 0.78rem 0.9rem;
}

.metric-value {
    color: var(--teal);
    font-size: 1.35rem;
    font-weight: 800;
}

.metric-label {
    color: var(--muted);
    font-size: 0.82rem;
}

.resource-card {
    border: 1px solid var(--line);
    border-left: 4px solid var(--teal);
    border-radius: 8px;
    background: var(--panel);
    padding: 0.9rem 0.95rem;
    margin-bottom: 0.7rem;
    box-shadow: 0 12px 30px rgba(17, 50, 50, 0.07);
}

.resource-title {
    color: var(--ink);
    font-size: 1.02rem;
    font-weight: 800;
    margin-bottom: 0.2rem;
}

.resource-meta {
    color: var(--muted);
    font-size: 0.86rem;
    line-height: 1.45;
    margin-bottom: 0.48rem;
}

.pill {
    display: inline-block;
    color: #163039;
    background: rgba(15, 118, 110, 0.1);
    border: 1px solid rgba(15, 118, 110, 0.17);
    border-radius: 999px;
    padding: 0.16rem 0.52rem;
    margin: 0.08rem 0.18rem 0.08rem 0;
    font-size: 0.76rem;
}

.map-link {
    display: inline-block;
    color: #ffffff !important;
    background: #0f766e;
    border-radius: 6px;
    padding: 0.42rem 0.62rem;
    margin-top: 0.42rem;
    text-decoration: none !important;
    font-size: 0.82rem;
    font-weight: 700;
}

.notice {
    border: 1px solid rgba(232, 93, 79, 0.22);
    border-left: 4px solid var(--coral);
    border-radius: 8px;
    background: rgba(255, 255, 255, 0.74);
    color: #5b332f;
    padding: 0.75rem 0.85rem;
    font-size: 0.88rem;
    margin-top: 0.75rem;
}

button[kind="secondary"] {
    border-radius: 6px;
}

@media (max-width: 760px) {
    .metric-row {
        grid-template-columns: 1fr;
    }
    .app-hero,
    .auth-panel {
        padding: 0.95rem;
    }
}
</style>
"""


def apply_styles():
    st.markdown(STYLE, unsafe_allow_html=True)


@st.cache_resource(show_spinner="Building the AI resource index...")
def load_engine():
    return ResourceEngine()


def escape(value):
    return html.escape(str(value or ""))


def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if "username" not in st.session_state:
        st.session_state["username"] = ""

    if st.session_state["authenticated"]:
        return True

    st.markdown(
        """
        <div class="auth-panel">
            <div class="app-title">Community Resource Finder</div>
            <p class="app-subtitle">Sign in to search hospitals, food help, NGOs, shops, malls, and transportation from one chat.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_login, tab_register = st.tabs(["Login", "Register"])

    with tab_login:
        with st.form("login_form"):
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Login", width="stretch")
            if submitted:
                if verify_user(username, password):
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = username.strip()
                    st.rerun()
                else:
                    st.error("Invalid username or password.")

    with tab_register:
        with st.form("register_form"):
            new_username = st.text_input("Choose username", key="register_username")
            new_password = st.text_input(
                "Choose password", type="password", key="register_password"
            )
            confirm_password = st.text_input(
                "Confirm password", type="password", key="confirm_password"
            )
            submitted = st.form_submit_button("Create account", width="stretch")
            if submitted:
                if len(new_username.strip()) < 3:
                    st.warning("Username must be at least 3 characters.")
                elif len(new_password) < 6:
                    st.warning("Password must be at least 6 characters.")
                elif new_password != confirm_password:
                    st.error("Passwords do not match.")
                elif add_user(new_username, new_password):
                    st.success("Account created. You can login now.")
                else:
                    st.error("Username already exists.")

    return False


def initialize_chat():
    if "messages" not in st.session_state:
        st.session_state["messages"] = [
            {
                "role": "assistant",
                "content": "Tell me what you need and where you are. I can match you with nearby community resources.",
            }
        ]
    if "latest_results" not in st.session_state:
        st.session_state["latest_results"] = []
    if "user_city" not in st.session_state:
        st.session_state["user_city"] = ""
    if "user_area" not in st.session_state:
        st.session_state["user_area"] = ""


def is_near_me_query(query):
    text = (query or "").lower()
    near_me_phrases = [
        "near me",
        "nearby",
        "near my location",
        "around me",
        "closest",
        "nearest",
    ]
    return any(phrase in text for phrase in near_me_phrases)


def format_location(city, area=""):
    city = (city or "").strip()
    area = (area or "").strip()
    if city and area:
        return f"{area}, {city}"
    return city or area


def normalize_area_for_search(area):
    area = (area or "").strip()
    replacements = {
        "anant vihar": "Anand Vihar",
        "anand vihar terminal": "Anand Vihar ISBT",
        "anant vihar terminal": "Anand Vihar ISBT",
    }
    lowered = area.lower()
    for wrong, corrected in replacements.items():
        if wrong in lowered:
            lowered = lowered.replace(wrong, corrected.lower())
    return lowered


def make_reply(query, results, location_context=None):
    if not results:
        if location_context:
            return f"I searched near {location_context}, but could not find a strong match. Try a broader resource type or nearby landmark."
        return "I could not find a strong match. Try a city, area, or resource type like free food, hospital, NGO, mall, shops, or bus."

    top = results[0]
    lines = []
    if location_context:
        lines.append(f"Using your location: {location_context}.")
    lines.extend([
        f"Best match: {top['name']} in {top['city']} ({top['category']}).",
        f"Address: {top['location']}.",
    ])
    if top.get("services"):
        lines.append("Useful for: " + ", ".join(top["services"][:4]) + ".")
    if len(results) > 1:
        lines.append(
            "Other options: "
            + ", ".join(f"{r['name']} ({r['category']})" for r in results[1:4])
            + "."
        )
    lines.append("Please verify timings and availability before visiting.")
    return " ".join(lines)


def run_query(query, engine, category, city, result_count, user_city="", user_area=""):
    query = (query or "").strip()
    if not query:
        return

    detected_city = engine.detect_city(query)
    effective_city = city if city not in (None, "", "All") else detected_city or user_city or "All"
    effective_area = ""
    location_context = None
    query_for_search = query
    is_using_saved_location = bool(user_city) and effective_city == user_city

    if is_using_saved_location:
        effective_area = normalize_area_for_search(user_area)
        location_context = format_location(effective_city, user_area)

    if is_near_me_query(query):
        if effective_city in (None, "", "All"):
            st.session_state["messages"].append({"role": "user", "content": query})
            st.session_state["messages"].append(
                {
                    "role": "assistant",
                    "content": "Please set your city and area in the My Location section, then ask again with near me.",
                }
            )
            st.session_state["latest_results"] = []
            return

        query_for_search = query

    results = engine.search(
        query_for_search,
        top_k=result_count,
        category=category,
        city=effective_city,
        user_area=effective_area,
    )
    st.session_state["messages"].append({"role": "user", "content": query})
    st.session_state["messages"].append(
        {"role": "assistant", "content": make_reply(query, results, location_context)}
    )
    st.session_state["latest_results"] = results


def render_resource_card(resource, rank=None):
    services = resource.get("services") or resource.get("tags") or []
    pills = "".join(f'<span class="pill">{escape(item)}</span>' for item in services[:5])
    label = f"{rank}. " if rank else ""
    score = resource.get("_score")
    score_text = f"Match {score:.2f}" if isinstance(score, float) else "Recommended"
    maps_link = generate_maps_link(resource["name"], resource["location"])

    st.markdown(
        f"""
        <div class="resource-card">
            <div class="resource-title">{label}{escape(resource["name"])}</div>
            <div class="resource-meta">
                {escape(resource["category"])} in {escape(resource["city"])} | {escape(score_text)}<br>
                {escape(resource["location"])}<br>
                Hours: {escape(resource.get("hours"))} | Cost: {escape(resource.get("cost"))}
            </div>
            <div>{pills}</div>
            <a class="map-link" href="{maps_link}" target="_blank">Open in Google Maps</a>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metrics(engine):
    st.markdown(
        f"""
        <div class="metric-row">
            <div class="metric-card">
                <div class="metric-value">{len(engine.resources)}</div>
                <div class="metric-label">resource records</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{len(engine.categories)}</div>
                <div class="metric-label">resource categories</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{len(engine.cities)}</div>
                <div class="metric-label">cities covered</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(engine):
    st.sidebar.title("Finder Controls")
    st.sidebar.subheader("My Location")
    city_options = [""] + engine.cities
    user_city = st.sidebar.selectbox(
        "My city",
        city_options,
        format_func=lambda value: "Select city" if value == "" else value,
        key="user_city",
    )
    user_area = st.sidebar.text_input(
        "Area / landmark",
        key="user_area",
        placeholder="e.g., Doctors Colony, Kankarbagh",
    )
    if user_city:
        st.sidebar.success(f"Search uses {format_location(user_city, user_area)}")
    else:
        st.sidebar.info("Set city and area so searches stay local.")

    st.sidebar.divider()
    st.sidebar.subheader("Search Filters")
    city = st.sidebar.selectbox("Filter city", ["All"] + engine.cities)
    category = st.sidebar.selectbox("Category", ["All"] + engine.categories)
    result_count = st.sidebar.slider("Results", min_value=3, max_value=8, value=5)

    if st.sidebar.button("Clear chat", width="stretch"):
        st.session_state.pop("messages", None)
        st.session_state.pop("latest_results", None)
        st.rerun()

    if st.sidebar.button("Logout", width="stretch"):
        st.session_state["authenticated"] = False
        st.session_state["username"] = ""
        st.rerun()

    mode = "semantic AI" if engine.model is not None else "keyword fallback"
    st.sidebar.caption(f"Signed in as {st.session_state['username'] or 'user'}")
    st.sidebar.caption(f"Search mode: {mode}")
    return category, city, result_count, user_city, user_area


def render_app():
    engine = load_engine()
    initialize_chat()
    category, city, result_count, user_city, user_area = render_sidebar(engine)

    st.markdown(
        """
        <div class="app-hero">
            <div class="app-title">Community Resource Finder</div>
            <p class="app-subtitle">Search local help across hospitals, shops, malls, free food, NGOs, and transportation.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_metrics(engine)

    st.markdown(
        """
        <div class="notice">
            For emergencies, contact local emergency services first. Resource hours and availability can change, so verify before visiting.
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.16, 0.84], gap="large")

    with left:
        st.subheader("Chat")
        quick_prompts = [
            "hospital near me",
            "shops near me",
            "bus stand near me",
            "cab stand near me",
        ]
        prompt_cols = st.columns(4)
        for col, prompt in zip(prompt_cols, quick_prompts):
            if col.button(prompt, width="stretch"):
                st.session_state["pending_query"] = prompt

        for message in st.session_state["messages"]:
            with st.chat_message(message["role"]):
                st.write(message["content"])

    with right:
        st.subheader("Top Matches")
        latest_results = st.session_state.get("latest_results", [])
        if latest_results:
            map_rows = [
                {"lat": r.get("lat"), "lon": r.get("lon")}
                for r in latest_results
                if r.get("lat") and r.get("lon")
            ]
            if map_rows:
                st.map(pd.DataFrame(map_rows), height=220)
            for index, resource in enumerate(latest_results[:result_count], start=1):
                render_resource_card(resource, index)
        else:
            st.info("Your matched resources will appear here.")

    pending_query = st.session_state.pop("pending_query", None)
    typed_query = st.chat_input("Ask for a resource, place, or need")
    if typed_query:
        pending_query = typed_query
    if pending_query:
        run_query(
            pending_query,
            engine,
            category,
            city,
            result_count,
            user_city,
            user_area,
        )
        st.rerun()


apply_styles()
if check_password():
    render_app()
