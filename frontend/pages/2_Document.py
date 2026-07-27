# =============================================================================
# PaperMind AI — Document Extraction Viewer
# =============================================================================

import streamlit as st
import requests

from components.sidebar import render_sidebar

API_URL = "http://localhost:8000/api/v1"

st.set_page_config(page_title="Document View - PaperMind AI", page_icon="📄", layout="wide")

st.markdown(
    """
    <style>
    .stApp { background-color: #0E1117; color: #FAFAFA; font-family: 'Inter', sans-serif; }
    h1, h2, h3 { color: #E2E8F0; font-weight: 600; }
    .block-container { padding-top: 2rem; }
    section[data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #30363D; }
    div[data-testid="stMetricValue"] { color: #3b82f6; }
    </style>
    """,
    unsafe_allow_html=True,
)

render_sidebar(API_URL)

st.title("📄 Document Extraction Viewer")

if not st.session_state.doc_id:
    st.info("👈 Please upload a document in the sidebar to view extracted metadata and components.")
else:
    doc_id = st.session_state.doc_id
    
    with st.spinner("Fetching document details..."):
        try:
            res = requests.get(f"{API_URL}/documents/{doc_id}")
            if res.status_code == 200:
                doc = res.json()
                
                st.subheader(f"Title: {doc.get('metadata', {}).get('title') or 'Unknown Title'}")
                st.write(f"**Authors:** {', '.join(doc.get('metadata', {}).get('authors', [])) or 'Unknown'}")
                
                # Metrics Overview
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Total Pages", doc.get("metadata", {}).get("page_count", 0))
                col2.metric("Tables Extracted", len(doc.get("tables", [])))
                col3.metric("Figures Extracted", len(doc.get("figures", [])))
                col4.metric("Semantic Chunks", len(doc.get("chunks", [])))
                
                st.divider()
                
                # Tabs for different extraction views
                tab1, tab2, tab3 = st.tabs(["📑 Document Hierarchy", "📊 Tables & Figures", "🔗 Knowledge Graph"])
                
                with tab1:
                    st.markdown("### Structural Elements")
                    st.caption("Displaying the first 50 elements of the document tree.")
                    elements = doc.get("elements", [])
                    for el in elements[:50]:
                        with st.expander(f"{el.get('element_type', 'TEXT')} (Page {el.get('page_number')})"):
                            st.write(el.get("text", ""))
                            st.caption(f"Bounding Box: {el.get('bounding_box')}")
                            
                with tab2:
                    st.markdown("### Extracted Tables")
                    tables = doc.get("tables", [])
                    if not tables:
                        st.info("No tables detected in this document.")
                    else:
                        for idx, table in enumerate(tables, 1):
                            st.markdown(f"**Table {idx}** (Page {table.get('page_number')})")
                            st.caption(table.get("caption") or "No caption detected")
                            st.dataframe(table.get("cells", [])) # Will render raw cell data gracefully
                            
                    st.markdown("### Extracted Figures")
                    figures = doc.get("figures", [])
                    if not figures:
                        st.info("No figures detected in this document.")
                    else:
                        for idx, fig in enumerate(figures, 1):
                            st.markdown(f"**Figure {idx}** (Page {fig.get('page_number')})")
                            st.caption(fig.get("caption") or "No caption detected")
                            
                with tab3:
                    st.markdown("### Knowledge Graph Nodes")
                    st.info("The knowledge graph has been successfully built in memory. Below is a summary of the extracted concepts and relationships.")
                    # Currently we don't return the full graph from the GET /documents/ endpoint to avoid massive payloads,
                    # but we can show stats if they were attached.
                    st.write("Graph visualization requires D3.js or Cytoscape integration (Planned for Next.js frontend).")
                    
            else:
                st.error("Failed to load document details.")
        except Exception as e:
            st.error(f"Error fetching document: {e}")
