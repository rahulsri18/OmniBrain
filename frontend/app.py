

import streamlit as st
import os

st.set_page_config(
    page_title="OmniBrain",
    page_icon="🧠",
    layout="wide"
)

# Sidebar और Components इम्पोर्ट करें
from components.sidebar import render_sidebar
from components.header import render_header
from components.uploader import render_uploader
from components.document_table import render_document_table

# साइडबार रेंडर करें
render_sidebar()
# हेडर रेंडर करें
render_header()

# पेज राउटिंग लॉजिक
if st.session_state.get("current_page") == "Upload":
    # मुख्य पेज पर अपलोडर और टेबल को अगल-बगल (Columns) में दिखाएं ताकि यूआई धांसू लगे
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        render_uploader()
        
    with col2:
        render_document_table()

elif st.session_state.get("current_page") == "Chat":
    st.info("💬 Chat interface is under construction for the next milestone.")