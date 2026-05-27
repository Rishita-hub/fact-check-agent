import streamlit as st
import pandas as pd

from utils import (
    extract_text_from_pdf,
    extract_claims,
    verify_claim
)

st.set_page_config(
    page_title="Fact Check Agent",
    layout="wide"
)

st.title("🔍 Fact-Check Agent")
st.sidebar.title("About")

st.sidebar.info(
    """
    This AI-powered Fact Check Agent:
    
    - Extracts factual claims from PDFs
    - Verifies claims using live web data
    - Detects misinformation
    - Suggests corrected facts
    """
)
st.write("Upload a PDF to detect false or outdated claims.")

uploaded_file = st.file_uploader(
    "Upload PDF",
    type=["pdf"]
)

if uploaded_file:

    with st.spinner("Extracting text from PDF..."):

        text = extract_text_from_pdf(uploaded_file)

    st.success("PDF text extracted successfully!")

    with st.spinner("Extracting factual claims..."):

        claims = extract_claims(text)

    st.subheader("Detected Claims")

    for claim in claims:
        st.write("•", claim)

    st.subheader("Fact Check Results")

    results = []

    progress_bar = st.progress(0)

    total_claims = len(claims)

    for index, claim in enumerate(claims):

        verification, source_urls = verify_claim(claim)

        status = "Unknown"
        explanation = ""
        correct_fact = ""

        lines = verification.split("\n")

        for line in lines:

            if "Status:" in line:
                status = line.replace("Status:", "").strip()

            elif "Explanation:" in line:
                explanation = line.replace("Explanation:", "").strip()

            elif "Correct Fact:" in line:
                correct_fact = line.replace("Correct Fact:", "").strip()

        results.append({
            "Claim": claim,
            "Status": status,
            "Explanation": explanation,
            "Correct Fact": correct_fact,
            "Sources": "\n".join(source_urls)
        })

        progress_bar.progress((index + 1) / total_claims)

    df = pd.DataFrame(results)

    def highlight_status(val):

        if val == "Verified":
            return "background-color: #b6fcb6"

        elif val == "Inaccurate":
            return "background-color: #ffe699"

        elif val == "False":
            return "background-color: #ffb3b3"

        return ""

    styled_df = df.style.map(
        highlight_status,
        subset=["Status"]
    )

    
    st.data_editor(
    styled_df,
    column_config={
        "Claim": st.column_config.TextColumn(
            "Claim", 
            help="The claim extracted from the PDF",
            width="medium"
        ),
        "Status": st.column_config.TextColumn(
            "Status", 
            width="small"
        ),
        "Explanation": st.column_config.TextColumn(
            "Explanation", 
            help="Live search cross-reference analysis",
            width="large"
        ),
        "Correct Fact": st.column_config.TextColumn(
            "Correct Fact", 
            help="Verified factual data from authoritative sources",
            width="medium"
        ),
    },
    disabled=True,          # Keeps the data read-only so they can't change your results
    hide_index=True,        # Removes the ugly 0, 1, 2 row numbers on the left
    use_container_width=True
)

    st.success("Fact checking completed!")