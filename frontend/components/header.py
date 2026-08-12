import streamlit as st


def render_header():

    left, right = st.columns([8, 2])

    with left:
        st.title("🧠 OmniBrain")
        st.caption("Agentic Multi-Modal RAG Orchestrator")

    with right:
        st.markdown(
            """
            <div class="ob-status ob-glass" style="margin-top: 1.1rem;">
                <span class="ob-status-dot"></span> System Online
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
