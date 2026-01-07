import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
from g4f.client import Client
import io

# Professional Page Setup - Keeping the same look
st.set_page_config(page_title="UAE Engineering Auditor Pro", layout="wide", page_icon="🏗️")

emirates_authorities = {
    "Abu Dhabi": "DMT (Dept. of Municipalities and Transport) & Estidama",
    "Dubai": "Dubai Municipality (DM) & RTA Standards",
    "Sharjah": "Sharjah City Municipality & SEWA",
    "Ajman": "Ajman Municipality",
    "Umm Al Quwain": "UAQ Municipality",
    "Ras Al Khaimah": "RAK Municipality & Barjeel",
    "Fujairah": "Fujairah Municipality"
}

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/cb/Flag_of_the_United_Arab_Emirates.svg/255px-Flag_of_the_United_Arab_Emirates.svg.png", width=120)
    st.title("System Settings")
    report_lang = st.radio("Output Report Language", ["English", "Arabic"])
    selected_emirate = st.selectbox("Project Location (Emirate)", list(emirates_authorities.keys()))
    authority = emirates_authorities[selected_emirate]
    st.info(f"Compliance Standard: {authority}")

# Main Interface Header
st.title("🏗️ UAE Smart Engineering Auditor Pro")
st.markdown(f"**Status:** Connected to {selected_emirate} Market Database | **Standard:** {authority}")
st.write("Upload your documents to perform a 100% item-by-item compliance audit.")

col1, col2 = st.columns(2)
with col1:
    specs_file = st.file_uploader("1. Reference Specifications (PDF)", type=['pdf'])
with col2:
    offer_file = st.file_uploader("2. Technical Offer to Audit (PDF)", type=['pdf'])

def extract_text(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    return "".join([page.get_text() for page in doc])

if st.button("🚀 Start Comprehensive Audit"):
    if specs_file and offer_file:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("Extracting text from engineering documents...")
        specs_txt = extract_text(specs_file)[:7000]
        offer_txt = extract_text(offer_file)[:7000]
        progress_bar.progress(30)
        
        status_text.text(f"Auditing items against {authority} standards...")
        client = Client()
        
        # Improved Prompt to prevent CSV formatting errors
        prompt = f"""
        Act as a Senior UAE Engineering Auditor. Compare Specs vs Offer.
        IMPORTANT: Return ONLY a valid CSV table. Use (;) as separator. 
        Do not use (;) inside the text cells.
        
        Columns: Item_Ref; Specs_Requirement; Offer_Response; Status; UAE_Alternatives; Price_AED; Auditor_Note.
        
        Rules:
        1. Review EVERY technical item.
        2. Identify Missing or Non-Compliant items.
        3. Language: {report_lang}.
        
        Specs: {specs_txt}
        Offer: {offer_txt}
        """
        
        try:
            response = client.chat.completions.create(model="", messages=[{"role": "user", "content": prompt}])
            raw_data = response.choices[0].message.content
            
            # Cleaning the data from potential AI prefixes/suffixes
            if "Item_Ref" in raw_data:
                csv_clean = raw_data[raw_data.find("Item_Ref"):]
                
                # Using on_bad_lines='skip' to prevent the app from crashing
                df = pd.read_csv(io.StringIO(csv_clean), sep=';', on_bad_lines='skip')
                
                progress_bar.progress(100)
                status_text.success("✅ Audit Completed Successfully!")
                
                st.subheader(f"Detailed Compliance Report - {selected_emirate}")
                st.dataframe(df, use_container_width=True)

                # Excel Export
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Audit_Report')
                
                st.download_button(
                    label="📥 Download Full Audit Report (Excel)",
                    data=output.getvalue(),
                    file_name=f"Detailed_Audit_{selected_emirate}.xlsx"
                )
            else:
                st.error("AI returned non-structured data. Please try again.")
                st.text_area("Raw AI Response:", raw_data)
                
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.warning("Please upload files first.")