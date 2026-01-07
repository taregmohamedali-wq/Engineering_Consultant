import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
from g4f.client import Client
import io

# 1. إعدادات الصفحة
st.set_page_config(page_title="UAE Engineering Auditor Pro", layout="wide", page_icon="🏗️")

# 2. قاموس اللغات
lang_data = {
    "English": {
        "sidebar_title": "Settings",
        "lang_select": "Interface Language",
        "region_select": "Project Location",
        "title": "🏗️ Full Technical Compliance Auditor",
        "run_btn": "🚀 Run Full Audit (All Clauses)",
        "success": "Full Audit Completed for {region}!",
        "table_header": "Comprehensive Compliance & Gap Analysis Report",
        "down_btn": "📥 Download Full Report (Excel)"
    },
    "العربية": {
        "sidebar_title": "الإعدادات",
        "lang_select": "لغة الواجهة",
        "region_select": "منطقة المشروع",
        "title": "🏗️ مدقق المطابقة الفنية الشامل",
        "run_btn": "🚀 تشغيل التدقيق الكامل (كافة البنود)",
        "success": "تم الانتهاء من التدقيق الشامل لإمارة {region}!",
        "table_header": "تقرير حصر المطابقة والنواقص الشامل",
        "down_btn": "📥 تحميل التقرير الشامل (Excel)"
    }
}

municipalities_db = {
    "Abu Dhabi": {"auth": "DMT & Estidama", "logic": "DMT Standards"},
    "Dubai": {"auth": "Dubai Municipality (DM)", "logic": "DM Al Sa'fat"},
    "Sharjah": {"auth": "Sharjah Municipality", "logic": "Sharjah Code"},
    "Other Emirates": {"auth": "Local Authority", "logic": "UAE Fire Safety"}
}

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/cb/Flag_of_the_United_Arab_Emirates.svg/255px-Flag_of_the_United_Arab_Emirates.svg.png", width=120)
    ui_lang = st.selectbox("Language / اللغة", ["العربية", "English"])
    txt = lang_data[ui_lang]
    selected_region = st.selectbox(txt["region_select"], list(municipalities_db.keys()))
    current_spec = municipalities_db[selected_region]

st.title(txt["title"])

col1, col2 = st.columns(2)
with col1:
    specs_file = st.file_uploader("Specs (المواصفات المرجعية)", type=['pdf'])
with col2:
    offer_file = st.file_uploader("Offer (العرض الفني للفحص)", type=['pdf'])

def extract_text(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    return "".join([page.get_text() for page in doc])

if st.button(txt["run_btn"]):
    if specs_file and offer_file:
        progress_bar = st.progress(0)
        
        # استخراج النصوص بحجم أكبر لضمان الشمولية
        specs_txt = extract_text(specs_file)[:15000]
        offer_txt = extract_text(offer_file)[:15000]
        progress_bar.progress(30)
        
        client = Client()
        
        # برومبت صارم لاسترجاع كافة البنود وتبيين المطابقة
        prompt = f"""
        Act as a Senior UAE Engineering Auditor. 
        TASK: Compare every clause in the 'Specs' against the 'Offer'.
        
        MANDATORY OUTPUT RULES:
        1. YOU MUST LIST EVERY ITEM FOUND IN THE SPECS.
        2. FOR EACH ITEM, CLEARLY STATE IF IT IS: 'Compliant', 'Non-Compliant', or 'Missing'.
        3. Use (;) as the ONLY separator for CSV.
        
        COLUMNS:
        Item_Ref; Clause_No; Specs_Requirement; Offer_Response; Status; Best_Alternatives_UAE; Price_Range_AED; AI_Municipality_Proposal.

        Language: {ui_lang}.
        Municipality: {current_spec['auth']}.
        Specs: {specs_txt}
        Offer: {offer_txt}
        """
        
        try:
            response = client.chat.completions.create(model="", messages=[{"role": "user", "content": prompt}])
            raw_data = response.choices[0].message.content
            
            if "Item_Ref" in raw_data:
                clean_csv = raw_data[raw_data.find("Item_Ref"):].replace('|', '').strip()
                df = pd.read_csv(io.StringIO(clean_csv), sep=';', on_bad_lines='skip')
                
                progress_bar.progress(100)
                st.success(txt["success"].format(region=selected_region))
                
                # عرض النتيجة
                st.subheader(txt["table_header"])
                st.dataframe(df, use_container_width=True)

                # التصدير
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Audit_Report')
                st.download_button(txt["down_btn"], output.getvalue(), f"Full_Compliance_Audit.xlsx")
            else:
                st.error("Error in data processing. Try again.")
        except Exception as e:
            st.error(f"Error: {e}")