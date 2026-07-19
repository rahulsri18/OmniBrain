import streamlit as st

st.set_page_config(
    page_title="OmniBrain",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🧠 OmniBrain")
st.subheader("Agentic Multi-Modal RAG Orchestrator")

st.markdown("---")

st.write("Welcome to OmniBrain!")

st.info(
    "Day 1: Streamlit environment has been successfully configured."
)