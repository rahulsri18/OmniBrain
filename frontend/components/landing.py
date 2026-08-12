import streamlit as st
import textwrap


# ============================================================
# NAVIGATION
# ============================================================

def _go_to(page: str):
    st.session_state.current_page = page
    st.rerun()


# ============================================================
# HTML HELPER
# ============================================================

def _html(content: str):
    st.html(textwrap.dedent(content))


# ============================================================
# HERO
# ============================================================

def render_hero():
    """
    Premium Home hero section with:
    - Hero headline
    - Description
    - Upload / Chat CTAs
    - 3D orb visual
    - System status
    """

    left, right = st.columns(
        [1.08, 0.92],
        gap="large",
    )

    # --------------------------------------------------------
    # LEFT SIDE
    # --------------------------------------------------------

    with left:

        _html(
            """
            <div class="ob-hero-copy">

                <div class="ob-eyebrow">
                    <span class="dot"></span>
                    AGENTIC MULTI-MODAL RAG ORCHESTRATOR
                </div>

                <h1 class="ob-hero-title">
                    Turn Your Documents
                    <br>
                    Into Intelligent
                    <br>
                    Conversations
                </h1>

                <p class="ob-hero-sub">
                    OmniBrain reads your documents, retrieves the parts
                    that matter, reasons over them with a multi-agent
                    pipeline, and understands charts and images along
                    the way — so you get grounded, contextual answers
                    instead of a search box.
                </p>

            </div>
            """
        )

        # ----------------------------------------------------
        # CTA BUTTONS
        # ----------------------------------------------------

        cta1, cta2 = st.columns(
            [1, 1],
            gap="medium",
        )

        with cta1:

            if st.button(
                "📤 Upload Documents",
                type="primary",
                use_container_width=True,
                key="hero_cta_upload",
            ):
                _go_to("Upload")

        with cta2:

            if st.button(
                "💬 Start Chat",
                use_container_width=True,
                key="hero_cta_chat",
            ):
                _go_to("Chat")

        # ----------------------------------------------------
        # SYSTEM STATUS
        # ----------------------------------------------------

        _html(
            """
            <div
                class="ob-status ob-glass"
                style="
                    width:fit-content;
                    margin-top:1.1rem;
                "
            >

                <span class="ob-status-dot"></span>

                <span>
                    System Online — ready to ingest and answer
                </span>

            </div>
            """
        )

    # --------------------------------------------------------
    # RIGHT SIDE — 3D VISUAL
    # --------------------------------------------------------

    with right:

        _html(
            """
            <div class="ob-hero-visual">

                <div class="ob-orb-wrap">

                    <div class="ob-orb-ring"></div>

                    <div class="ob-orb"></div>

                </div>

            </div>
            """
        )


# ============================================================
# CAPABILITIES
# ============================================================

def render_capabilities():

    _html(
        """
        <section class="ob-section">

            <div class="ob-section-label">
                CAPABILITIES
            </div>

            <div class="ob-section-title">
                What OmniBrain Can Do
            </div>

            <div class="ob-card-grid">

                <div class="ob-card">

                    <span class="ob-card-icon">
                        📄
                    </span>

                    <h4>
                        Document Intelligence
                    </h4>

                    <p>
                        Parses and chunks PDFs — including text
                        and tables — so important information
                        is preserved during ingestion.
                    </p>

                </div>


                <div class="ob-card">

                    <span class="ob-card-icon">
                        🔍
                    </span>

                    <h4>
                        Intelligent Retrieval
                    </h4>

                    <p>
                        Hybrid text and image retrieval finds
                        only the passages and visual information
                        relevant to your question.
                    </p>

                </div>


                <div class="ob-card">

                    <span class="ob-card-icon">
                        🤖
                    </span>

                    <h4>
                        Agentic Reasoning
                    </h4>

                    <p>
                        A supervisor agent routes each query
                        to the appropriate capability — retrieval,
                        structured queries, or vision.
                    </p>

                </div>


                <div class="ob-card">

                    <span class="ob-card-icon">
                        👁️
                    </span>

                    <h4>
                        Vision Understanding
                    </h4>

                    <p>
                        Understands charts, figures and scanned
                        tables inside documents rather than
                        relying only on surrounding text.
                    </p>

                </div>


                <div class="ob-card">

                    <span class="ob-card-icon">
                        🛡️
                    </span>

                    <h4>
                        Prompt Safety
                    </h4>

                    <p>
                        Questions pass through input guardrails
                        before reaching the agent workflow.
                    </p>

                </div>


                <div class="ob-card">

                    <span class="ob-card-icon">
                        📚
                    </span>

                    <h4>
                        Context Grounding
                    </h4>

                    <p>
                        Responses are grounded against retrieved
                        context to reduce unsupported answers
                        and keep results traceable.
                    </p>

                </div>

            </div>

        </section>
        """
    )


# ============================================================
# WORKFLOW
# ============================================================

def render_workflow():

    _html(
        """
        <section class="ob-section">

            <div class="ob-section-label">
                HOW IT WORKS
            </div>

            <div class="ob-section-title">
                From Upload to Answer
            </div>

            <div class="ob-glass ob-pipeline">

                <div class="ob-pipeline-node">

                    <div class="ob-node-icon">
                        📤
                    </div>

                    <span>
                        Upload
                    </span>

                </div>


                <div class="ob-pipeline-line"></div>


                <div class="ob-pipeline-node">

                    <div class="ob-node-icon">
                        ⚙️
                    </div>

                    <span>
                        Processing
                    </span>

                </div>


                <div class="ob-pipeline-line"></div>


                <div class="ob-pipeline-node">

                    <div class="ob-node-icon">
                        🔍
                    </div>

                    <span>
                        Retrieval
                    </span>

                </div>


                <div class="ob-pipeline-line"></div>


                <div class="ob-pipeline-node">

                    <div class="ob-node-icon">
                        🤖
                    </div>

                    <span>
                        Reasoning
                    </span>

                </div>


                <div class="ob-pipeline-line"></div>


                <div class="ob-pipeline-node">

                    <div class="ob-node-icon">
                        👁️
                    </div>

                    <span>
                        Vision
                    </span>

                </div>


                <div class="ob-pipeline-line"></div>


                <div class="ob-pipeline-node">

                    <div class="ob-node-icon">
                        ✅
                    </div>

                    <span>
                        Answer
                    </span>

                </div>

            </div>

        </section>
        """
    )


# ============================================================
# TECHNOLOGY
# ============================================================

def render_technology():

    _html(
        """
        <section class="ob-section">

            <div class="ob-section-label">
                UNDER THE HOOD
            </div>

            <div class="ob-section-title">
                Built On
            </div>

            <div class="ob-card-grid">

                <div class="ob-card">

                    <h4>
                        🕸️ LangGraph
                    </h4>

                    <p>
                        State-machine orchestration for the
                        multi-agent processing pipeline.
                    </p>

                </div>


                <div class="ob-card">

                    <h4>
                        📚 RAG
                    </h4>

                    <p>
                        Retrieval-augmented generation grounded
                        in the user's own documents.
                    </p>

                </div>


                <div class="ob-card">

                    <h4>
                        🤝 Multi-Agent AI
                    </h4>

                    <p>
                        A supervisor coordinates specialized
                        agents according to the user's request.
                    </p>

                </div>


                <div class="ob-card">

                    <h4>
                        👁️ Vision Models
                    </h4>

                    <p>
                        Processes charts, figures and visual
                        document content alongside text.
                    </p>

                </div>

            </div>

        </section>
        """
    )


# ============================================================
# ABOUT
# ============================================================

def render_about():

    _html(
        """
        <section class="ob-section">

            <div
                class="ob-glass"
                style="
                    padding:2.5rem 2.6rem;
                    position:relative;
                    overflow:hidden;
                "
            >

                <div
                    style="
                        position:absolute;
                        top:-100px;
                        right:-100px;
                        width:260px;
                        height:260px;
                        border-radius:50%;
                        background:
                            radial-gradient(
                                circle,
                                rgba(139,92,246,0.18),
                                transparent 70%
                            );
                        pointer-events:none;
                    "
                ></div>


                <div class="ob-section-label">
                    ABOUT OMNIBRAIN
                </div>


                <div
                    class="ob-section-title"
                    style="margin-bottom:1rem;"
                >
                    What OmniBrain Solves
                </div>


                <p
                    style="
                        color:var(--ob-muted);
                        line-height:1.8;
                        max-width:75ch;
                        margin:0;
                        font-size:1.02rem;
                    "
                >
                    Long documents bury the answer you actually
                    need under pages you don't. OmniBrain ingests
                    your PDFs — text, tables and figures — and lets
                    you ask for what you need in plain language.
                    A routing agent determines whether the answer
                    belongs to retrieved text, structured data or
                    visual content, then grounds the response
                    against the available source material.
                </p>


                <div
                    style="
                        display:flex;
                        gap:0.7rem;
                        flex-wrap:wrap;
                        margin-top:1.5rem;
                    "
                >

                    <span class="ob-eyebrow">
                        <span class="dot"></span>
                        GROUNDED RESPONSES
                    </span>

                    <span class="ob-eyebrow">
                        <span class="dot"></span>
                        MULTI-MODAL
                    </span>

                    <span class="ob-eyebrow">
                        <span class="dot"></span>
                        AGENTIC
                    </span>

                </div>

            </div>

        </section>
        """
    )


# ============================================================
# FOOTER
# ============================================================

def render_footer():

    _html(
        """
        <footer class="ob-footer">

            <div class="ob-footer-grid">

                <div class="ob-footer-brand">

                    <h3>
                        🧠 OmniBrain
                    </h3>

                    <p>
                        Agentic Multi-Modal RAG Orchestrator
                    </p>

                </div>


                <div class="ob-footer-col">

                    <h5>
                        Navigation
                    </h5>

                    <span>
                        Home
                    </span>

                    <span>
                        Upload
                    </span>

                    <span>
                        Chat
                    </span>

                    <span>
                        Features
                    </span>

                </div>


                <div class="ob-footer-col">

                    <h5>
                        Technology
                    </h5>

                    <span>
                        RAG
                    </span>

                    <span>
                        LangGraph
                    </span>

                    <span>
                        Vision AI
                    </span>

                    <span>
                        Document Intelligence
                    </span>

                </div>

            </div>


            <div class="ob-footer-bottom">

                <span>
                    © 2026 OmniBrain
                </span>

                <span>
                    Built with Python + Streamlit
                </span>

            </div>

        </footer>
        """
    )


# ============================================================
# MAIN LANDING PAGE
# ============================================================

def render_landing():

    render_hero()

    render_capabilities()

    render_workflow()

    render_technology()

    render_about()

    render_footer()