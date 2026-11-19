
import streamlit as st
import sys

if "/content" not in sys.path:
    sys.path.insert(0, "/content")

from homepage import render_homepage

st.set_page_config(
    page_title="Sai Charan Katta's Personal GPT",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ------------------------------------------------------------
# GLOBAL DARK THEME
# ------------------------------------------------------------

st.markdown("""
<style>
:root {
    color-scheme: dark;
}

.stApp {
    background: #17191D;
    color: #F3F4F6;
}

[data-testid="stAppViewContainer"] {
    background: #17191D;
}

[data-testid="stSidebar"] {
    display: none !important;
}

[data-testid="stHeader"] {
    background: transparent;
}

#MainMenu, footer {
    visibility: hidden;
}

.block-container {
    max-width: 1180px;
    padding-top: 1.2rem;
    padding-bottom: 3rem;
}

h1, h2, h3, h4 {
    color: #F9FAFB !important;
    letter-spacing: -0.5px;
}

p, label, li {
    color: #D1D5DB;
}

.stCaption, [data-testid="stCaptionContainer"] {
    color: #9CA3AF;
}

[data-testid="stMetric"] {
    background: #22252B;
    border: 1px solid #343840;
    border-radius: 14px;
    padding: 16px;
}

[data-testid="stMetricValue"] {
    color: #F9FAFB;
}

.stButton > button,
.stFormSubmitButton > button {
    background: #343840;
    color: #F9FAFB;
    border: 1px solid #454A54;
    border-radius: 10px;
    transition: all 0.2s ease;
}

.stButton > button:hover,
.stFormSubmitButton > button:hover {
    background: #454A54;
    border-color: #717784;
    color: white;
}

.stTextInput input,
.stTextArea textarea,
.stSelectbox div[data-baseweb="select"] {
    background: #22252B;
    color: #F9FAFB;
    border-color: #454A54;
    border-radius: 10px;
}

.stTabs [data-baseweb="tab-list"] {
    background: #202329;
    border-radius: 12px;
    gap: 5px;
}

.stTabs [data-baseweb="tab"] {
    color: #B8BEC8;
}

.stTabs [aria-selected="true"] {
    color: #FFFFFF !important;
}

hr {
    border-color: #383C44 !important;
}

.top-navigation {
    background: #1D2025;
    border: 1px solid #343840;
    border-radius: 16px;
    padding: 10px 16px;
    margin-bottom: 26px;
}

.brand-name {
    font-size: 18px;
    font-weight: 700;
    color: #F9FAFB;
    letter-spacing: -0.4px;
}

.brand-caption {
    font-size: 11px;
    color: #9CA3AF;
    margin-top: 2px;
}

.hero-panel {
    background: linear-gradient(135deg, #22252B, #191B20);
    border: 1px solid #383C44;
    border-radius: 22px;
    padding: 30px;
    margin-bottom: 20px;
}

.eyebrow {
    color: #A5AAB4;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 2.5px;
    text-transform: uppercase;
}

.portfolio-card {
    background: #22252B;
    border: 1px solid #383C44;
    border-radius: 16px;
    padding: 22px;
    margin-bottom: 14px;
}

.muted-text {
    color: #A1A1AA;
}

[data-testid="stPopover"] button {
    background: #292D34;
    border: 1px solid #454A54;
    border-radius: 10px;
}

@media (max-width: 640px) {
    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }

    .hero-panel {
        padding: 22px;
    }
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# HIDDEN STREAMLIT NAVIGATION + CUSTOM TOP NAVIGATION
# ------------------------------------------------------------

portfolio_page = st.Page(
    render_homepage,
    title="Portfolio",
    url_path="",
    default=True
)

chat_page = st.Page(
    "pages/chat.py",
    title="Personal GPT",
    url_path="chat"
)

admin_page = st.Page(
    "pages/admin.py",
    title="Admin",
    url_path="admin",
    visibility="hidden"
)

navigation = st.navigation(
    [portfolio_page, chat_page, admin_page],
    position="hidden"
)

# ------------------------------------------------------------

# ------------------------------------------------------------
# CUSTOM HEADER — NATIVE STREAMLIT LAYOUT
# ------------------------------------------------------------

with st.container(border=True):

    left, portfolio_col, chat_col, menu_col = st.columns(
        [3.5, 1.3, 1.5, 0.7],
        vertical_alignment="center"
    )

    with left:
        st.markdown(
            """
            <div class="brand-name">Sai Charan Katta's Personal GPT</div>
            <div class="brand-caption">PORTFOLIO • AI ASSISTANT</div>
            """,
            unsafe_allow_html=True
        )

    with portfolio_col:
        st.page_link(
            portfolio_page,
            label="Portfolio",
            icon="💼",
            use_container_width=True
        )

    with chat_col:
        st.page_link(
            chat_page,
            label="Personal GPT",
            icon="💬",
            use_container_width=True
        )

    with menu_col:
        with st.popover("⋯", use_container_width=True):
            st.page_link(
                admin_page,
                label="Admin access",
                icon="🔒"
            )

# RUN SELECTED PAGE
# ------------------------------------------------------------

navigation.run()
