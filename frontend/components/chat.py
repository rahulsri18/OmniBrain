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