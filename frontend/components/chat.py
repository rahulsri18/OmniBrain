import streamlit as st
import time


def apply_chat_styles():
    """Custom CSS for distinct chat bubbles."""
    st.markdown(
        """
        <style>
        div[data-testid="stChatMessage"]:has(div[aria-label="chat message avatar 🤖"]) {
            background-color: rgba(28, 131, 225, 0.05);
            border-radius: 10px;
            padding: 8px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


def render_chat():
    apply_chat_styles()

    st.title("💬 OmniBrain AI Assistant")
    st.caption("Ask questions about your uploaded documents.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display previous chat history
    for message in st.session_state.messages:

        avatar = "👤" if message["role"] == "user" else "🤖"

        with st.chat_message(message["role"], avatar=avatar):

            st.markdown(message["content"])

            # Show image if available
            if message["role"] == "assistant" and "image" in message:
                st.image(
                    message["image"],
                    caption="Image referenced by the Vision Agent",
                    width=500,
                )

            # Show reasoning if available
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
    prompt = st.chat_input("Ask OmniBrain anything...")

    if prompt:

        # User message
        st.session_state.messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        # Day 11 - Document grading status
        with st.chat_message("assistant", avatar="🤖"):

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

            st.markdown(response)

            # Day 10 - Vision image
            vision_image = "https://placehold.co/700x350/png?text=Vision+Agent+Output"

            st.image(
                vision_image,
                caption="Image referenced by the Vision Agent",
                width=500,
            )

            # Day 9 - Agent reasoning
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

        # Save assistant message
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": response,
                "image": vision_image,
                "reasoning": reasoning_steps,
            }
        )