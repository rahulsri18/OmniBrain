

import streamlit as st
from services.api import upload_pdf

def render_uploader():
    st.subheader("📤 Upload Documents")
    st.write("Upload PDF documents to begin analysis.")

    # 🚀 फिक्स: फ़ाइल अपलोडर विजेट को वापस जोड़ा
    uploaded_file = st.file_uploader("Choose PDF", type=["pdf"])

    if uploaded_file:
        st.success(f"✅ {uploaded_file.name} ready to upload.")

        if st.button("Upload to Backend", use_container_width=True):
            # 🚀 फिक्स: नकली लूप की जगह असली Spinner का इस्तेमाल
            with st.spinner("Uploading and starting ingestion pipeline..."):
                response = upload_pdf(uploaded_file)

            if response and hasattr(response, "status_code"):
                # बैकएंड 202 Accepted रिटर्न करता है बैकग्राउंड टास्क के लिए
                if response.status_code in [200, 202]:
                    try:
                        data = response.json()
                        st.success(f"🎉 {data.get('message', 'Upload successful!')}")
                        
                        # 🚀 स्टेट अपडेट करें ताकि टेबल में नई फाइल दिख सके
                        if "uploaded_files" not in st.session_state:
                            st.session_state.uploaded_files = []
                        st.session_state.uploaded_files.append({
                            "File Name": uploaded_file.name,
                            "Status": "Processing (Background)"
                        })
                        st.rerun()
                    except Exception:
                        st.success("🎉 File uploaded successfully!")
                elif response.status_code == 413:
                    st.error("❌ Upload Failed: File size exceeds the 50MB limit.")
                else:
                    st.error(f"❌ Upload Failed (Status Code: {response.status_code})")
            else:
                st.error(f"❌ Connection Error: Backend server is offline. {response}")
    else:
        st.info("Supported format: PDF (Max 50MB)")