import streamlit as st


def _go_to(page: str):
    st.session_state.current_page = page
    st.rerun()


def render_hero():
    """Top-of-page hero: eyebrow, headline, CTAs, and the signature pipeline visual."""
    left, right = st.columns([1.05, 1], gap="large")

    with left:
        st.markdown(
            """
            <div class="ob-hero-copy">
                <div class="ob-eyebrow"><span class="dot"></span> AGENTIC MULTI-MODAL RAG ORCHESTRATOR</div>
                <h1 class="ob-hero-title">Turn Your Documents Into<br>Intelligent Conversations</h1>
                <p class="ob-hero-sub">
                    OmniBrain reads your documents, retrieves the parts that matter, reasons
                    over them with a multi-agent pipeline, and understands charts and images
                    along the way — so you get grounded, contextual answers instead of a
                    search box.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        cta1, cta2 = st.columns(2)
        with cta1:
            if st.button("📤 Upload Documents", type="primary", use_container_width=True, key="hero_cta_upload"):
                _go_to("Upload")
        with cta2:
            if st.button("💬 Start Chat", use_container_width=True, key="hero_cta_chat"):
                _go_to("Chat")

    with right:
        st.markdown(
            """
            <div class="ob-hero-visual">
                <div class="ob-orb-wrap">
                    <div class="ob-orb-ring"></div>
                    <div class="ob-orb"></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="ob-status ob-glass" style="width:fit-content; margin-top:0.5rem;">
            <span class="ob-status-dot"></span> System Online — ready to ingest and answer
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_capabilities():
    st.markdown(
        """
        <div class="ob-section">
            <div class="ob-section-label">Capabilities</div>
            <div class="ob-section-title">What OmniBrain Can Do</div>
            <div class="ob-card-grid">
                <div class="ob-card">
                    <span class="ob-card-icon">📄</span>
                    <h4>Document Intelligence</h4>
                    <p>Parses and chunks PDFs — including text and tables — so nothing important is lost on ingestion.</p>
                </div>
                <div class="ob-card">
                    <span class="ob-card-icon">🔍</span>
                    <h4>Intelligent Retrieval</h4>
                    <p>Hybrid text + image search pulls back only the passages relevant to what you actually asked.</p>
                </div>
                <div class="ob-card">
                    <span class="ob-card-icon">🤖</span>
                    <h4>Agentic Reasoning</h4>
                    <p>A supervisor agent routes each query to the right tool — vector search, SQL, or vision.</p>
                </div>
                <div class="ob-card">
                    <span class="ob-card-icon">👁️</span>
                    <h4>Vision Understanding</h4>
                    <p>Reads charts, figures, and scanned tables inside your PDFs, not just the surrounding text.</p>
                </div>
                <div class="ob-card">
                    <span class="ob-card-icon">🛡️</span>
                    <h4>Prompt Safety</h4>
                    <p>Every question passes through input guardrails before it ever reaches the agent graph.</p>
                </div>
                <div class="ob-card">
                    <span class="ob-card-icon">📚</span>
                    <h4>Context Grounding</h4>
                    <p>Answers are checked against retrieved context before they're shown, to keep responses honest.</p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_workflow():
    st.markdown(
        """
        <div class="ob-section">
            <div class="ob-section-label">How It Works</div>
            <div class="ob-section-title">From Upload to Answer</div>
            <div class="ob-glass ob-pipeline">
                <div class="ob-pipeline-node"><div class="ob-node-icon">📤</div>Upload</div>
                <div class="ob-pipeline-line"></div>
                <div class="ob-pipeline-node"><div class="ob-node-icon">⚙️</div>Processing</div>
                <div class="ob-pipeline-line"></div>
                <div class="ob-pipeline-node"><div class="ob-node-icon">🔍</div>Retrieval</div>
                <div class="ob-pipeline-line"></div>
                <div class="ob-pipeline-node"><div class="ob-node-icon">🤖</div>Reasoning</div>
                <div class="ob-pipeline-line"></div>
                <div class="ob-pipeline-node"><div class="ob-node-icon">👁️</div>Vision</div>
                <div class="ob-pipeline-line"></div>
                <div class="ob-pipeline-node"><div class="ob-node-icon">✅</div>Answer</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_technology():
    st.markdown(
        """
        <div class="ob-section">
            <div class="ob-section-label">Under the Hood</div>
            <div class="ob-section-title">Built On</div>
            <div class="ob-card-grid">
                <div class="ob-card"><h4>🕸️ LangGraph</h4><p>State-machine orchestration for the multi-agent pipeline.</p></div>
                <div class="ob-card"><h4>📚 RAG</h4><p>Retrieval-augmented generation grounded in your own documents.</p></div>
                <div class="ob-card"><h4>🤝 Multi-Agent AI</h4><p>A supervisor node routes work across specialized sub-agents.</p></div>
                <div class="ob-card"><h4>👁️ Vision Models</h4><p>Reads charts and figures alongside plain text.</p></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_about():
    st.markdown(
        """
        <div class="ob-section">
            <div class="ob-glass" style="padding: 2rem 2.2rem;">
                <div class="ob-section-label">About</div>
                <div class="ob-section-title" style="margin-bottom:0.8rem;">What OmniBrain Solves</div>
                <p style="color:var(--ob-muted); line-height:1.7; max-width:70ch; margin:0;">
                    Long documents bury the answer you actually need under pages you don't.
                    OmniBrain ingests your PDFs — text, tables, and figures — and lets you ask
                    for what you want in plain language. A routing agent decides whether the
                    answer lives in retrieved text, a structured query, or an image, then
                    checks its own answer against the source material before showing it to you.
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer():
    st.markdown(
        """
        <div class="ob-footer">
            <div class="ob-footer-grid">
                <div class="ob-footer-brand">
                    <h3>🧠 OmniBrain</h3>
                    <p>Agentic Multi-Modal RAG Orchestrator</p>
                </div>
                <div class="ob-footer-col">
                    <h5>Navigation</h5>
                    <span>Home</span>
                    <span>Upload</span>
                    <span>Chat</span>
                    <span>Features</span>
                </div>
                <div class="ob-footer-col">
                    <h5>Technology</h5>
                    <span>RAG</span>
                    <span>LangGraph</span>
                    <span>Vision AI</span>
                    <span>Document Intelligence</span>
                </div>
            </div>
            <div class="ob-footer-bottom">
                <span>© 2026 OmniBrain</span>
                <span>Built with Python + Streamlit</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_landing():
    render_hero()
    render_capabilities()
    render_workflow()
    render_technology()
    render_about()
    render_footer()
