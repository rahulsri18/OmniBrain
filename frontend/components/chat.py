import streamlit as st
import time


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

    # Store user message
     st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

     with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # Placeholder assistant response
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

        st.markdown(response)