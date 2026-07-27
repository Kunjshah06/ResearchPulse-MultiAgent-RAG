# =============================================================================
# PaperMind AI — Sidebar Component
# =============================================================================

import streamlit as st
import requests


def _reset_document_state() -> None:
    st.session_state.doc_id = None
    st.session_state.doc_summary = None
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Welcome to PaperMind AI! Please upload a document to begin.",
        }
    ]


def upload_document(api_url: str, uploaded_file) -> None:
    """Upload a PDF and hydrate the active document state."""
    if uploaded_file is None:
        return

    with st.spinner("Ingesting, parsing layout, and generating embeddings..."):
        try:
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
            response = requests.post(f"{api_url}/documents/upload", files=files, timeout=90)

            if response.status_code == 200:
                data = response.json()
                st.session_state.doc_id = data["id"]
                st.session_state.doc_summary = data

                st.session_state.messages = [
                    {
                        "role": "assistant",
                        "content": (
                            f"Successfully processed **{data['filename']}**! "
                            "What would you like to know about it?"
                        ),
                    }
                ]
                st.success("Document processed successfully!")
                st.rerun()
            else:
                detail = response.json().get("detail", response.text)
                st.error(f"Error: {detail}")
        except requests.exceptions.RequestException as exc:
            st.error(f"Failed to connect to backend: {exc}")

def render_sidebar(api_url: str):
    """Renders the sidebar with document upload functionality."""
    with st.sidebar:
        st.markdown("### PaperMind AI")
        st.caption("Research workspace")

        uploaded_file = st.file_uploader("Upload research paper (PDF)", type=["pdf"])

        if uploaded_file is not None:
            st.caption(f"Ready to process {uploaded_file.name}")
            if st.button("Process document", type="primary", use_container_width=True):
                upload_document(api_url, uploaded_file)

        st.divider()

        if st.session_state.doc_summary:
            doc = st.session_state.doc_summary
            st.markdown("### Active paper")
            st.markdown(f"**{doc['filename']}**")
            
            col1, col2 = st.columns(2)
            col1.metric("Pages", doc["page_count"])
            col2.metric("Elements", doc["element_count"])
            
            col3, col4 = st.columns(2)
            col3.metric("Chunks", doc["chunk_count"])
            col4.metric("Tables", doc["table_count"])
            
            if st.button("Clear Document", use_container_width=True):
                _reset_document_state()
                st.rerun()
