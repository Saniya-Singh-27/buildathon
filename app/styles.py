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

    .card {
        background: #1e1631;
        border: 1px solid rgba(255, 77, 141, 0.18);
        border-radius: 18px;
        padding: 1.6rem 1.8rem;
        box-shadow: 0 8px 24px rgba(168, 85, 247, 0.18);
        margin-bottom: 1.2rem;
        color: #f2ecff;
    }

    .card strong, .card p, .card label {
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

    .placeholder-tag {
        display: inline-block;
        background: #3b1650;
        color: #e6b3ff;
        font-size: 0.78rem;
        font-weight: 700;
        padding: 0.15rem 0.6rem;
        border-radius: 999px;
        margin-bottom: 0.8rem;
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
