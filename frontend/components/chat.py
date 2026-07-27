import streamlit as st


def render_chat():

    st.title("💬 OmniBrain AI Assistant")
    st.caption("Ask questions about your uploaded documents.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display previous messages
    for message in st.session_state.messages:

        avatar = "👤" if message["role"] == "user" else "🤖"

        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

    # Chat input
    prompt = st.chat_input("Ask OmniBrain anything...")

    if prompt:

        st.session_state.messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        response = (
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