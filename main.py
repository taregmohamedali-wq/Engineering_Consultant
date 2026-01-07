import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
from g4f.client import Client
import io

# 1. إعدادات الصفحة
st.set_page_config(page_title="UAE Engineering Auditor Pro", layout="wide", page_icon="🏗️")

# 2. قاموس الواجهة (تم تعديله لإظهار اسم الإمارة بوضوح)
lang_data = {
    "English": {
        "sidebar_title": "Control Panel",
        "lang_select": "Select Language",
        "region_label": "Project Location (Emirate)",
        "title": "🏗️ Technical Compliance & Gap Auditor",
        "run_btn": "🚀 Run Comprehensive Audit",
        "table_header": "Compliance, Gaps & Market Analysis Report",
        "down_btn": "📥 Download Excel Report"
    },
    "العربية": {
        "sidebar_title": "لوحة التحكم",
        "lang_select": "اختر اللغة",
        "region_label": "موقع المشروع (الإمارة)",
        "title": "🏗️ مدقق المطابقة الفنية وحصر النواقص الشامل",
        "run_btn": "🚀 بدء التدقيق الشامل",
        "table_header": "تقرير المطابقة، النواقص، وتحليل السوق التفصيلي",
        "down_btn": "📥 تحميل التقرير (Excel)"
    }
}

# 3. قاعدة بيانات البلديات
municipalities_db = {
    "Abu Dhabi (DMT & Estidama)": {"auth": "DMT - Abu Dhabi", "logic": "Abu Dhabi Codes"},
    "Dubai (Municipality & RTA)": {"auth": "Dubai Municipality", "logic": "Al Sa'fat System"},
    "Sharjah (Municipality)": {"auth": "Sharjah Municipality", "logic": "Sharjah Building Code"},
    "Other Emirates": {"auth": "UAE Local Municipality", "logic": "UAE General Code"}
}

# القائمة الجانبية
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/cb/Flag_of_the_United_Arab_Emirates.svg/255px-Flag_of_the_United_Arab_Emirates.svg.png", width=100)
    ui_lang = st.selectbox("Language / اللغة", ["العربية", "English"])
    txt = lang_data[ui_lang]
    st.divider()
    # هنا تم إصلاح اختفاء اسم الإمارة بإضافة عنوان واضح للخانية
    selected_region = st.selectbox(txt["region_label"], list(municipalities_db.keys()))
    current = municipalities_db[selected_region]
    st.success(f"Selected: {current['auth']}")

st.title(txt["title"])

col1, col2 = st.columns(2)
with col1:
    specs_file = st.file_uploader("Reference Specs (المواصفات)", type=['pdf'])
with col2:
    offer_file = st.file_uploader("Technical Offer (العرض الفني)", type=['pdf'])

def extract_text(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    return "".join([page.get_text() for page in doc])

# 4. التنفيذ
if st.button(txt["run_btn"]):
    if specs_file and offer_file:
        progress_bar = st.progress(0)
        specs_txt = extract_text(specs_file)[:15000]
        offer_txt = extract_text(offer_file)[:15000]
        progress_bar.progress(30)
        
        client = Client()
        
        # برومبت يضمن تعبئة كافة المعلومات وحذف Item_Ref
        prompt = f"""
        Act as a Senior UAE Engineering Auditor for {current['auth']}.
        Analyze Specs vs Offer. 
        
        MANDATORY:
        1. NO 'Item_Ref' column.
        2. Column 1: 'Clause_or_Spec_Name'.
        3. Column 2: 'Status' (Compliant / Non-Compliant / Missing in Offer).
        4. YOU MUST FILL ALL COLUMNS: 'Specs_Requirement', 'Offer_Response', 'Best_Alternatives_UAE', 'Price_Range_AED', 'AI_Municipality_Proposal'.
        5. Return ONLY a CSV table using (;) as separator.
        
        Language: {ui_lang}.
        """
        
        try:
            response = client.chat.completions.create(model="", messages=[{"role": "user", "content": f"{prompt}\nSpecs: {specs_txt}\nOffer: {offer_txt}"}])
            raw_data = response.choices[0].message.content
            
            if "Status" in raw_data:
                clean_csv = raw_data[raw_data.find("Clause_or_Spec_Name"):].strip()
                df = pd.read_csv(io.StringIO(clean_csv), sep=';', on_bad_lines='skip')
                
                progress_bar.progress(100)
                st.subheader(txt["table_header"])
                # عرض الجدول بالهيكلية المطلوبة
                st.dataframe(df, use_container_width=True)

                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
                st.download_button(txt["down_btn"], output.getvalue(), "Engineering_Audit_Report.xlsx")
            else:
                st.error("Error formatting table. Please try again.")
        except Exception as e:
            st.error(f"Error: {e}")