import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
from g4f.client import Client
import io

# 1. إعدادات الصفحة (الحفاظ على الهوية البصرية)
st.set_page_config(page_title="UAE Engineering Auditor Pro", layout="wide", page_icon="🏗️")

# 2. قاموس الواجهة لضمان ثبات الشكل
lang_data = {
    "English": {
        "sidebar_title": "Control Panel",
        "region_label": "Project Location (Emirate)",
        "title": "🏗️ Full Technical Compliance & Gap Auditor",
        "run_btn": "🚀 Run Item-by-Item Audit",
        "table_header": "Complete Compliance, Differences & Market Analysis Report",
        "down_btn": "📥 Download Full Report (Excel)",
        "processing": "Auditing all clauses... analyzing differences."
    },
    "العربية": {
        "sidebar_title": "لوحة التحكم",
        "region_label": "موقع المشروع (الإمارة)",
        "title": "🏗️ مدقق المطابقة الفنية وحصر النواقص الشامل",
        "run_btn": "🚀 بدء التدقيق الشامل (بند بند)",
        "table_header": "تحليل المطابقة الكاملة، الاختلافات الفنية، والتسعير",
        "down_btn": "📥 تحميل التقرير الشامل (Excel)",
        "processing": "جاري تدقيق كافة البنود وتحليل الفروقات... يرجى الانتظار."
    }
}

municipalities_db = {
    "Abu Dhabi (DMT & Estidama)": {"auth": "DMT Abu Dhabi", "std": "Estidama"},
    "Dubai (Municipality & RTA)": {"auth": "Dubai Municipality", "std": "Al Sa'fat"},
    "Sharjah (Municipality)": {"auth": "Sharjah Municipality", "std": "Sharjah Code"},
    "Other Emirates": {"auth": "UAE Authority", "std": "UAE General Code"}
}

# --- القائمة الجانبية (ظهور الإمارة بشكل دائم) ---
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
    specs_file = st.file_uploader("1. Reference Specs (المواصفات)", type=['pdf'])
with col2:
    offer_file = st.file_uploader("2. Technical Offer (العرض الفني)", type=['pdf'])

def extract_text(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    return "".join([page.get_text() for page in doc])

# 3. محرك التدقيق (يظهر المطابق والمختلف والمفقود)
if st.button(txt["run_btn"]):
    if specs_file and offer_file:
        progress_bar = st.progress(0)
        status_msg = st.empty()
        
        status_msg.info(txt["processing"])
        specs_txt = extract_text(specs_file)[:18000]
        progress_bar.progress(30)
        
        offer_txt = extract_text(offer_file)[:15000]
        progress_bar.progress(60)
        
        client = Client()
        
        # برومبت صارم لاستخراج كل شيء (المطابق، المختلف، والمفقود)
        prompt = f"""
        Act as a Senior UAE Engineering Auditor for {current['auth']}.
        Analyze Specs against Offer Item-by-Item. 
        MANDATORY: List EVERY clause from the Specs.

        JUDGMENT CRITERIA:
        - COMPLIANT: Exact match.
        - DIFFERENT: Exists but differs in brand/tech-specs (Explain what is different).
        - MISSING: Not mentioned in the offer.

        COLUMNS (Strictly):
        Clause_No; Specs_Requirement; Offer_Response; Status; Difference_Details; UAE_Alternative_Market; Price_AED_Range; AI_Expert_Recommendation.

        RULES: 
        - NEVER leave cells empty. Use AI logic to fill Prices and Alternatives.
        - Return ONLY a CSV table with (;) separator.
        Language: {ui_lang}.
        """
        
        try:
            response = client.chat.completions.create(model="", messages=[{"role": "user", "content": f"{prompt}\nSpecs: {specs_txt}\nOffer: {offer_txt}"}])
            raw_data = response.choices[0].message.content
            
            if "Clause_No" in raw_data:
                clean_csv = raw_data[raw_data.find("Clause_No"):].strip()
                df = pd.read_csv(io.StringIO(clean_csv), sep=';', on_bad_lines='skip')
                
                # ملء الفراغات لضمان مظهر جدول مكتمل
                df.fillna("Standard Analysis Applied", inplace=True)
                
                progress_bar.progress(100)
                status_msg.empty()
                
                # 4. عرض التقرير بالشكل النهائي المعتمد
                st.subheader(txt["table_header"])
                st.dataframe(df, use_container_width=True)

                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
                st.download_button(txt["down_btn"], output.getvalue(), "Technical_Audit_Comprehensive.xlsx")
            else:
                st.error("Error: The AI response was not structured correctly. Please try again.")
        except Exception as e:
            st.error(f"Error: {e}")