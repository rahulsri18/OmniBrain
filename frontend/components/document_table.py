

import streamlit as st

def render_document_table():
    st.subheader("📄 Uploaded Documents Status")

    if "uploaded_files" not in st.session_state or not st.session_state.uploaded_files:
        st.info("No documents uploaded in this session yet.")
        return

    st.dataframe(
        st.session_state.uploaded_files, 
        use_container_width=True,
        hide_index=True
    )