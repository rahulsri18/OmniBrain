import time
import streamlit as st


def apply_chat_styles():
    """Custom CSS for distinct chat bubbles."""
    st.markdown(
        """
        <style>
        div[data-testid="stChatMessage"]:has(div[aria-label="chat message avatar 🤖"]) {
            background-color: rgba(28, 131, 225, 0.05);
            border-radius: 10px;
            padding: 8px;
            box-shadow: 0 0 8px rgba(28,131,225,0.15);
            transition: all 0.2s ease-in-out;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_chat():
    apply_chat_styles()

    st.title("💬 OmniBrain AI Assistant")
    # Day 18 - Keyboard Accessibility
    st.markdown(
    """
    <div tabindex="0"
         role="region"
         aria-label="OmniBrain Chat Assistant"
         style="outline:none;">
    </div>
    """,
    unsafe_allow_html=True,
)
    st.caption("Ask questions about your uploaded documents.")
    # Day 17 - End User Guide
    with st.expander("📖 How to Use OmniBrain", expanded=False):

        st.markdown("""
### Welcome to OmniBrain

Follow these simple steps:

1. 📄 Upload your documents from **Upload & Dashboard**
2. 💬 Open **Chat Assistant**
3. ⌨️ Type your question in the chat box
4. 🤖 OmniBrain searches your documents
5. 📚 Review retrieved context and confidence score
6. 🧠 Expand **Agent Reasoning** to view execution steps

---

### Features

- ✅ Prompt Safety Validation
- 🔄 Query Rewriting
- 📚 Retrieved Context
- 🖼️ Vision Agent Support
- 🧠 Agent Reasoning
- ⚡ Streaming Responses
- 📜 Chat History Pagination

---

### Tip

Use clear, specific questions for the best results.
""")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Day 16 - Chat History Pagination
    PAGE_SIZE = 5

    if "chat_page" not in st.session_state:
        st.session_state.chat_page = 1

    total_messages = len(st.session_state.messages)
    start_index = max(0, total_messages - (PAGE_SIZE * st.session_state.chat_page))
    visible_messages = st.session_state.messages[start_index:]

    # Show pagination control if total messages exceed page threshold
    if start_index > 0:
        if st.button("⬆️ Load Older Messages", key="load_older"):
            st.session_state.chat_page += 1
            st.rerun()

    # Display paginated messages
    for message in visible_messages:

    
        avatar = "👤" if message["role"] == "user" else "🤖"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

            if message["role"] == "assistant" and "image" in message:
                st.image(
                    message["image"],
                    caption="Image referenced by the Vision Agent",
                    width=500,
                )

            if message["role"] == "assistant" and "reasoning" in message:
                with st.expander("🧠 Agent Reasoning", expanded=False):
                    for step, icon in message["reasoning"]:
                        st.markdown(f"{icon} {step}")
                    st.divider()
                    st.caption(
                        "This reasoning panel currently displays placeholder execution steps. "
                        "Live LangGraph reasoning will be integrated in future milestones."
                    )

    # Chat input
    prompt = st.chat_input(
    "Ask OmniBrain anything...",
    key="chat_input",
)

    if prompt:
        # FIX: Reset pagination back to page 1 on new user input
        st.session_state.chat_page = 1

        # User message
        st.session_state.messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        # Assistant processing & streaming pipeline
        with st.chat_message("assistant", avatar="🤖"):
            guardrail_status = st.status(
                "🛡️ Checking user prompt against safety policies...",
                expanded=False,
            )
            time.sleep(1)
            guardrail_status.update(
                label="✅ Prompt passed safety validation",
                state="complete",
            )

            st.info("🔄 Retrying search with optimized query...")
            st.code(
                "Compare annual revenue trends from the uploaded financial report.",
                language="text",
            )

            status = st.status(
                "🟡 Grading retrieved documents...",
                expanded=False,
            )
            with st.spinner("Analyzing retrieved context..."):
                time.sleep(2)

            status.update(
                label="✅ Document grading completed",
                state="complete",
            )

            response = (
                "This is a placeholder response from OmniBrain.\n\n"
                "Backend integration with the LangGraph agent will be connected in the next milestone."
            )

            placeholder = st.empty()
            streamed_text = ""
            for word in response.split():
                streamed_text += word + " "
                placeholder.markdown(streamed_text)
                time.sleep(0.05)

            with st.container():
                st.caption("📚 Retrieved Context")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(label="Documents Retrieved", value="4")
                with col2:
                    st.metric(label="Confidence", value="92%")
                st.caption("Source: Annual_Report_2025.pdf • Pages 12–18 (Placeholder)")

            vision_image = "https://placehold.co/700x350/png?text=Vision+Agent+Output"
            st.image(
                vision_image,
                caption="Image referenced by the Vision Agent",
                width=500,
            )
            st.caption("🖼️ Accessible image preview for Vision Agent output.")
            reasoning_steps = [
                ("Question received", "✅"),
                ("Analyzing user query", "🔍"),
                ("Retrieved relevant document chunks", "📄"),
                ("Vision agent selected an image", "🖼️"),
                ("Generated final response", "🤖"),
            ]

            with st.expander("🧠 Agent Reasoning", expanded=False):
                for step, icon in reasoning_steps:
                    st.markdown(f"{icon} {step}")
                st.divider()
                st.caption(
                    "This reasoning panel currently displays placeholder execution steps. "
                    "Live LangGraph reasoning will be integrated in future milestones."
                )

        # Save assistant message to session state
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": response,
                "image": vision_image,
                "reasoning": reasoning_steps,
            }
        )