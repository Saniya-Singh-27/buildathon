"""Custom CSS for the app. Kept in one place so main.py stays readable.

Theme is forced to dark via .streamlit/config.toml so rendering is
consistent regardless of the viewer's OS/browser preference. Every
custom element below sets its own `color` explicitly rather than
inheriting - that's what caused invisible white-on-white text before.
"""

CUSTOM_CSS = """
<style>
    #MainMenu, footer, header {visibility: hidden;}

    .stApp {
        background: linear-gradient(160deg, #120c1e 0%, #1a1030 50%, #0f1a2e 100%);
    }

    .block-container {
        padding-top: 2.5rem;
        max-width: 760px;
    }

    .big-title {
        font-size: 2.6rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0;
        background: linear-gradient(90deg, #ff4d8d, #a855f7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .subtitle {
        text-align: center;
        color: #b9aed6;
        font-size: 1.05rem;
        margin-top: 0.3rem;
        margin-bottom: 2rem;
    }

    /* Native st.container(border=True) boxes, styled as "cards".
       Custom unsafe_allow_html <div> wrappers don't work for this in
       Streamlit - a markdown-injected opening tag can't actually contain
       widgets rendered after it, they end up as separate sibling
       elements. Real bordered containers are the only reliable way.
       Streamlit gives every st.container() this same test id, including
       the implicit unbordered root block - that one gets the shared
       "st-emotion-cache-0" no-op class, so it's excluded here to avoid
       wrapping the entire page in a card. */
    div[data-testid="stVerticalBlockBorderWrapper"]:not(.st-emotion-cache-0) {
        background: #1e1631;
        border: 1px solid rgba(255, 77, 141, 0.18) !important;
        border-radius: 18px;
        padding: 0.4rem 0.6rem;
        box-shadow: 0 8px 24px rgba(168, 85, 247, 0.18);
        margin-bottom: 1.2rem;
        color: #f2ecff;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:not(.st-emotion-cache-0) strong,
    div[data-testid="stVerticalBlockBorderWrapper"]:not(.st-emotion-cache-0) p,
    div[data-testid="stVerticalBlockBorderWrapper"]:not(.st-emotion-cache-0) label {
        color: #f2ecff;
    }

    .or-divider {
        text-align: center;
        color: #8f7fb8;
        font-weight: 700;
        margin: 1.2rem 0;
        letter-spacing: 2px;
    }

    div.stButton > button {
        border-radius: 999px;
        font-weight: 700;
        padding: 0.6rem 1.4rem;
        border: 1px solid rgba(255, 255, 255, 0.12);
        color: #f2ecff;
        background: #2a2140;
    }

    div.stButton > button[kind="primary"] {
        background: linear-gradient(90deg, #ff4d8d, #a855f7);
        color: white;
        border: none;
    }

    div.stButton > button:disabled {
        color: #8f7fb8;
        background: #201936;
        border: 1px solid rgba(255, 255, 255, 0.06);
    }

    .verdict-banner {
        border-radius: 18px;
        padding: 1.4rem 1.8rem;
        text-align: center;
        font-size: 1.6rem;
        font-weight: 800;
        color: white;
        margin-bottom: 1.2rem;
    }

    .verdict-buy { background: linear-gradient(90deg, #22c55e, #16a34a); }
    .verdict-wait { background: linear-gradient(90deg, #f59e0b, #d97706); }
    .verdict-dontbuy { background: linear-gradient(90deg, #ef4444, #dc2626); }

    .price-tag {
        text-align: center;
        font-size: 2.2rem;
        font-weight: 800;
        color: #f2ecff;
        margin-bottom: 1rem;
    }

    .reason-item {
        font-size: 1.02rem;
        padding: 0.4rem 0;
        color: #ded4f5;
    }

    .bestie-note {
        background: #2a1a2e;
        border-left: 4px solid #ff4d8d;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        font-style: italic;
        font-size: 1.05rem;
        margin: 1rem 0 1.4rem 0;
        color: #f5d9ea;
    }

    .test-badge {
        display: inline-block;
        background: #3b1650;
        color: #ffd166;
        border: 1px solid rgba(255, 209, 102, 0.4);
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.5px;
        padding: 0.2rem 0.7rem;
        border-radius: 999px;
        margin-bottom: 0.6rem;
    }

    .ai-headline {
        text-align: center;
        font-size: 1.3rem;
        font-weight: 800;
        color: #ff9ec7;
        margin-bottom: 1rem;
    }

    [data-testid="stFileUploaderDropzone"] {
        background: #1e1631;
        border: 1px dashed rgba(255, 77, 141, 0.35);
    }

    [data-testid="stCaptionContainer"], .stCaption, small {
        color: #9c8fbf !important;
    }
</style>
"""
