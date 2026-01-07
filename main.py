import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
from g4f.client import Client
import io
import re

# 1. Professional Page Configuration
st.set_page_config(page_title="UAE Engineering Auditor Pro", layout="wide", page_icon="🏗️")

# 2. Municipality Standards Mapping
municipalities_specs = {
    "Abu Dhabi": {"auth": "DMT & Estidama", "logic": "Abu Dhabi International Building Code & Pearl Rating."},
    "Dubai": {"auth": "Dubai Municipality (DM)", "logic": "Al Sa'fat Green Building System & DM Standards."},
    "Sharjah": {"auth": "Sharjah Municipality", "logic": "Sharjah Building Code & SEWA Regulations."},
    "Other Emirates": {"auth": "Local Municipality", "logic": "UAE Fire & Life Safety Code."}
}

# 3. Sidebar for Regional Control
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/cb/Flag_of_the_United_Arab_Emirates.svg/255px-Flag_of_the_United_Arab_Emirates.svg.png", width=120)
    st.title("Settings")
    selected_region = st.selectbox("Select Region", list(municipalities_specs.keys()))
    current = municipalities_specs[selected_region]
    st.info(f"Authority: {current['auth']}")

# 4. Main Interface
st.title("🏗️ UAE Smart Engineering Auditor Pro")
st.markdown(f"**Audit Mode:** {selected_region} Standards | **Standard:** {current['auth']}")

col1, col2 = st.columns(2)
with col1:
    specs_file = st.file_uploader("1. Reference Specs (PDF)", type=['pdf'])
with col2:
    offer_file = st.file_uploader("2. Technical Offer (PDF)", type=['pdf'])

def extract_text(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    return "".join([page.get_text() for page in doc])

# 5. Execution Logic
if st.button("🚀 Run Comprehensive Audit"):
    if specs_file and offer_file:
        progress_bar = st.progress(0)
        status = st.empty()
        
        # Text Extraction
        specs_txt = extract_text(specs_file)[:10000]
        offer_txt = extract_text(offer_file)[:10000]
        progress_bar.progress(30)
        
        status.text(f"Auditing according to {current['auth']}...")
        client = Client()
        
        # Strict Prompt for Structured Output
        prompt = f"""
        Act as a Senior UAE Engineering Auditor for {current['auth']}.
        Analyze Specs vs Offer. 
        MANDATORY: Return the result as a CLEAN CSV TABLE using the symbol (;) as the ONLY separator.
        DO NOT use any other separators like (|) or markdown table formatting.
        
        Columns: Item_Ref; Specs_Requirement; Status; Best_Alternatives; Price_Range_AED; AI_Municipality_Proposal.
        
        Requirements:
        - Analyze all items for {selected_region} compliance.
        - Provide realistic Price Ranges.
        - Strategic AI proposal per {current['logic']}.
        
        Specs: {specs_txt}
        Offer: {offer_txt}
        """
        
        try:
            response = client.chat.completions.create(model="", messages=[{"role": "user", "content": prompt}])
            raw_data = response.choices[0].message.content
            
            # 6. Critical Fix: Cleaning and Parsing the CSV
            if "Item_Ref" in raw_data:
                # Remove Markdown table symbols if present
                clean_data = raw_data[raw_data.find("Item_Ref"):].replace('|', '')
                
                # Load into Dataframe
                df = pd.read_csv(io.StringIO(clean_data), sep=';', on_bad_lines='skip')
                
                progress_bar.progress(100)
                status.success(f"Audit Completed Successfully for {selected_region}!")
                
                # 7. Display result in structured table (The look you want)
                st.subheader(f"Detailed Compliance Report - {selected_region}")
                st.dataframe(df, use_container_width=True)

                # Export Logic
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Audit_Report')
                st.download_button("📥 Download Excel Report", output.getvalue(), f"Audit_{selected_region}.xlsx")
            else:
                st.error("Format Error: AI returned non-structured text. Please run again.")
                st.text_area("Debug Info (Raw Data):", raw_data)
                
        except Exception as e:
            st.error(f"System Error: {e}")
    else:
        st.warning("Please upload both files.")