import streamlit as st


def render_header():

    left, right = st.columns([8, 2])

    with left:
        st.title("🧠 OmniBrain")
        st.caption("Agentic Multi-Modal RAG Orchestrator")

    with right:
        st.success("🟢 System Online")

    st.markdown("<br>", unsafe_allow_html=True)