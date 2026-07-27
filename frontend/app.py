# =============================================================================
# PaperMind AI — Streamlit Main Application
# =============================================================================

import streamlit as st

# Must be the first Streamlit command
st.set_page_config(
    page_title="PaperMind AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

import requests

from components.sidebar import render_sidebar, upload_document

# API Base URL
API_URL = "http://localhost:8000/api/v1"

# Initialize Session State
if "doc_id" not in st.session_state:
    st.session_state.doc_id = None
if "doc_summary" not in st.session_state:
    st.session_state.doc_summary = None
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Welcome to PaperMind AI! Upload a paper to begin."}
    ]

EXAMPLE_PAPERS = [
    {
        "title": "Retrieval-Augmented Generation for Scientific Discovery",
        "subtitle": "Methods, evaluation, and citation-grounded responses",
    },
    {
        "title": "Multimodal Document Intelligence at Scale",
        "subtitle": "Figures, tables, equations, and layout-aware extraction",
    },
    {
        "title": "Knowledge Graphs for Research Exploration",
        "subtitle": "Concept links, authorship, and evidence traversal",
    },
]

FEATURE_CARDS = [
    {
        "title": "Read with context",
        "body": "Keep the source PDF, highlights, and extraction results aligned in one workspace.",
    },
    {
        "title": "Ask grounded questions",
        "body": "Receive answers with citations, jump-to-source links, and evidence trails.",
    },
    {
        "title": "Explore structure",
        "body": "Move from sections to figures, tables, equations, and concept graphs without losing context.",
    },
]


def apply_global_styles() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(59, 130, 246, 0.16), transparent 28%),
                radial-gradient(circle at top right, rgba(168, 85, 247, 0.14), transparent 26%),
                linear-gradient(180deg, #070B14 0%, #090D18 45%, #0B1020 100%);
            color: #F8FAFC;
            font-family: 'Inter', sans-serif;
        }

        .block-container {
            padding-top: 1.25rem;
            padding-bottom: 2rem;
            max-width: 1320px;
        }

        h1, h2, h3, h4 {
            color: #F8FAFC;
            letter-spacing: -0.03em;
        }

        p, li, span, label {
            color: #CBD5E1;
        }

        section[data-testid="stSidebar"] {
            background: rgba(7, 11, 20, 0.92);
            border-right: 1px solid rgba(148, 163, 184, 0.14);
        }

        div[data-testid="stMetricValue"] {
            color: #E2E8F0;
            font-size: 1.6rem;
        }

        div[data-testid="stMetricLabel"] {
            color: #94A3B8;
        }

        .paper-hero {
            position: relative;
            overflow: hidden;
            border: 1px solid rgba(148, 163, 184, 0.16);
            border-radius: 28px;
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.88), rgba(10, 15, 28, 0.88));
            box-shadow: 0 20px 70px rgba(0, 0, 0, 0.28);
        }

        .paper-hero:before {
            content: '';
            position: absolute;
            inset: 0;
            background:
                radial-gradient(circle at 20% 25%, rgba(59, 130, 246, 0.26), transparent 20%),
                radial-gradient(circle at 82% 18%, rgba(168, 85, 247, 0.24), transparent 18%),
                radial-gradient(circle at 72% 82%, rgba(16, 185, 129, 0.12), transparent 18%);
            pointer-events: none;
        }

        .paper-card {
            border: 1px solid rgba(148, 163, 184, 0.14);
            border-radius: 20px;
            background: rgba(15, 23, 42, 0.72);
            box-shadow: 0 16px 42px rgba(0, 0, 0, 0.22);
            backdrop-filter: blur(18px);
        }

        .paper-chip {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 0.8rem;
            border-radius: 999px;
            border: 1px solid rgba(96, 165, 250, 0.22);
            background: rgba(37, 99, 235, 0.12);
            color: #BFDBFE;
            font-size: 0.82rem;
            letter-spacing: 0.02em;
        }

        .paper-title {
            font-size: clamp(2.5rem, 5vw, 4.8rem);
            line-height: 0.97;
            font-weight: 700;
            margin: 0;
        }

        .paper-subtitle {
            max-width: 62ch;
            font-size: 1.05rem;
            line-height: 1.8;
            color: #CBD5E1;
        }

        .paper-feature h3 {
            margin-bottom: 0.35rem;
            font-size: 1.05rem;
        }

        .paper-feature p {
            margin: 0;
            font-size: 0.95rem;
            line-height: 1.65;
        }

        .paper-example {
            padding: 1rem 1rem 0.9rem;
            border-radius: 18px;
            border: 1px solid rgba(148, 163, 184, 0.14);
            background: rgba(15, 23, 42, 0.58);
        }

        .paper-example strong {
            color: #F8FAFC;
        }

        .paper-example span {
            display: block;
            margin-top: 0.35rem;
            color: #94A3B8;
            font-size: 0.9rem;
            line-height: 1.5;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    left, right = st.columns([1.25, 0.9], gap="large")

    with left:
        st.markdown(
            """
            <div class="paper-hero">
              <div style="position: relative; padding: 2.2rem 2.2rem 1.8rem;">
                <div class="paper-chip">Multimodal research intelligence</div>
                <div style="height: 1.1rem;"></div>
                <h1 class="paper-title">PaperMind AI</h1>
                <div style="height: 0.9rem;"></div>
                <div class="paper-subtitle">
                  An end-to-end multimodal research paper intelligence platform that reads,
                  extracts, and explains papers with citation-grounded answers.
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.write("")
        st.write("")
        c1, c2, c3 = st.columns(3)
        c1.metric("Fast ingest", "PDF → structure")
        c2.metric("Evidence-first", "Citations")
        c3.metric("Multimodal", "Tables + figures")

    with right:
        st.markdown(
            """
            <div class="paper-card" style="padding: 1.15rem 1.15rem 1rem; margin-bottom: 1rem;">
              <div class="paper-chip">Upload entry</div>
              <div style="height: 0.8rem;"></div>
              <div style="font-size: 1.35rem; font-weight: 650; color: #F8FAFC;">Start with a paper</div>
              <div style="height: 0.35rem;"></div>
              <div style="color: #94A3B8; line-height: 1.65;">
                Drop a PDF below to create a research workspace with extracted text, figures,
                tables, and citation-aware chat.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        uploaded_file = st.file_uploader("Choose a research paper", type=["pdf"], label_visibility="collapsed")
        if uploaded_file is not None:
            st.caption(f"Selected: {uploaded_file.name}")
            st.progress(15)
            if st.button("Process paper", type="primary", use_container_width=True):
                upload_document(API_URL, uploaded_file)

        st.caption("PDF upload is the first step. The workspace will appear after processing.")


def render_feature_strip() -> None:
    st.write("")
    st.markdown("### Why PaperMind AI")
    cols = st.columns(3, gap="large")
    for column, feature in zip(cols, FEATURE_CARDS, strict=True):
        with column:
            st.markdown(
                f"""
                <div class="paper-card paper-feature" style="padding: 1.15rem 1.15rem 1rem; height: 100%;">
                  <h3>{feature['title']}</h3>
                  <p>{feature['body']}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_examples() -> None:
    st.write("")
    st.markdown("### Example papers")
    cols = st.columns(3, gap="medium")
    for column, paper in zip(cols, EXAMPLE_PAPERS, strict=True):
        with column:
            st.markdown(
                f"""
                <div class="paper-example">
                  <strong>{paper['title']}</strong>
                  <span>{paper['subtitle']}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_home_status() -> None:
    st.write("")
    try:
        res = requests.get(f"{API_URL}/health", timeout=2)
        if res.status_code == 200:
            payload = res.json()
            st.success(f"Backend connected. LLM provider: {payload.get('llm_provider', 'Unknown')}")
        else:
            st.warning("Backend is returning an error state.")
    except requests.exceptions.RequestException:
        st.error("Backend status unavailable. Start the FastAPI server on port 8000.")

def main():
    apply_global_styles()
    render_sidebar(API_URL)

    st.write("")
    render_hero()
    render_feature_strip()
    render_examples()
    render_home_status()

if __name__ == "__main__":
    main()
