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

    # Display previous messages with their saved reasoning
    for message in st.session_state.messages:
        avatar = "👤" if message["role"] == "user" else "🤖"

        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

            # Render Saved Reasoning in Expander if available
            if message["role"] == "assistant" and "reasoning" in message:
                with st.expander("🧠 Agent Reasoning Process"):
                    st.markdown("### Execution Steps")
                    for step in message["reasoning"]:
                        st.success(f"✅ {step}")

    # Chat input
    prompt = st.chat_input("Ask OmniBrain anything...")

    if prompt:
        # 1. User Message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        # 2. Assistant Response + Reasoning Mock Payload
        response_text = (
            "This is a placeholder response from OmniBrain.\n\n"
            "Backend integration with the LangGraph agent will be connected in the next milestone."
        )

        st.session_state.messages.append(
    {
        "role": "assistant",
        "content": response,
    }
)

        with st.chat_message("assistant", avatar="🤖"):

            st.markdown(response)

    # Placeholder image returned by the Vision Agent
            vision_image = "https://placehold.co/700x350/png?text=Vision+Agent+Output"

            st.image(
                vision_image,
                caption="Image referenced by the Vision Agent",
                width=500,
        )


        with st.expander("🧠 Agent Reasoning", expanded=False):

            reasoning_steps = [
            ("Question received", "✅"),
            ("Analyzing user query", "🔍"),
            ("Retrieved relevant document chunks", "📄"),
            ("Vision agent selected an image", "🖼️"),
            ("Generated final response", "🤖"),
        ]

        for step, icon in reasoning_steps:
            st.markdown(f"{icon} {step}")

        st.divider()

        st.caption(
            "This reasoning panel currently displays placeholder execution steps. "
            "Live LangGraph reasoning will be integrated in future milestones."
        )
        
        reasoning_steps = [
            "Question received & validated",
            "Supervisor Node: Query routed to Retriever Engine",
            "Qdrant Vector DB: Retrieved top matching contexts",
            "GPT-4o: Synthesized final response"
        ]

        # Append to session state WITH reasoning
        st.session_state.messages.append({
            "role": "assistant",
            "content": response_text,
            "reasoning": reasoning_steps
        })

        # Render immediately
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(response_text)

            with st.expander("🧠 Agent Reasoning Process"):
                st.markdown("### Execution Steps")
                for step in reasoning_steps:
                    st.success(f"✅ {step}")
                st.info("💡 Real-time backend SSE reasoning stream connection ready for Day 9 integration.")
