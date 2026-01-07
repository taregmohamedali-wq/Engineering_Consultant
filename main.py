import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
from g4f.client import Client
import io

# 1. إعدادات الصفحة (الحفاظ على المظهر الداكن والاحترافي)
st.set_page_config(page_title="UAE Engineering Auditor Pro", layout="wide", page_icon="🏗️")

lang_data = {
    "English": {
        "sidebar_title": "Control Panel",
        "region_label": "Project Location (Emirate)",
        "title": "🏗️ Engineering Compliance & Market Analyzer",
        "run_btn": "🚀 Run Deep Technical Audit",
        "table_header": "Detailed Technical Compliance & Gap Analysis Report",
        "down_btn": "📥 Download Report (Excel)",
        "processing": "Analyzing every clause... ensuring 100% clarity."
    },
    "العربية": {
        "sidebar_title": "لوحة التحكم",
        "region_label": "موقع المشروع (الإمارة)",
        "title": "🏗️ مدقق المطابقة الهندسي وتحليل السوق",
        "run_btn": "🚀 بدء التدقيق الفني العميق",
        "table_header": "تقرير تحليل المطابقة الفنية، الفروقات، والتسعير",
        "down_btn": "📥 تحميل التقرير التفصيلي (Excel)",
        "processing": "جاري مراجعة كافة البنود بدقة متناهية... يرجى الانتظار."
    }
}

municipalities_db = {
    "Abu Dhabi (DMT & Estidama)": {"auth": "DMT Abu Dhabi", "std": "Estidama"},
    "Dubai (Municipality & RTA)": {"auth": "Dubai Municipality", "std": "Al Sa'fat"},
    "Sharjah (Municipality)": {"auth": "Sharjah Municipality", "std": "Sharjah Code"},
    "Other Emirates": {"auth": "UAE Authority", "std": "General Code"}
}

# --- القائمة الجانبية (Sidebar) ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/cb/Flag_of_the_United_Arab_Emirates.svg/255px-Flag_of_the_United_Arab_Emirates.svg.png", width=100)
    ui_lang = st.selectbox("Language / اللغة", ["العربية", "English"])
    txt = lang_data[ui_lang]
    st.divider()
    selected_region = st.selectbox(txt["region_label"], list(municipalities_db.keys()))
    current = municipalities_db[selected_region]
    st.success(f"📍 Standard: {current['auth']}")

st.title(txt["title"])

col1, col2 = st.columns(2)
with col1:
    specs_file = st.file_uploader("1. Reference Specs (المواصفات المرجعية)", type=['pdf'])
with col2:
    offer_file = st.file_uploader("2. Technical Offer (العرض الفني)", type=['pdf'])

def extract_text(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    return " ".join([page.get_text() for page in doc])

# 3. محرك التدقيق والتحليل الواضح
if st.button(txt["run_btn"]):
    if specs_file and offer_file:
        progress_bar = st.progress(0)
        status_msg = st.empty()
        
        status_msg.info(txt["processing"])
        specs_txt = extract_text(specs_file)[:20000]
        progress_bar.progress(30)
        
        offer_txt = extract_text(offer_file)[:20000]
        progress_bar.progress(60)
        
        client = Client()
        
        # برومبت يضمن وضوح التحليل وفصل البنود (مطابق + مختلف + مفقود)
        prompt = f"""
        Act as a Senior UAE Technical Auditor. Compare EVERY clause from Specs against Offer.
        
        REQUIRED TABLE STRUCTURE (Clear & Precise):
        1. Clause_No: Extract the specific number (e.g., 260519).
        2. Clause_Name: Extract the technical title (e.g., Low Voltage Cables).
        3. Status: Must be one of (COMPLIANT, DIFFERENT, MISSING).
        4. Technical_Comparison: 
           - If COMPLIANT: Write 'Fully Matches Specs'.
           - If DIFFERENT: Detail the gap (e.g., brand mismatch, material change).
           - If MISSING: Write 'Not addressed in the technical offer'.
        5. UAE_Alternatives: Provide approved brands (e.g., Ducab, Schneider, ABB).
        6. Market_Price_AED: Estimated price range in UAE market.
        7. Expert_Recommendation: Precise action for the engineer.

        Language: {ui_lang}.
        Formatting: Return ONLY a clean CSV with (;) separator. No markdown code blocks.
        """
        
        try:
            response = client.chat.completions.create(
                model="", 
                messages=[{"role": "user", "content": f"{prompt}\nSpecs Data: {specs_txt}\nOffer Data: {offer_txt}"}]
            )
            raw_data = response.choices[0].message.content
            
            # معالجة البيانات لضمان نظافة الجدول
            if "Clause_No" in raw_data:
                clean_csv = raw_data[raw_data.find("Clause_No"):].strip()
                df = pd.read_csv(io.StringIO(clean_csv), sep=';', on_bad_lines='skip')
                
                # حذف أي صفوف فارغة أو مشوهة
                df.dropna(subset=['Clause_No', 'Status'], inplace=True)
                
                progress_bar.progress(100)
                status_msg.empty()
                
                # 4. عرض النتائج (وضوح تام)
                st.subheader(txt["table_header"])
                st.dataframe(df, use_container_width=True)

                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
                st.download_button(txt["down_btn"], output.getvalue(), "Engineering_Audit_Report.xlsx")
            else:
                st.error("Format Error: AI output was not clear. Please run the audit again.")
        except Exception as e:
            st.error(f"Error during analysis: {e}")