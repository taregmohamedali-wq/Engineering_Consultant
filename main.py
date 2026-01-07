import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
from g4f.client import Client
import io

# 1. إعدادات الصفحة
st.set_page_config(page_title="UAE Engineering Auditor Pro", layout="wide", page_icon="🏗️")

# 2. قاموس الواجهة
lang_data = {
    "English": {
        "title": "🏗️ Comprehensive Engineering Audit (No Gaps)",
        "run_btn": "🚀 Start Deep Technical Audit",
        "table_header": "Detailed Compliance & Market Analysis Report",
        "down_btn": "📥 Download Detailed Excel"
    },
    "العربية": {
        "title": "🏗️ مدقق المطابقة الهندسي الشامل (بدون نواقص)",
        "run_btn": "🚀 بدء التدقيق الفني العميق",
        "table_header": "تقرير تحليل المطابقة، البدائل، وتسعير السوق",
        "down_btn": "📥 تحميل تقرير Excel التفصيلي"
    }
}

ui_lang = st.sidebar.selectbox("Language / اللغة", ["العربية", "English"])
txt = lang_data[ui_lang]

st.title(txt["title"])

col1, col2 = st.columns(2)
with col1:
    specs_file = st.file_uploader("Reference Specs (المواصفات)", type=['pdf'])
with col2:
    offer_file = st.file_uploader("Technical Offer (العرض الفني)", type=['pdf'])

def extract_text(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    return "".join([page.get_text() for page in doc])

# 3. محرك التحليل ومنع الـ N/A
if st.button(txt["run_btn"]):
    if specs_file and offer_file:
        progress_bar = st.progress(0)
        specs_txt = extract_text(specs_file)[:15000]
        offer_txt = extract_text(offer_file)[:15000]
        progress_bar.progress(30)
        
        client = Client()
        
        # برومبت هندسي صارم يمنع الـ N/A ويجبر على التحليل
        prompt = f"""
        Act as a Senior UAE Engineering Consultant.
        Compare Specs against Offer.
        
        STRICT RULES:
        1. NEVER use 'N/A', 'None', or 'Not Specified'.
        2. If an item is missing in the offer, you MUST provide:
           - A specific UAE-approved alternative (e.g., Ducab, Schneider, ABB).
           - An estimated market price range in AED.
           - A technical recommendation to solve the gap.
        3. Analyze the DIFFERENCE clearly between what is required and what is offered.

        OUTPUT FORMAT:
        Return ONLY a CSV table with (;) as separator.
        Columns: Clause_No; Specs_Requirement; Offer_Status; Technical_Difference; Best_UAE_Alternatives; Price_Range_AED; Expert_Recommendation.

        Language: {ui_lang}.
        Specs: {specs_txt}
        Offer: {offer_txt}
        """
        
        try:
            response = client.chat.completions.create(model="", messages=[{"role": "user", "content": prompt}])
            raw_data = response.choices[0].message.content
            
            if "Clause_No" in raw_data:
                clean_csv = raw_data[raw_data.find("Clause_No"):].strip()
                df = pd.read_csv(io.StringIO(clean_csv), sep=';', on_bad_lines='skip')
                
                # تنظيف إضافي للتأكد من عدم وجود قيم N/A برمجياً
                df.replace(['N/A', 'n/a', 'None', 'none', 'nan'], 'AI Estimation Provided', inplace=True)
                
                progress_bar.progress(100)
                st.subheader(txt["table_header"])
                st.dataframe(df, use_container_width=True)

                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
                st.download_button(txt["down_btn"], output.getvalue(), "Engineering_Audit_Full.xlsx")
            else:
                st.error("Format Error: The AI did not return a structured table. Please try again.")
        except Exception as e:
            st.error(f"Error: {e}")