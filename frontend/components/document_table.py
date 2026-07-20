import streamlit as st


def render_document_table():

    st.subheader("📄 Uploaded Documents")

    documents = [
        {
            "File Name": "Annual_Report.pdf",
            "Status": "Processed"
        },
        {
            "File Name": "Research_Paper.pdf",
            "Status": "Processing"
        },
        {
            "File Name": "Invoice.pdf",
            "Status": "Pending"
        }
    ]

    st.table(documents)