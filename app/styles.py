"""Custom CSS for the app. Kept in one place so main.py stays readable."""

CUSTOM_CSS = """
<style>
    #MainMenu, footer, header {visibility: hidden;}

    .stApp {
        background: linear-gradient(160deg, #fff0f6 0%, #f3e8ff 50%, #e8f0ff 100%);
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
        color: #6b6b6b;
        font-size: 1.05rem;
        margin-top: 0.3rem;
        margin-bottom: 2rem;
    }

    .card {
        background: white;
        border-radius: 18px;
        padding: 1.6rem 1.8rem;
        box-shadow: 0 8px 24px rgba(168, 85, 247, 0.10);
        margin-bottom: 1.2rem;
    }

    .or-divider {
        text-align: center;
        color: #b8a8c8;
        font-weight: 700;
        margin: 1.2rem 0;
        letter-spacing: 2px;
    }

    div.stButton > button {
        border-radius: 999px;
        font-weight: 700;
        padding: 0.6rem 1.4rem;
        border: none;
    }

    div.stButton > button[kind="primary"] {
        background: linear-gradient(90deg, #ff4d8d, #a855f7);
        color: white;
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
        color: #1f1f1f;
        margin-bottom: 1rem;
    }

    .reason-item {
        font-size: 1.02rem;
        padding: 0.4rem 0;
    }

    .bestie-note {
        background: #fdf2f8;
        border-left: 4px solid #ff4d8d;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        font-style: italic;
        font-size: 1.05rem;
        margin: 1rem 0 1.4rem 0;
    }

    .placeholder-tag {
        display: inline-block;
        background: #f3e8ff;
        color: #7e22ce;
        font-size: 0.78rem;
        font-weight: 700;
        padding: 0.15rem 0.6rem;
        border-radius: 999px;
        margin-bottom: 0.8rem;
    }
</style>
"""
