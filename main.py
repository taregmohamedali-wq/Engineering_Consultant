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
        "title": "🏗️ Technical Compliance & Gap Auditor",
        "run_btn": "🚀 Run Comprehensive Audit",
        "table_header": "Compliance, Gaps & Market Analysis Report",
        "down_btn": "📥 Download Excel Report"
    },
    "العربية": {
        "title": "🏗️ مدقق المطابقة الفنية وحصر النواقص الشامل",
        "run_btn": "🚀 بدء التدقيق الشامل",
        "table_header": "تقرير المطابقة، النواقص، وتحليل السوق التفصيلي",
        "down_btn": "📥 تحميل التقرير (Excel)"
    }
}

ui_lang = st.sidebar.selectbox("Language / اللغة", ["العربية", "English"])
txt = lang_data[ui_lang]

st.title(txt["title"])

col1, col2 = st.columns(2)
with col1:
    specs_file = st.file_uploader("Reference Specs (المواصفات المرجعية)", type=['pdf'])
with col2:
    offer_file = st.file_uploader("Technical Offer (العرض الفني)", type=['pdf'])

def extract_text(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    return "".join([page.get_text() for page in doc])

# 3. منطق التدقيق مع ضمان ملء كافة البيانات
if st.button(txt["run_btn"]):
    if specs_file and offer_file:
        progress_bar = st.progress(0)
        specs_txt = extract_text(specs_file)[:15000]
        offer_txt = extract_text(offer_file)[:15000]
        progress_bar.progress(30)
        
        client = Client()
        
        # برومبت يركز على اسم المواصفة، الحالة، وتعبئة كافة البيانات الأخرى
        prompt = f"""
        Act as a Senior UAE Engineering Auditor. Compare Specs vs Offer.
        
        MANDATORY RULES:
        1. NO 'Item_Ref' column.
        2. Column 1 MUST be 'Clause_or_Spec_Name' (Number or Title).
        3. Column 2 MUST be 'Status' (Compliant / Non-Compliant / Missing in Offer).
        4. YOU MUST FILL ALL OTHER COLUMNS: 'Specs_Requirement', 'Offer_Response', 'Best_Alternatives_UAE', 'Price_Range_AED', 'AI_Municipality_Proposal'.
        5. Return ONLY a CSV table using (;) as separator.
        
        Language: {ui_lang}.
        Specs: {specs_txt}
        Offer: {offer_txt}
        """
        
        try:
            response = client.chat.completions.create(model="", messages=[{"role": "user", "content": prompt}])
            raw_data = response.choices[0].message.content
            
            if "Status" in raw_data:
                clean_csv = raw_data[raw_data.find("Clause_or_Spec_Name"):].strip()
                df = pd.read_csv(io.StringIO(clean_csv), sep=';', on_bad_lines='skip')
                
                progress_bar.progress(100)
                st.subheader(txt["table_header"])
                
                # عرض الجدول بالتنسيق المنظم المطلوب
                st.dataframe(df, use_container_width=True)

                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
                st.download_button(txt["down_btn"], output.getvalue(), "Engineering_Audit_Report.xlsx")
            else:
                st.error("Format error. Please retry.")
        except Exception as e:
            st.error(f"Error: {e}")