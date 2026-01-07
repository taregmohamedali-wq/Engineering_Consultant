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
        
        status.text("Reading engineering documents...")
        specs_txt = extract_text(specs_file)[:10000]
        offer_txt = extract_text(offer_file)[:10000]
        progress_bar.progress(30)
        
        status.text("AI is generating the structured table...")
        client = Client()
        
        # التعديل هنا لضمان خروج البيانات بتنسيق يفهمه البرنامج ويحوله لجدول
        prompt = f"""
        Act as a Senior UAE Engineering Auditor. 
        Compare Specs vs Offer and return a CSV table using (;) as a separator.
        IMPORTANT: Do not include any text or markers like (|) outside the CSV format.
        
        Columns: Item_Ref; Specs_Requirement; Offer_Response; Status; UAE_Local_Alternatives; Price_AED_Est; Auditor_Note.
        
        Requirements:
        1. Review every technical item from the specs.
        2. Provide REAL UAE alternatives (e.g., Ducab, Schneider, ABB).
        3. Provide realistic ESTIMATED prices in AED.
        4. Language: {report_lang}.
        
        Specs: {specs_txt}
        Offer: {offer_txt}
        """
        
        try:
            response = client.chat.completions.create(model="", messages=[{"role": "user", "content": prompt}])
            raw_data = response.choices[0].message.content
            
            # معالجة النص لضمان تحويله لجدول (DataFrame)
            if "Item_Ref" in raw_data:
                # تنظيف أي رموز زائدة قد تضعها بعض موديلات الـ AI
                clean_csv = raw_data[raw_data.find("Item_Ref"):].replace('|', '').strip()
                
                # قراءة البيانات كجدول
                df = pd.read_csv(io.StringIO(clean_csv), sep=';', on_bad_lines='skip')
                
                progress_bar.progress(100)
                status.success("✅ Deep Audit Completed! Results below in structured table.")
                
                # عرض الجدول بشكل احترافي (نفس شكل الصورة الأولى)
                st.subheader(f"Detailed Compliance Report - {selected_emirate}")
                st.dataframe(df, use_container_width=True)

                # زر التحميل
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Audit_Results')
                
                st.download_button("📥 Download Report (Excel)", output.getvalue(), f"Audit_{selected_emirate}.xlsx")
            else:
                st.error("Format Error: AI did not return a proper table. Please try running the audit again.")
                st.text_area("Raw Response for Debug:", raw_data)
                
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.warning("Please upload both PDF files.")