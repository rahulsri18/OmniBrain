import time
import streamlit as st
import textwrap


def scroll_chat_to_top():
    st.markdown(
        """
        <script>
        window.parent.scrollTo({
            top: 0,
            behavior: "instant"
        });
        </script>
        """,
        unsafe_allow_html=True,
    )


def _html(content):
    """Render custom HTML safely."""
    st.html(textwrap.dedent(content))


def render_chat():

    # =========================================================
    # INITIAL STATE
    # =========================================================

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "chat_page" not in st.session_state:
        st.session_state.chat_page = 1

    PAGE_SIZE = 5

    # =========================================================
    # CHAT HEADER
    # =========================================================

    _html(
        """
        <div class="ob-chat-header">

            <div class="ob-chat-header-left">

                <div class="ob-chat-avatar">
                    🧠
                </div>

                <div>

                    <div class="ob-eyebrow">
                        <span class="dot"></span>
                        AI ASSISTANT
                    </div>

                    <h1 class="ob-chat-title">
                        OmniBrain <span>Chat</span>
                    </h1>

                    <p class="ob-chat-subtitle">
                        Ask questions about your uploaded documents
                        and get grounded, contextual answers.
                    </p>

                </div>

            </div>

            <div class="ob-chat-online">
                <span class="ob-status-dot"></span>
                Online
            </div>

        </div>
        """
    )

    # =========================================================
    # EMPTY CHAT / WELCOME
    # =========================================================

    if not st.session_state.messages:

        _html(
            """
            <div class="ob-chat-welcome">

                <div class="ob-chat-welcome-icon">
                    ✨
                </div>

                <h2>
                    Ask OmniBrain anything
                </h2>

                <p>
                    Your documents are the knowledge source.
                    Ask specific questions and OmniBrain will retrieve
                    relevant context before generating an answer.
                </p>

            </div>
            """
        )

        _html(
            """
            <div class="ob-suggestion-label">
                TRY ASKING
            </div>
            """
        )

        suggestion_col1, suggestion_col2, suggestion_col3 = st.columns(3)

        with suggestion_col1:

            suggestion_1 = st.button(
                "📄 Summarize my document",
                use_container_width=True,
                key="suggestion_summary",
            )

        with suggestion_col2:

            suggestion_2 = st.button(
                "🔍 Find the key points",
                use_container_width=True,
                key="suggestion_keypoints",
            )

        with suggestion_col3:

            suggestion_3 = st.button(
                "📊 Analyze the data",
                use_container_width=True,
                key="suggestion_data",
            )

        if suggestion_1:

            st.session_state.pending_prompt = (
                "Summarize my uploaded document."
            )

        elif suggestion_2:

            st.session_state.pending_prompt = (
                "What are the key points in my uploaded document?"
            )

        elif suggestion_3:

            st.session_state.pending_prompt = (
                "Analyze the important data from my uploaded document."
            )

    # =========================================================
    # CHAT HISTORY PAGINATION
    # =========================================================

    total_messages = len(
        st.session_state.messages
    )

    start_index = max(
        0,
        total_messages - (
            PAGE_SIZE * st.session_state.chat_page
        ),
    )

    visible_messages = (
        st.session_state.messages[start_index:]
    )

    if start_index > 0:

        if st.button(
            "⬆️ Load Older Messages",
            key="load_older",
        ):

            st.session_state.chat_page += 1
            st.rerun()

    # =========================================================
    # DISPLAY EXISTING MESSAGES
    # =========================================================

    for message in visible_messages:

        role = message["role"]

        if role == "user":

            with st.chat_message(
                "user",
                avatar="👤",
            ):

                st.markdown(
                    message["content"]
                )

        else:

            with st.chat_message(
                "assistant",
                avatar="🤖",
            ):

                st.markdown(
                    message["content"]
                )

                # ---------------------------------------------
                # Retrieved Context
                # ---------------------------------------------

                if "context" in message:

                    _html(
                        """
                        <div class="ob-chat-section-label">
                            📚 RETRIEVED CONTEXT
                        </div>
                        """
                    )

                    context_col1, context_col2 = st.columns(2)

                    with context_col1:

                        st.metric(
                            label="Documents Retrieved",
                            value=message.get(
                                "documents",
                                "4",
                            ),
                        )

                    with context_col2:

                        st.metric(
                            label="Confidence",
                            value=message.get(
                                "confidence",
                                "92%",
                            ),
                        )

                    st.caption(
                        message.get(
                            "context",
                            "Source information unavailable.",
                        )
                    )

                # ---------------------------------------------
                # Vision Output
                # ---------------------------------------------

                if "image" in message:

                    _html(
                        """
                        <div class="ob-chat-section-label">
                            🖼️ VISION AGENT OUTPUT
                        </div>
                        """
                    )

                    st.image(
                        message["image"],
                        caption=(
                            "Image referenced by "
                            "the Vision Agent"
                        ),
                        width=500,
                    )

                # ---------------------------------------------
                # Agent Reasoning
                # ---------------------------------------------

                if "reasoning" in message:

                    with st.expander(
                        "🧠 Agent Reasoning",
                        expanded=False,
                    ):

                        for step, icon in message["reasoning"]:

                            st.markdown(
                                f"{icon} {step}"
                            )

                        st.divider()

                        st.caption(
                            "Execution steps shown here are "
                            "currently representative placeholders. "
                            "Live LangGraph reasoning will be "
                            "connected during backend integration."
                        )

    # =========================================================
    # PENDING SUGGESTION
    # =========================================================

    pending_prompt = st.session_state.pop(
        "pending_prompt",
        None,
    )

    prompt = st.chat_input(
        "Ask OmniBrain anything...",
        key="chat_input",
    )

    if pending_prompt:
        prompt = pending_prompt

    # =========================================================
    # PROCESS NEW QUESTION
    # =========================================================

    if prompt:

        st.session_state.chat_page = 1

        # -----------------------------------------------------
        # Save user message
        # -----------------------------------------------------

        st.session_state.messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        with st.chat_message(
            "user",
            avatar="👤",
        ):

            st.markdown(prompt)

        # =====================================================
        # ASSISTANT RESPONSE
        # =====================================================

        with st.chat_message(
            "assistant",
            avatar="🤖",
        ):

            # -------------------------------------------------
            # Prompt safety
            # -------------------------------------------------

            guardrail_status = st.status(
                "🛡️ Checking prompt safety...",
                expanded=False,
            )

            time.sleep(0.5)

            guardrail_status.update(
                label="✅ Prompt passed safety validation",
                state="complete",
            )

            # -------------------------------------------------
            # Query optimization
            # -------------------------------------------------

            _html(
                """
                <div class="ob-processing-card">

                    <div class="ob-processing-icon">
                        🔄
                    </div>

                    <div>

                        <strong>
                            Optimizing your query
                        </strong>

                        <div>
                            Rewriting the question for better retrieval
                        </div>

                    </div>

                </div>
                """
            )

            time.sleep(0.4)

            # -------------------------------------------------
            # Document retrieval
            # -------------------------------------------------

            document_status = st.status(
                "📚 Searching and grading retrieved documents...",
                expanded=False,
            )

            with st.spinner(
                "Analyzing retrieved context..."
            ):

                time.sleep(1)

            document_status.update(
                label="✅ Relevant context identified",
                state="complete",
            )

            # =================================================
            # PLACEHOLDER RESPONSE
            # =================================================

            response = (
                "This is a placeholder response from OmniBrain.\n\n"
                "The frontend chat experience is ready. "
                "Backend integration with the LangGraph agent "
                "will provide the real grounded response."
            )

            # -------------------------------------------------
            # Streaming
            # -------------------------------------------------

            placeholder = st.empty()

            streamed_text = ""

            for word in response.split():

                streamed_text += word + " "

                placeholder.markdown(
                    streamed_text
                )

                time.sleep(0.035)

            # =================================================
            # RETRIEVED CONTEXT
            # =================================================

            _html(
                """
                <div class="ob-chat-section-label">
                    📚 RETRIEVED CONTEXT
                </div>
                """
            )

            context_col1, context_col2 = st.columns(2)

            with context_col1:

                st.metric(
                    label="Documents Retrieved",
                    value="4",
                )

            with context_col2:

                st.metric(
                    label="Confidence",
                    value="92%",
                )

            st.caption(
                "Source: Annual_Report_2025.pdf • "
                "Pages 12–18 • Placeholder"
            )

            # =================================================
            # VISION AGENT
            # =================================================

            _html(
                """
                <div class="ob-chat-section-label">
                    🖼️ VISION AGENT
                </div>
                """
            )

            _html(
    """
                <div class="ob-vision-placeholder">

                    <div class="ob-vision-placeholder-icon">
                        👁️
                </div>

                <h3>Vision Agent Output</h3>

                <p>
                    Charts, figures, scanned tables and images
                    extracted from your documents will appear here.
                </p>

                <div class="ob-vision-status">
                    <span class="ob-status-dot"></span>
                    Vision processing ready
                </div>

            </div>
    """
)

            # =================================================
            # AGENT REASONING
            # =================================================

            reasoning_steps = [
                ("Question received", "✅"),
                ("Analyzing user query", "🔍"),
                (
                    "Retrieved relevant document chunks",
                    "📄",
                ),
                (
                    "Vision agent selected an image",
                    "🖼️",
                ),
                (
                    "Generated final response",
                    "🤖",
                ),
            ]

            with st.expander(
                "🧠 Agent Reasoning",
                expanded=False,
            ):

                for step, icon in reasoning_steps:

                    st.markdown(
                        f"{icon} {step}"
                    )

                st.divider()

                st.caption(
                    "Execution steps currently represent "
                    "the frontend demonstration flow. "
                    "Live LangGraph reasoning will be "
                    "connected during backend integration."
                )

        # =====================================================
        # SAVE ASSISTANT MESSAGE
        # =====================================================

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": response,
                "context": (
                    "Annual_Report_2025.pdf • "
                    "Pages 12–18 (Placeholder)"
                ),
                "documents": "4",
                "confidence": "92%",
                
                "reasoning": reasoning_steps,
            }
        )