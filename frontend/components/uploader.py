import streamlit as st
import textwrap

from services.api import upload_pdf


def _html(content):
    """Render custom HTML safely."""
    st.html(textwrap.dedent(content))


def render_uploader():

    # =========================================================
    # PAGE HEADER
    # =========================================================

    _html(
        """
        <div class="ob-page-header">

            <div class="ob-eyebrow">
                <span class="dot"></span>
                DOCUMENT WORKSPACE
            </div>

            <h1 class="ob-page-title">
                Upload & <span>Analyze</span>
            </h1>

            <p class="ob-page-subtitle">
                Upload your documents and let OmniBrain process text, tables,
                figures and images through its intelligent ingestion pipeline.
            </p>

        </div>
        """
    )

    # =========================================================
    # UPLOAD ZONE
    # =========================================================

    _html(
        """
        <div class="ob-upload-card">

            <div class="ob-upload-icon">
                📄
            </div>

            <h2>
                Drop your document here
            </h2>

            <p>
                Upload a PDF and OmniBrain will automatically prepare it
                for retrieval and agentic reasoning.
            </p>

            <div class="ob-upload-meta">
                <span>PDF</span>
                <span>•</span>
                <span>Maximum 50 MB</span>
                <span>•</span>
                <span>Secure processing</span>
            </div>

        </div>
        """
    )

    # =========================================================
    # FILE UPLOADER
    # =========================================================

    uploaded_file = st.file_uploader(
        "Choose a PDF document",
        type=["pdf"],
        label_visibility="collapsed",
    )

    # =========================================================
    # SELECTED FILE
    # =========================================================

    if uploaded_file:

        file_size_mb = uploaded_file.size / (1024 * 1024)

        _html(
            f"""
            <div class="ob-file-preview">

                <div class="ob-file-icon">
                    📄
                </div>

                <div class="ob-file-info">

                    <div class="ob-file-name">
                        {uploaded_file.name}
                    </div>

                    <div class="ob-file-size">
                        {file_size_mb:.2f} MB
                    </div>

                </div>

                <div class="ob-file-status">
                    READY
                </div>

            </div>
            """
        )

        # =====================================================
        # PROCESS BUTTON
        # =====================================================

        if st.button(
            "🚀 Start Document Processing",
            type="primary",
            use_container_width=True,
            key="upload_backend_button",
        ):

            with st.spinner(
                "Uploading document and starting ingestion pipeline..."
            ):

                response = upload_pdf(uploaded_file)

            # =================================================
            # SUCCESS
            # =================================================

            if response and hasattr(response, "status_code"):

                if response.status_code in [200, 202]:

                    try:

                        data = response.json()

                        if "uploaded_files" not in st.session_state:
                            st.session_state.uploaded_files = []

                        st.session_state.uploaded_files.append(
                            {
                                "File Name": uploaded_file.name,
                                "Status": "Processing",
                            }
                        )

                        st.success(
                            data.get(
                                "message",
                                "Document uploaded successfully!",
                            )
                        )

                        st.rerun()

                    except Exception:

                        st.success(
                            "🎉 Document uploaded successfully!"
                        )

                # =================================================
                # FILE TOO LARGE
                # =================================================

                elif response.status_code == 413:

                    st.error(
                        "Upload failed: file size exceeds the 50 MB limit."
                    )

                # =================================================
                # OTHER ERROR
                # =================================================

                else:

                    st.error(
                        f"Upload failed — Status Code: "
                        f"{response.status_code}"
                    )

            # =================================================
            # BACKEND OFFLINE
            # =================================================

            else:

                st.error(
                    "Connection error: Backend server is offline."
                )

    # =========================================================
    # WORKSPACE
    # =========================================================

    _html(
        """
        <div class="ob-dashboard-heading">

            <div>

                <div class="ob-section-label">
                    WORKSPACE
                </div>

                <h2>
                    Your Documents
                </h2>

            </div>

        </div>
        """
    )

    uploaded_files = st.session_state.get(
        "uploaded_files",
        [],
    )

    # =========================================================
    # STATISTICS
    # =========================================================

    col1, col2, col3 = st.columns(3)

    # =========================================================
    # DOCUMENTS
    # =========================================================

    with col1:

        _html(
            f"""
            <div class="ob-stat-card">

                <div class="ob-stat-label">
                    DOCUMENTS
                </div>

                <div class="ob-stat-value">
                    {len(uploaded_files)}
                </div>

                <div class="ob-stat-caption">
                    Uploaded files
                </div>

            </div>
            """
        )

    # =========================================================
    # PROCESSING
    # =========================================================

    with col2:

        processing_count = sum(
            1
            for item in uploaded_files
            if item.get("Status") == "Processing"
        )

        _html(
            f"""
            <div class="ob-stat-card">

                <div class="ob-stat-label">
                    PROCESSING
                </div>

                <div class="ob-stat-value">
                    {processing_count}
                </div>

                <div class="ob-stat-caption">
                    Currently indexing
                </div>

            </div>
            """
        )

    # =========================================================
    # ENGINE
    # =========================================================

    with col3:

        _html(
            """
            <div class="ob-stat-card">

                <div class="ob-stat-label">
                    ENGINE
                </div>

                <div class="ob-stat-value">
                    RAG
                </div>

                <div class="ob-stat-caption">
                    Multi-modal pipeline
                </div>

            </div>
            """
        )

    # =========================================================
    # DOCUMENT LIST
    # =========================================================

    if uploaded_files:

        _html(
            """
            <div class="ob-document-list">
            """
        )

        for item in uploaded_files:

            status = item.get(
                "Status",
                "Processing",
            )

            file_name = item.get(
                "File Name",
                "Unknown",
            )

            _html(
                f"""
                <div class="ob-document-row">

                    <div class="ob-document-left">

                        <div class="ob-small-file-icon">
                            📄
                        </div>

                        <div>

                            <div class="ob-document-name">
                                {file_name}
                            </div>

                            <div class="ob-document-type">
                                PDF DOCUMENT
                            </div>

                        </div>

                    </div>

                    <div class="ob-document-status">

                        <span class="ob-status-dot"></span>

                        {status}

                    </div>

                </div>
                """
            )

        _html(
            """
            </div>
            """
        )

    # =========================================================
    # EMPTY STATE
    # =========================================================

    else:

        _html(
            """
            <div class="ob-empty-state">

                <div class="ob-empty-icon">
                    🗂️
                </div>

                <h3>
                    No documents yet
                </h3>

                <p>
                    Upload your first PDF to start building your
                    OmniBrain knowledge workspace.
                </p>

            </div>
            """
        )