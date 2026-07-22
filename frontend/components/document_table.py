

import streamlit as st

def render_document_table():
    st.subheader("📄 Uploaded Documents Status")

    # 🚀 फिक्स: हार्डकोडेड डेटा की जगह Session State से डायनेमिक डेटा उठाना
    if "uploaded_files" not in st.session_state or not st.session_state.uploaded_files:
        st.info("No documents uploaded in this session yet.")
        return

    # डेटा को टेबल फॉर्मेट में दिखाना
    st.dataframe(
        st.session_state.uploaded_files, 
        use_container_width=True,
        hide_index=True
    )