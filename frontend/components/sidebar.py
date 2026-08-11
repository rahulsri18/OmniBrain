
import streamlit as st

def render_sidebar():
    with st.sidebar:
        st.markdown("# 🧠 OmniBrain")
        st.caption("Agentic AI Assistant")
        st.divider()

        # नेविगेशन स्टेट सेट करना (ताकि बटन्स काम कर सकें)
        if "current_page" not in st.session_state:
            st.session_state.current_page = "Home"

        st.markdown("### Navigation")
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.current_page = "Home"
        if st.button("📤 Upload & Dashboard", use_container_width=True):
            st.session_state.current_page = "Upload"
        if st.button("💬 Chat Assistant", use_container_width=True):
            st.session_state.current_page = "Chat"

        st.divider()
        st.caption("Version 1.0.0 (v0.1.0)")
