import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
from g4f.client import Client
import io

# 1. إعدادات الصفحة والواجهة (ثبات الشكل العام)
st.set_page_config(page_title="UAE Engineering Auditor Pro", layout="wide", page_icon="🏗️")

lang_data = {
    "English": {
        "sidebar_title": "Consultant Control Panel",
        "region_label": "Project Location (Emirate)",
        "title": "🏗️ Full Clause-by-Clause Engineering Auditor",
        "run_btn": "🚀 Run 100% Comprehensive Audit",
        "table_header": "Detailed Technical Compliance & Full Discrepancy Report",
        "down_btn": "📥 Download Full Report (Excel)",
        "processing": "Scrutinizing EVERY single clause... No items will be ignored."
    },
    "العربية": {
        "sidebar_title": "لوحة التحكم الاستشارية",
        "region_label": "موقع المشروع (الإمارة)",
        "title": "🏗️ مدقق البنود الهندسي الشامل (بند بند)",
        "run_btn": "🚀 بدء التدقيق الشامل بنسبة 100%",
        "table_header": "تقرير مطابقة البنود وتحليل الفوارق (مراجعة كاملة)",
        "down_btn": "📥 تحميل التقرير الشامل (Excel)",
        "processing": "جاري فحص كل بند على حدة... لن يتم تجاهل أي تفصيلة."
    }
}

municipalities_db = {
    "Abu Dhabi (DMT & Estidama)": {"auth": "DMT Abu Dhabi", "std": "Estidama"},
    "Dubai (Municipality & RTA)": {"auth": "Dubai Municipality", "std": "Al Sa'fat"},
    "Sharjah (Municipality)": {"auth": "Sharjah Municipality", "std": "Sharjah Code"},
    "Other Emirates": {"auth": "UAE Authority", "std": "General Code"}
}

# --- القائمة الجانبية (Sidebar) لضمان ثبات الإمارة ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/cb/Flag_of_the_United_Arab_Emirates.svg/255px-Flag_of_the_United_Arab_Emirates.svg.png", width=100)
    ui_lang = st.selectbox("Language / اللغة", ["العربية", "English"])
    txt = lang_data[ui_lang]
    st.divider()
    selected_region = st.selectbox(txt["region_label"], list(municipalities_db.keys()))
    current = municipalities_db[selected_region]
    st.info(f"📍 Authority: {current['auth']}")

st.title(txt["title"])

col1, col2 = st.columns(2)
with col1:
    specs_file = st.file_uploader("1. Reference Specs (المواصفات المرجعية)", type=['pdf'])
with col2:
    offer_file = st.file_uploader("2. Technical Offer (العرض الفني)", type=['pdf'])

def extract_full_text(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    return " ".join([page.get_text() for page in doc])

# 3. محرك التدقيق الشامل (Zero-Gap Logic)
if st.button(txt["run_btn"]):
    if specs_file and offer_file:
        progress_bar = st.progress(0)
        status_msg = st.empty()
        
        status_msg.warning(txt["processing"])
        # زيادة حجم المسح لضمان عدم ضياع البنود في الملفات الكبيرة
        specs_txt = extract_full_text(specs_file)[:30000] 
        progress_bar.progress(30)
        
        offer_txt = extract_full_text(offer_file)[:25000]
        progress_bar.progress(60)
        
        client = Client()
        
        # برومبت صارم جداً يمنع تجاهل أي بند ويتبع منطق الاستشاري الذي أرفقته
        prompt = f"""
        Act as a Senior Technical Auditor. You are prohibited from skipping or summarizing clauses.
        
        MANDATORY INSTRUCTIONS:
        1. SCAN EVERY CLAUSE: Extract every numbered item (e.g., 1.1.1, 2.1, 260519) from the Specs.
        2. CROSS-CHECK: For each extracted item, find its equivalent in the Offer.
        3. DISCREPANCY ANALYSIS: 
           - Identify technical gaps (e.g., THD percentages, missing 55" display).
           - Identify missing documents (e.g., COO, Warranty Draft, Declaration of Conformity).
           - Identify missing logic (e.g., Remote control from Server Room).
        4. NO SUMMARY: If the Specs have 50 items, the table MUST have 50 rows.
        
        COLUMNS:
        Clause_No; Clause_Title_Description; Offer_Status; Consultant_Notes_Discrepancies; Required_Action; UAE_Alternatives; Price_Range_AED.

        Language: {ui_lang}.
        Separator: (;)
        """
        
        try:
            response = client.chat.completions.create(
                model="", 
                messages=[{"role": "user", "content": f"{prompt}\nReference Specs: {specs_txt}\nTechnical Offer: {offer_txt}"}]
            )
            raw_data = response.choices[0].message.content
            
            if "Clause_No" in raw_data:
                clean_csv = raw_data[raw_data.find("Clause_No"):].strip()
                df = pd.read_csv(io.StringIO(clean_csv), sep=';', on_bad_lines='skip')
                
                progress_bar.progress(100)
                status_msg.empty()
                
                # 4. عرض النتائج (الجدول الاحترافي)
                st.subheader(txt["table_header"])
                st.dataframe(df, use_container_width=True)

                # خيار التحميل
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
                st.download_button(txt["down_btn"], output.getvalue(), "Comprehensive_Audit_No_Gaps.xlsx")
            else:
                st.error("AI Output Error: The analysis was too short or unstructured. Please try once more.")
        except Exception as e:
            st.error(f"Audit System Error: {e}")