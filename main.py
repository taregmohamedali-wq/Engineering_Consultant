import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
from g4f.client import Client
import io

# 1. إعدادات الصفحة (الحفاظ على الشكل العام)
st.set_page_config(page_title="UAE Engineering Auditor Pro", layout="wide", page_icon="🏗️")

# 2. قاموس الواجهة
lang_data = {
    "English": {
        "sidebar_title": "Control Panel",
        "region_label": "Project Location (Emirate)",
        "title": "🏗️ Full Technical Compliance & Clause Auditor",
        "run_btn": "🚀 Run Item-by-Item Audit",
        "table_header": "Detailed Clause-by-Clause Compliance Report",
        "down_btn": "📥 Download Full Audit (Excel)",
        "processing": "Auditing every single clause... Please wait."
    },
    "العربية": {
        "sidebar_title": "لوحة التحكم",
        "region_label": "موقع المشروع (الإمارة)",
        "title": "🏗️ مدقق المطابقة الفنية ومراجعة البنود الشامل",
        "run_btn": "🚀 بدء تدقيق البنود (بند بند)",
        "table_header": "تقرير مطابقة ومراجعة كافة البنود التفصيلي",
        "down_btn": "📥 تحميل التقرير الشامل (Excel)",
        "processing": "جاري مراجعة كل بند من المواصفات... يرجى الانتظار."
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
    st.info(f"📍 Standard Applied: {current['auth']}")

st.title(txt["title"])

col1, col2 = st.columns(2)
with col1:
    specs_file = st.file_uploader("1. Reference Specs (ملف المواصفات)", type=['pdf'])
with col2:
    offer_file = st.file_uploader("2. Technical Offer (العرض الفني)", type=['pdf'])

def extract_text(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    return "".join([page.get_text() for page in doc])

# 3. محرك المراجعة التفصيلية لكل بند
if st.button(txt["run_btn"]):
    if specs_file and offer_file:
        progress_bar = st.progress(0)
        status_msg = st.empty()
        
        status_msg.warning(txt["processing"])
        specs_txt = extract_text(specs_file)[:18000] # زيادة سعة القراءة للمراجعة الشاملة
        progress_bar.progress(30)
        
        offer_txt = extract_text(offer_file)[:15000]
        progress_bar.progress(60)
        
        client = Client()
        
        # برومبت يركز على رقم البند ومراجعة كل البنود بدون استثناء
        prompt = f"""
        Act as a Senior UAE Engineering Auditor.
        COMPARE Specs vs Offer MANDATORY Item-by-Item.

        ANALYSIS STEPS:
        1. Extract EVERY Clause Number (e.g., 260519, 1.1.2) and Title.
        2. Check if it exists in the Technical Offer.
        3. If missing, write 'MISSING / NOT PROVIDED' and provide a solution.
        4. Provide UAE Market Pricing and Recommendations for ALL items.

        COLUMNS (Strictly follow this order):
        Clause_No; Specs_Requirement; Offer_Response; Compliance_Status; Technical_Difference; Price_Range_AED; Recommendation.

        Format: Return ONLY a CSV table with (;) separator.
        NO 'N/A' - NO 'None'.
        Language: {ui_lang}.
        Standard: {current['auth']}.
        """
        
        try:
            response = client.chat.completions.create(model="", messages=[{"role": "user", "content": f"{prompt}\nSpecs: {specs_txt}\nOffer: {offer_txt}"}])
            raw_data = response.choices[0].message.content
            
            if "Clause_No" in raw_data:
                clean_csv = raw_data[raw_data.find("Clause_No"):].strip()
                df = pd.read_csv(io.StringIO(clean_csv), sep=';', on_bad_lines='skip')
                
                # ملء أي فراغات ناتجة عن التحليل لضمان وضوح التقرير
                df.fillna("Under Evaluation", inplace=True)
                
                progress_bar.progress(100)
                status_msg.success("Audit Completed Successfully!")
                
                # 4. عرض الجدول بالشكل العام المعتمد
                st.subheader(txt["table_header"])
                st.dataframe(df, use_container_width=True)

                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
                st.download_button(txt["down_btn"], output.getvalue(), "Engineering_Full_Audit.xlsx")
            else:
                st.error("Format Error: AI could not structure the clauses. Please try again.")
        except Exception as e:
            st.error(f"Error: {e}")