import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
from g4f.client import Client
import io
import time

# 1. إعدادات الصفحة والواجهة الاحترافية
st.set_page_config(page_title="UAE Engineering Auditor Pro", layout="wide", page_icon="🏗️")

# 2. قاموس اللغات (تم إرجاع كافة الخانات وإصلاح المسميات)
lang_data = {
    "English": {
        "sidebar_title": "Control Panel",
        "region_label": "Project Location (Emirate)",
        "title": "🏗️ Comprehensive Technical Compliance Auditor",
        "run_btn": "🚀 Run Full Audit (Clause-by-Clause)",
        "table_header": "Complete Compliance, Gap & Pricing Analysis",
        "down_btn": "📥 Download Full Report (Excel)",
        "processing": "Auditing every clause... Please wait.",
        "success": "Full Audit Completed for {region}!"
    },
    "العربية": {
        "sidebar_title": "لوحة التحكم",
        "region_label": "موقع المشروع (الإمارة)",
        "title": "🏗️ مدقق المطابقة الفنية وحصر النواقص الشامل",
        "run_btn": "🚀 بدء التدقيق الشامل (بند مقابل بند)",
        "table_header": "تحليل المطابقة الكاملة، النواقص، والتسعير",
        "down_btn": "📥 تحميل التقرير الشامل (Excel)",
        "processing": "جاري تدقيق كافة البنود... يرجى الانتظار.",
        "success": "تم التدقيق الشامل بنجاح لإمارة {region}!"
    }
}

municipalities_db = {
    "Abu Dhabi (DMT & Estidama)": {"auth": "DMT Abu Dhabi", "std": "Estidama"},
    "Dubai (Municipality & RTA)": {"auth": "Dubai Municipality", "std": "Al Sa'fat"},
    "Sharjah (Municipality)": {"auth": "Sharjah Municipality", "std": "Sharjah Code"},
    "Other Emirates": {"auth": "Local Authority", "std": "UAE General Code"}
}

# القائمة الجانبية
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/cb/Flag_of_the_United_Arab_Emirates.svg/255px-Flag_of_the_United_Arab_Emirates.svg.png", width=100)
    ui_lang = st.selectbox("Language / اللغة", ["العربية", "English"])
    txt = lang_data[ui_lang]
    st.divider()
    selected_region = st.selectbox(txt["region_label"], list(municipalities_db.keys()))
    current = municipalities_db[selected_region]

st.title(txt["title"])

col1, col2 = st.columns(2)
with col1:
    specs_file = st.file_uploader("1. Reference Specs (المواصفات المرجعية)", type=['pdf'])
with col2:
    offer_file = st.file_uploader("2. Technical Offer (العرض الفني)", type=['pdf'])

def extract_text(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# 3. محرك التدقيق (يظهر كل شيء: مطابق، مختلف، مفقود)
if st.button(txt["run_btn"]):
    if specs_file and offer_file:
        # إظهار شريط التقدم كما طلبت
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text(txt["processing"])
        specs_txt = extract_text(specs_file)[:15000] 
        progress_bar.progress(20)
        
        offer_txt = extract_text(offer_file)[:15000]
        progress_bar.progress(40)
        
        client = Client()
        
        # برومبت يغطي (الموجود، الفرق، المفقود، السعر، والتوصية)
        prompt = f"""
        Act as a Senior UAE Engineering Auditor. 
        TASK: Compare EVERY clause in the Specs against the Offer.

        MANDATORY OUTPUT REQUIREMENTS:
        1. LIST EVERY ITEM from Specs.
        2. STATUS: Mark as 'Compliant' (if exists & matches), 'Partially Compliant' (if exists but differs), or 'Missing' (if not found).
        3. DIFFERENCE: If partially compliant, explain the exact difference.
        4. PRICE & ALTERNATIVES: Even if missing, provide estimated UAE market price and best alternatives.
        5. RECOMMENDATION: Provide a professional solution for gaps.
        
        COLUMNS:
        Clause_No; Specs_Requirement; Offer_Status; Status_Detail; Best_Alternatives_UAE; Price_Range_AED; Recommended_Action.

        Separator: (;)
        Language: {ui_lang}.
        """
        
        try:
            progress_bar.progress(60)
            response = client.chat.completions.create(model="", messages=[{"role": "user", "content": f"{prompt}\nSpecs: {specs_txt}\nOffer: {offer_txt}"}])
            raw_data = response.choices[0].message.content
            
            progress_bar.progress(90)
            
            if "Clause_No" in raw_data:
                clean_csv = raw_data[raw_data.find("Clause_No"):].replace('|', '').strip()
                df = pd.read_csv(io.StringIO(clean_csv), sep=';', on_bad_lines='skip')
                
                # إكمال شريط التقدم
                progress_bar.progress(100)
                time.sleep(0.5)
                progress_bar.empty() # إخفاء الشريط بعد النجاح
                
                st.success(txt["success"].format(region=selected_region))
                
                # 4. عرض التقرير الشامل
                st.subheader(txt["table_header"])
                st.dataframe(df, use_container_width=True)

                # تحميل إكسل
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
                st.download_button(txt["down_btn"], output.getvalue(), "Comprehensive_Audit_Report.xlsx")
            else:
                st.error("Error processing table. Ensure PDFs are not images.")
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.warning("Please upload both files.")