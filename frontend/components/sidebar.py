import streamlit as st


def render_sidebar():
    with st.sidebar:

        st.markdown("# 🧠 OmniBrain")
        st.caption("Agentic AI Assistant")

        st.divider()

        st.button("➕ New Chat", use_container_width=True)

        st.divider()

        st.markdown("### Navigation")

        st.button("🏠 Home", use_container_width=True)
        st.button("💬 Chat", use_container_width=True)
        st.button("📤 Upload", use_container_width=True)
        st.button("📚 Documents", use_container_width=True)
        st.button("🗄 SQL Assistant", use_container_width=True)
        st.button("⚙ Settings", use_container_width=True)

        st.divider()

        st.markdown("### Recent Chats")

        st.caption("📄 Annual Report")
        st.caption("🤖 Transformer Notes")
        st.caption("📊 Sales Dashboard")

        st.divider()

        st.caption("Version 1.0")