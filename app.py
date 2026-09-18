import os
import tempfile
import streamlit as st
from src.pdf_reader import detect_pdf_type, extract_text_from_pdf
from src.ocr_engine import extract_text_from_image_pdf
from src.parser import extract_account_info, parse_transactions
from src.classifier import train_ml_classifier, classify_transactions
from src.exporter import export_data, export_summary

st.set_page_config(page_title="Bank Statement Processor", layout="wide")
st.title("🏦 Bank Statement Processing & Classification")
st.caption("Upload a PDF bank statement → auto-detect type → extract → classify (no LLM) → export to CSV/Excel")

# Cache the ML model so it doesn't retrain on every upload
@st.cache_resource
def get_ml_model():
    return train_ml_classifier()

uploaded = st.file_uploader("Upload PDF bank statement", type=["pdf"])

if uploaded is not None:
    # Save uploaded file to a temp path
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded.read())
        pdf_path = tmp.name

    try:
        # Step 1: Detect PDF type
        with st.spinner("Detecting PDF type..."):
            pdf_type = detect_pdf_type(pdf_path)
        st.info(f"**Detected PDF type:** `{pdf_type}`")

        # Step 2: Extract text
        with st.spinner("Extracting text..."):
            if pdf_type == "text":
                raw_text = extract_text_from_pdf(pdf_path)
            else:
                raw_text = extract_text_from_image_pdf(pdf_path)

        if not raw_text or len(raw_text.strip()) < 20:
            st.error("Could not extract meaningful text from this PDF. Try a clearer scan.")
            st.stop()

        # Step 3: Parse account info + transactions
        with st.spinner("Parsing account info and transactions..."):
            account_info = extract_account_info(raw_text)
            transactions = parse_transactions(raw_text)

        # Step 4: Classify
        with st.spinner("Classifying transactions..."):
            model = get_ml_model()
            transactions = classify_transactions(transactions, model)

        # Step 5: Display
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📋 Account Information")
            st.json(account_info)
        with col2:
            st.subheader("📊 Summary")
            st.metric("Total transactions", len(transactions))

        st.subheader(f"💳 Transactions ({len(transactions)})")
        if transactions:
            import pandas as pd
            df = pd.DataFrame(transactions)
            st.dataframe(df, use_container_width=True)

            # Step 6: Export
            df_out, files = export_data(transactions, account_info)
            export_summary(transactions)

            st.subheader("⬇ Download")
            c1, c2 = st.columns(2)
            with c1:
                with open(files["csv"], "rb") as f:
                    st.download_button("Download CSV", f, "transactions.csv", "text/csv")
            with c2:
                with open(files["excel"], "rb") as f:
                    st.download_button(
                        "Download Excel",
                        f,
                        "transactions.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
        else:
            st.warning("No transactions were detected. Check the raw text below to see what was extracted.")

        # Debug expander — shows raw text (very useful and shows engineering maturity)
        with st.expander("🔍 Show raw extracted text (debug)"):
            st.text(raw_text[:5000])

    finally:
        try:
            os.unlink(pdf_path)
        except Exception:
            pass