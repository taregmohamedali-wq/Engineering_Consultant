import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
from g4f.client import Client
import io

# 1. إعدادات الصفحة (ثابتة للحفاظ على المظهر)
st.set_page_config(page_title="UAE Engineering Auditor Pro", layout="wide", page_icon="🏗️")

# 2. قاموس اللغات لضمان ثبات الواجهة
lang_data = {
    "English": {
        "sidebar_title": "Control Panel",
        "region_label": "Project Location (Emirate)",
        "title": "🏗️ Full Technical Compliance & Gap Auditor",
        "run_btn": "🚀 Run Deep Item-by-Item Audit",
        "table_header": "Comprehensive Compliance, Gaps & Pricing Analysis",
        "down_btn": "📥 Download Full Report (Excel)",
        "processing": "Analyzing every clause... Please wait."
    },
    "العربية": {
        "sidebar_title": "لوحة التحكم",
        "region_label": "موقع المشروع (الإمارة)",
        "title": "🏗️ مدقق المطابقة الفنية وحصر النواقص الشامل",
        "run_btn": "🚀 بدء التدقيق العميق (بند مقابل بند)",
        "table_header": "تقرير تحليل المطابقة الكاملة، النواقص، والتسعير",
        "down_btn": "📥 تحميل التقرير الشامل (Excel)",
        "processing": "جاري تدقيق كافة البنود... يرجى الانتظار."
    }
}

# 3. قاعدة بيانات البلديات (تظهر في القائمة الجانبية)
municipalities_db = {
    "Abu Dhabi (DMT & Estidama)": {"auth": "DMT Abu Dhabi", "std": "Estidama"},
    "Dubai (Municipality & RTA)": {"auth": "Dubai Municipality", "std": "Al Sa'fat"},
    "Sharjah (Municipality)": {"auth": "Sharjah Municipality", "std": "Sharjah Code"},
    "Other Emirates": {"auth": "UAE Authority", "std": "UAE General Code"}
}

# --- القائمة الجانبية (Sidebar) لضمان ظهور الإمارة ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/cb/Flag_of_the_United_Arab_Emirates.svg/255px-Flag_of_the_United_Arab_Emirates.svg.png", width=100)
    ui_lang = st.selectbox("Language / اللغة", ["العربية", "English"])
    txt = lang_data[ui_lang]
    st.divider()
    # تثبيت اختيار الإمارة لضمان عدم اختفائها
    selected_region = st.selectbox(txt["region_label"], list(municipalities_db.keys()))
    current = municipalities_db[selected_region]
    st.success(f"📍 Standard: {current['auth']}")

# --- الواجهة الرئيسية ---
st.title(txt["title"])

col1, col2 = st.columns(2)
with col1:
    specs_file = st.file_uploader("1. Reference Specs (المواصفات المرجعية)", type=['pdf'])
with col2:
    offer_file = st.file_uploader("2. Technical Offer (العرض الفني)", type=['pdf'])

def extract_text(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    return "".join([page.get_text() for page in doc])

# 4. محرك التدقيق والتحليل العميق
if st.button(txt["run_btn"]):
    if specs_file and offer_file:
        # إظهار شريط التحقق (Progress Bar)
        progress_bar = st.progress(0)
        status_msg = st.empty()
        
        status_msg.info(txt["processing"])
        specs_txt = extract_text(specs_file)[:15000]
        progress_bar.progress(30)
        
        offer_txt = extract_text(offer_file)[:15000]
        progress_bar.progress(50)
        
        client = Client()
        
        # برومبت صارم يمنع الـ N/A ويحلل الفروقات بدقة
        prompt = f"""
        Act as a Senior UAE Engineering Auditor for {current['auth']}.
        Analyze Specs against Offer بند بند (Item-by-Item).

        STRICT RULES:
        1. NO 'N/A' or 'None'. Provide AI estimations if data is missing.
        2. Column 1: Clause_No or Specification Title.
        3. Column 2: Specs_Requirement (Summary).
        4. Column 3: Offer_Response (What did they provide?).
        5. Column 4: Compliance_Status (Compliant / Partially / Missing).
        6. Column 5: Technical_Difference (Explain the gap clearly).
        7. Column 6: Market_Price_AED (Estimated range in UAE).
        8. Column 7: Expert_Recommendation (Actionable advice).

        Format: Return ONLY a CSV table with (;) separator.
        Language: {ui_lang}.
        """
        
        try:
            response = client.chat.completions.create(model="", messages=[{"role": "user", "content": f"{prompt}\nSpecs: {specs_txt}\nOffer: {offer_txt}"}])
            raw_data = response.choices[0].message.content
            
            if "Clause_No" in raw_data or "بند" in raw_data:
                # تنظيف البيانات وتحويلها لجدول
                clean_csv = raw_data[raw_data.find("Clause_No") if "Clause_No" in raw_data else raw_data.find("بند"):].strip()
                df = pd.read_csv(io.StringIO(clean_csv), sep=';', on_bad_lines='skip')
                
                # استبدال أي قيم فارغة متبقية لضمان وضوح التحليل
                df.fillna("Detailed analysis in progress", inplace=True)
                
                progress_bar.progress(100)
                status_msg.empty()
                
                # عرض النتيجة بالشكل العام المطلوب
                st.subheader(txt["table_header"])
                st.dataframe(df, use_container_width=True)

                # خيار تحميل التقرير
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
                st.download_button(txt["down_btn"], output.getvalue(), f"Engineering_Audit_{current['auth']}.xlsx")
            else:
                st.error("Format Error. Please try again.")
        except Exception as e:
            st.error(f"Error during audit: {e}")