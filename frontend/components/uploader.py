import streamlit as st
from services.api import upload_pdf


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

        if st.button("Upload to Backend"):

            response = upload_pdf(uploaded_file)

            if hasattr(response, "status_code"):

                if response.status_code == 200:

                    data = response.json()
                    st.success(data["message"])

                else:

                    st.error(f"Upload Failed ({response.status_code})")

            else:

                st.error(f"Error: {response}")

    else:

        st.info("Supported format: PDF")