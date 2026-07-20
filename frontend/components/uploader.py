import streamlit as st


def render_uploader():

    st.subheader("📤 Upload Documents")

    st.write(
        "Upload PDF documents to begin analysis."
    )

    uploaded_file = st.file_uploader(
        "Choose PDF",
        type=["pdf"]
    )

    if uploaded_file:

        st.success(f"✅ {uploaded_file.name}")

    else:

        st.info(
            "Supported format: PDF"
        )