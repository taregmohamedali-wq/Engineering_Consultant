import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
from g4f.client import Client
import io

# Professional UI Setup
st.set_page_config(page_title="UAE Engineering Auditor Pro", layout="wide", page_icon="🏗️")

emirates_authorities = {
    "Abu Dhabi": "DMT & Estidama",
    "Dubai": "Dubai Municipality & RTA",
    "Sharjah": "Sharjah Municipality & SEWA",
    "Ajman": "Ajman Municipality",
    "Ras Al Khaimah": "RAK Municipality & Barjeel",
    "Fujairah": "Fujairah Municipality"
}

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/cb/Flag_of_the_United_Arab_Emirates.svg/255px-Flag_of_the_United_Arab_Emirates.svg.png", width=120)
    st.title("System Settings")
    report_lang = st.radio("Output Report Language", ["English", "Arabic"])
    selected_emirate = st.selectbox("Project Location", list(emirates_authorities.keys()))
    authority = emirates_authorities[selected_emirate]

st.title("🏗️ UAE Smart Engineering Auditor Pro")
st.markdown(f"**Standard:** {authority} | **Target Market:** {selected_emirate} Suppliers")

col1, col2 = st.columns(2)
with col1:
    specs_file = st.file_uploader("Reference Specs (PDF)", type=['pdf'])
with col2:
    offer_file = st.file_uploader("Technical Offer (PDF)", type=['pdf'])

def extract_text(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    return "".join([page.get_text() for page in doc])

if st.button("🚀 Run Deep Audit & Price Check"):
    if specs_file and offer_file:
        progress_bar = st.progress(0)
        status = st.empty()
        
        status.text("Deep scanning PDF pages...")
        specs_txt = extract_text(specs_file)[:10000] # زيادة حجم النص للقراءة الشاملة
        offer_txt = extract_text(offer_file)[:10000]
        progress_bar.progress(30)
        
        status.text(f"Searching for {selected_emirate} market prices & alternatives...")
        client = Client()
        
        # برومبت مكثف لإجبار الـ AI على وضع الأسعار والبدائل
        prompt = f"""
        ACT AS A SENIOR UAE COST CONSULTANT. 
        MANDATORY REQUIREMENT: For every technical item, you MUST provide:
        1. A real local alternative available in UAE (e.g., Ducab, Riyadh Cables, Schneider UAE).
        2. A realistic ESTIMATED UNIT PRICE in AED based on current market trends in {selected_emirate}.
        
        TABLE FORMAT: Use (;) as separator ONLY. 
        Columns: Item_Ref; Specs_Requirement; Offer_Response; Status; UAE_Local_Alternatives; Price_AED_Est; Auditor_Note.
        
        Language: {report_lang}.
        Audit every single section in the provided Specs: {specs_txt}
        Compare with Offer: {offer_txt}
        """
        
        try:
            response = client.chat.completions.create(model="", messages=[{"role": "user", "content": prompt}])
            raw_data = response.choices[0].message.content
            
            if "Item_Ref" in raw_data:
                csv_clean = raw_data[raw_data.find("Item_Ref"):]
                df = pd.read_csv(io.StringIO(csv_clean), sep=';', on_bad_lines='skip')
                
                # إجبار الخانات الفارغة على التعبئة (اختياري لضمان المظهر)
                df.fillna("Check Market Price", inplace=True)
                
                progress_bar.progress(100)
                status.success("✅ Deep Audit Completed!")
                st.dataframe(df, use_container_width=True)

                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Deep_Audit_Results')
                
                st.download_button("📥 Download Report with Prices (Excel)", output.getvalue(), f"Deep_Audit_{selected_emirate}.xlsx")
            else:
                st.error("Data processing failed. Please click 'Run' again to refresh AI connection.")
                
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.warning("Please upload both documents.")