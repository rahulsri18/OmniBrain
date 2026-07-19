import streamlit as st
def load_css():
    with open("frontend/assets/css/style.css") as f:
        st.markdown(
            f"<style>{f.read()}</style>",
            unsafe_allow_html=True
        )

from components.sidebar import render_sidebar
from components.header import render_header
from components.uploader import render_uploader

st.set_page_config(
    load_css()
    page_title="OmniBrain",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar
render_sidebar()

# Main Page
render_header()
st.info(
    "👋 Welcome! Upload a PDF document to start chatting with OmniBrain."
)

render_uploader()