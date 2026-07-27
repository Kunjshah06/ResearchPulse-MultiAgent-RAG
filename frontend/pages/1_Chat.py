# =============================================================================
# PaperMind AI — RAG Chat Interface
# =============================================================================

import streamlit as st
import requests

from components.sidebar import render_sidebar

API_URL = "http://localhost:8000/api/v1"

st.set_page_config(page_title="Chat - PaperMind AI", page_icon="💬", layout="wide")

# Re-apply custom CSS to ensure it persists across multi-page apps
st.markdown(
    """
    <style>
    .stApp { background-color: #0E1117; color: #FAFAFA; font-family: 'Inter', sans-serif; }
    h1, h2, h3 { color: #E2E8F0; font-weight: 600; }
    .block-container { padding-top: 2rem; }
    .stChatMessage { border-radius: 10px; padding: 15px; margin-bottom: 10px; }
    section[data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #30363D; }
    </style>
    """,
    unsafe_allow_html=True,
)

render_sidebar(API_URL)

st.title("💬 Multi-Agent RAG Chat")
st.markdown("Ask questions, generate summaries, or inquire about specific tables and figures.")

# Display chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Render citations if present in history
        if "citations" in message and message["citations"]:
            with st.expander("🔍 View Citations & Evidence"):
                for cite in message["citations"]:
                    st.markdown(f"**{cite['source_id']}** (Page {cite['page_number']}, {cite['chunk_type']})")
                    st.info(cite['snippet'] + "...")

# Accept user input
if prompt := st.chat_input("Ask a question about the document..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        if not st.session_state.doc_id:
            st.warning("⚠️ No document is currently active. Please upload a document first.")
            response_content = "Please upload a document to proceed."
            citations = []
        else:
            with st.spinner("Analyzing document and generating response..."):
                try:
                    payload = {
                        "query": prompt,
                        "filter_doc_ids": [st.session_state.doc_id]
                    }
                    response = requests.post(f"{API_URL}/query/", json=payload)
                    
                    if response.status_code == 200:
                        data = response.json()
                        response_content = data["answer"]
                        citations = data.get("citations", [])
                        
                        message_placeholder.markdown(response_content)
                        
                        if citations:
                            with st.expander("🔍 View Citations & Evidence"):
                                for cite in citations:
                                    st.markdown(f"**{cite['source_id']}** (Page {cite['page_number']}, {cite['chunk_type']})")
                                    st.info(cite['snippet'] + "...")
                                    
                        st.caption(f"Confidence: {data['confidence_score']:.2f} | Chunks Retrieved: {data['chunks_retrieved']}")
                        
                    else:
                        response_content = f"Error: Backend returned {response.status_code}"
                        message_placeholder.error(response_content)
                        citations = []
                except requests.exceptions.RequestException as e:
                    response_content = f"Failed to connect to backend API: {str(e)}"
                    message_placeholder.error(response_content)
                    citations = []
        
        # Add assistant response to chat history
        st.session_state.messages.append({
            "role": "assistant", 
            "content": response_content,
            "citations": citations
        })
