
import streamlit as st
import os

st.set_page_config(
    page_title="OmniBrain",
    page_icon="🧠",
    layout="wide"
)

# --- Load premium theme (fonts + glassmorphism/animation stylesheet) ---
def load_css():
    css_path = os.path.join(os.path.dirname(__file__), "assets", "css", "style.css")
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- Custom theme temporarily OFF (functionality first, styling later) ---
# load_css()

# Sidebar और Components इम्पोर्ट करें
from components.sidebar import render_sidebar
from components.header import render_header
from components.uploader import render_uploader
from components.document_table import render_document_table
from components.chat import render_chat
from components.landing import render_landing, render_footer

# साइडबार रेंडर करें
render_sidebar()

# डिफ़ॉल्ट पेज: Home (नया लैंडिंग एक्सपीरियंस)
if "current_page" not in st.session_state:
    st.session_state.current_page = "Home"

# पेज राउटिंग लॉजिक
if st.session_state.get("current_page") == "Home":
    # लैंडिंग पेज खुद अपना हीरो/स्टेटस रेंडर करता है, अलग हेडर की जरूरत नहीं
    render_landing()

elif st.session_state.get("current_page") == "Upload":
    render_header()
    # मुख्य पेज पर अपलोडर और टेबल को अगल-बगल (Columns) में दिखाएं ताकि यूआई धांसू लगे
    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        render_uploader()

    with col2:
        render_document_table()

    render_footer()

elif st.session_state.get("current_page") == "Chat":
    render_header()
    render_chat()
    render_footer()
