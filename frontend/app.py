# frontend/app.py
import os
import streamlit as st

# 🚀 नियम #1: st.set_page_config सबसे ऊपर होना ही चाहिए!
st.set_page_config(
    page_title="OmniBrain",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_css():
    """डायनेमिक पाथ हैंडलिंग ताकि कहीं से भी रन करने पर CSS लोड हो जाए"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    css_path = os.path.join(current_dir, "assets", "css", "style.css")
    
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(
                f"<style>{f.read()}</style>",
                unsafe_allow_html=True
            )

# CSS को पेज कॉन्फिगरेशन के बाद लोड करें
load_css()

# रिलेटिव इम्पोर्ट्स (ताकि पाथ का कोई लोचा न रहे)
from components.sidebar import render_sidebar
from components.header import render_header
from components.uploader import render_uploader

# Sidebar Render
render_sidebar()

# Main Page Render
render_header()

st.info(
    "👋 Welcome! Upload a PDF document to start chatting with OmniBrain."
)

render_uploader()