import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
from g4f.client import Client
import io

# 1. إعدادات الصفحة
st.set_page_config(page_title="UAE Engineering Auditor Pro", layout="wide", page_icon="🏗️")

# 2. قاموس الواجهة المصلح
lang_data = {
    "English": {
        "sidebar_title": "Control Panel",
        "region_label": "Project Location (Emirate)",
        "title": "🏗️ Full Technical Compliance & Gap Auditor",
        "run_btn": "🚀 Run Item-by-Item Audit",
        "table_header": "Detailed Compliance Report (Clause by Clause)",
        "down_btn": "📥 Download Excel Report"
    },
    "العربية": {
        "sidebar_title": "لوحة التحكم",
        "region_label": "موقع المشروع (الإمارة)",
        "title": "🏗️ مدقق المطابقة الفنية وحصر النواقص الشامل",
        "run_btn": "🚀 بدء التدقيق (بند بند)",
        "table_header": "تقرير المطابقة التفصيلي (بند مقابل بند)",
        "down_btn": "📥 تحميل التقرير (Excel)"
    }
}

municipalities_db = {
    "Abu Dhabi (DMT & Estidama)": {"auth": "DMT Abu Dhabi", "std": "Estidama/ADCC"},
    "Dubai (Municipality & RTA)": {"auth": "Dubai Municipality", "std": "Al Sa'fat System"},
    "Sharjah (Municipality)": {"auth": "Sharjah Municipality", "std": "Sharjah Code"},
    "Other Emirates": {"auth": "UAE Authority", "std": "UAE Fire Safety"}
}

with st.sidebar:
    ui_lang = st.selectbox("Language / اللغة", ["العربية", "English"])
    txt = lang_data[ui_lang]
    st.divider()
    selected_region = st.selectbox(txt["region_label"], list(municipalities_db.keys()))
    current = municipalities_db[selected_region]
    st.info(f"📍 Standard: {current['auth']}")

st.title(txt["title"])

col1, col2 = st.columns(2)
with col1:
    specs_file = st.file_uploader("Reference Specs (ملف المواصفات)", type=['pdf'])
with col2:
    offer_file = st.file_uploader("Technical Offer (العرض الفني)", type=['pdf'])

def extract_text(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# 3. محرك التدقيق الصارم
if st.button(txt["run_btn"]):
    if specs_file and offer_file:
        with st.spinner("جاري التدقيق العميق لكافة البنود..."):
            specs_txt = extract_text(specs_file)[:15000] # زيادة حجم القراءة
            offer_txt = extract_text(offer_file)[:15000]
            
            client = Client()
            
            # برومبت صارم لمنع ظهور None ولضمان فحص كل بند
            prompt = f"""
            Act as a Senior UAE Engineering Auditor. 
            Compare 'Specs' against 'Offer' item-by-item.
            
            STRICT INSTRUCTIONS:
            1. Extract every single Clause Number or Specification Title from the Specs.
            2. For EVERY clause, search if it exists in the Offer.
            3. If the clause is NOT found in the Offer, you MUST write 'NOT PROVIDED / MISSING' in the Status and Offer_Response.
            4. DO NOT LEAVE ANY COLUMN EMPTY. If information is missing, provide an AI estimation for Price and UAE Alternatives.
            5. Return ONLY a CSV table using (;) as separator. NO markdown, NO Item_Ref.

            COLUMNS:
            Clause_No; Specs_Requirement; Offer_Response; Status; Best_Alternatives_UAE; Price_Range_AED; AI_Municipality_Proposal.

            Language: {ui_lang}.
            Standard: {current['auth']}.
            Specs Content: {specs_txt}
            Offer Content: {offer_txt}
            """
            
            try:
                response = client.chat.completions.create(model="", messages=[{"role": "user", "content": prompt}])
                raw_data = response.choices[0].message.content
                
                if "Clause_No" in raw_data:
                    clean_csv = raw_data[raw_data.find("Clause_No"):].replace('|', '').strip()
                    df = pd.read_csv(io.StringIO(clean_csv), sep=';', on_bad_lines='skip')
                    
                    # استبدال أي قيم فارغة متبقية برسالة تنبيه
                    df.fillna("Not Specified", inplace=True)
                    
                    st.success(txt["success"].format(region=selected_region) if "success" in txt else "Success")
                    st.subheader(txt["table_header"])
                    st.dataframe(df, use_container_width=True)

                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False)
                    st.download_button(txt["down_btn"], output.getvalue(), "Detailed_Audit_Report.xlsx")
                else:
                    st.error("AI Error: Please try again or reduce PDF size.")
            except Exception as e:
                st.error(f"Error: {e}")