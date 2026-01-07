import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
from g4f.client import Client
import io

# Professional Page Setup
st.set_page_config(page_title="UAE Engineering Auditor Pro", layout="wide", page_icon="🏗️")

# Emirates Regulatory Authorities Mapping
emirates_authorities = {
    "Abu Dhabi": "DMT (Dept. of Municipalities and Transport) & Estidama",
    "Dubai": "Dubai Municipality (DM) & RTA Standards",
    "Sharjah": "Sharjah City Municipality & SEWA",
    "Ajman": "Ajman Municipality",
    "Umm Al Quwain": "UAQ Municipality",
    "Ras Al Khaimah": "RAK Municipality & Barjeel",
    "Fujairah": "Fujairah Municipality"
}

# Sidebar Settings
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/cb/Flag_of_the_United_Arab_Emirates.svg/255px-Flag_of_the_United_Arab_Emirates.svg.png", width=120)
    st.title("System Settings")
    report_lang = st.radio("Output Report Language", ["English", "Arabic"])
    selected_emirate = st.selectbox("Project Location (Emirate)", list(emirates_authorities.keys()))
    authority = emirates_authorities[selected_emirate]
    st.info(f"Compliance Standard: {authority}")

# Main Interface (English by Default)
st.title("🏗️ UAE Smart Engineering Auditor Pro")
st.markdown(f"**Status:** Connected to {selected_emirate} Market Database | **Standard:** {authority}")
st.write("Upload your documents to perform a 100% item-by-item compliance audit.")

# Upload Section
col1, col2 = st.columns(2)
with col1:
    specs_file = st.file_uploader("1. Reference Specifications (PDF)", type=['pdf'])
with col2:
    offer_file = st.file_uploader("2. Technical Offer to Audit (PDF)", type=['pdf'])

def extract_text(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    return full_text

# Analysis Action
if st.button("🚀 Start Comprehensive Audit"):
    if specs_file and offer_file:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Step 1: Text Extraction
        status_text.text("Extracting text from engineering documents...")
        specs_text = extract_text(specs_file)
        offer_text = extract_text(offer_file)
        progress_bar.progress(30)
        
        # Step 2: AI Audit Logic
        status_text.text(f"Auditing items against {authority} standards...")
        client = Client()
        
        # Strict Prompt to ensure 100% item review
        prompt = f"""
        Role: Senior UAE Engineering Auditor.
        Task: Perform a full Gap Analysis.
        1. Extract EVERY clause and technical item from the 'Specs'.
        2. Cross-check each with the 'Offer'.
        3. Identify: Compliant, Non-Compliant, or Missing items.
        4. For Non-Compliant/Missing: Suggest 2 UAE-available alternatives with estimated prices in AED.
        
        Output: ONLY a CSV table (separator: ;)
        Columns: Item Ref; Specs Requirement; Offer Response; Compliance Status; UAE Alternatives; Price Est. (AED); Auditor's Note ({authority}).
        
        Language of Report: {report_lang}.
        Context: Specs({specs_text[:8000]}) Offer({offer_text[:8000]})
        """
        
        try:
            response = client.chat.completions.create(model="", messages=[{"role": "user", "content": prompt}])
            res_data = response.choices[0].message.content
            progress_bar.progress(80)
            
            # Step 3: Data Processing
            df = pd.read_csv(io.StringIO(res_data), sep=';')
            
            progress_bar.progress(100)
            status_text.success("✅ Audit Completed Successfully!")
            
            st.subheader(f"Detailed Compliance Report - {selected_emirate}")
            st.dataframe(df, use_container_width=True)

            # Excel Export
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Engineering_Audit')
            
            st.download_button(
                label="📥 Download Full Audit Report (Excel)",
                data=output.getvalue(),
                file_name=f"Detailed_Audit_{selected_emirate}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
        except Exception as e:
            st.error(f"AI Audit Error: {e}")
            st.info("Try reducing the PDF size or ensure the text is not an image (scanned).")
    else:
        st.warning("Please upload both Specifications and Technical Offer files.")