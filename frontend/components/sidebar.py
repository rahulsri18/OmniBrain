import streamlit as st


def render_sidebar():
    with st.sidebar:

        # -----------------------------
        # Brand
        # -----------------------------
        st.markdown(
            """
            <div class="ob-sidebar-brand">
                <div class="ob-brand-icon">🧠</div>
                <div>
                    <div class="ob-brand-name">OmniBrain</div>
                    <div class="ob-brand-subtitle">Agentic AI Assistant</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="ob-sidebar-status">
                <span class="ob-status-dot"></span>
                System Online
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")

        # -----------------------------
        # Navigation state
        # -----------------------------
        if "current_page" not in st.session_state:
            st.session_state.current_page = "Home"

        current_page = st.session_state.current_page

        st.markdown(
            '<div class="ob-sidebar-heading">NAVIGATION</div>',
            unsafe_allow_html=True,
        )

        # -----------------------------
        # Navigation buttons
        # -----------------------------
        if st.button(
            "🏠  Home",
            use_container_width=True,
            key="nav_home",
        ):
            st.session_state.current_page = "Home"
            st.rerun()

        if st.button(
            "📤  Upload & Dashboard",
            use_container_width=True,
            key="nav_upload",
        ):
            st.session_state.current_page = "Upload"
            st.rerun()

        if st.button(
            "💬  Chat Assistant",
            use_container_width=True,
            key="nav_chat",
        ):
            st.session_state.current_page = "Chat"
            st.rerun()

        # -----------------------------
        # Sidebar divider
        # -----------------------------
        st.markdown("---")

        # -----------------------------
        # Product information
        # -----------------------------
        st.markdown(
            """
            <div class="ob-sidebar-info">
                <div class="ob-sidebar-info-label">OMNIBRAIN</div>
                <div class="ob-sidebar-info-text">
                    Multi-Modal RAG Orchestrator
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="ob-sidebar-footer">
                <span>v1.0.0</span>
                <span>•</span>
                <span>2026</span>
            </div>
            """,
            unsafe_allow_html=True,
        )