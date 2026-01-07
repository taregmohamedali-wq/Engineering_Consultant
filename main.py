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
        "sidebar_title": "Control Panel",
        "lang_select": "Language",
        "region_select": "Project Emirate",
        "title": "🏗️ Full Technical Compliance Auditor",
        "run_btn": "🚀 Run Comprehensive Audit",
        "success": "Audit Completed for {region}!",
        "table_header": "Detailed Compliance, Gaps & Pricing Report",
        "down_btn": "📥 Download Excel Report"
    },
    "العربية": {
        "sidebar_title": "لوحة التحكم",
        "lang_select": "اللغة",
        "region_select": "إمارة المشروع",
        "title": "🏗️ مدقق المطابقة الفنية وحصر النواقص",
        "run_btn": "🚀 بدء التدقيق الشامل",
        "success": "تم التدقيق بنجاح لإمارة {region}!",
        "table_header": "تقرير المطابقة، النواقص، والتسعير التفصيلي",
        "down_btn": "📥 تحميل التقرير (Excel)"
    }
}

municipalities_db = {
    "Abu Dhabi": {"auth": "DMT & Estidama"},
    "Dubai": {"auth": "Dubai Municipality (DM)"},
    "Sharjah": {"auth": "Sharjah Municipality"},
    "Other Emirates": {"auth": "Local Authority"}
}

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/cb/Flag_of_the_United_Arab_Emirates.svg/255px-Flag_of_the_United_Arab_Emirates.svg.png", width=100)
    ui_lang = st.selectbox("Language / اللغة", ["العربية", "English"])
    txt = lang_data[ui_lang]
    selected_region = st.selectbox(txt["region_select"], list(municipalities_db.keys()))
    current = municipalities_db[selected_region]

st.title(txt["title"])

col1, col2 = st.columns(2)
with col1:
    specs_file = st.file_uploader("1. Specs (المواصفات)", type=['pdf'])
with col2:
    offer_file = st.file_uploader("2. Technical Offer (العرض الفني)", type=['pdf'])

def extract_text(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    return "".join([page.get_text() for page in doc])

# 3. معالجة البيانات والتدقيق
if st.button(txt["run_btn"]):
    if specs_file and offer_file:
        progress_bar = st.progress(0)
        
        specs_txt = extract_text(specs_file)[:12000]
        offer_txt = extract_text(offer_file)[:12000]
        progress_bar.progress(30)
        
        client = Client()
        
        # البرومبت المحدث لضمان تعبئة كافة الخانات وحذف Item_Ref
        prompt = f"""
        Act as a Senior UAE Engineering Auditor for {current['auth']}.
        Analyze Specs vs Offer. 
        
        MANDATORY: 
        - Return ONLY a CSV table using (;) as separator.
        - DO NOT include Item_Ref column.
        - YOU MUST PROVIDE REAL VALUES for 'Best_Alternatives_UAE', 'Price_Range_AED', and 'AI_Municipality_Proposal'. DO NOT LEAVE THEM EMPTY OR 'None'.
        
        COLUMNS IN ORDER:
        Clause_No; Specs_Requirement; Offer_Response; Status; Best_Alternatives_UAE; Price_Range_AED; AI_Municipality_Proposal.

        Language of report: {ui_lang}.
        Specs: {specs_txt}
        Offer: {offer_txt}
        """
        
        try:
            response = client.chat.completions.create(model="", messages=[{"role": "user", "content": prompt}])
            raw_data = response.choices[0].message.content
            
            if "Clause_No" in raw_data:
                # تنظيف البيانات وتحويلها لجدول
                clean_csv = raw_data[raw_data.find("Clause_No"):].replace('|', '').strip()
                df = pd.read_csv(io.StringIO(clean_csv), sep=';', on_bad_lines='skip')
                
                # التأكد من حذف عمود Item_Ref إذا وجد بالخطأ
                if 'Item_Ref' in df.columns:
                    df = df.drop(columns=['Item_Ref'])
                
                progress_bar.progress(100)
                st.success(txt["success"].format(region=selected_region))
                
                # عرض النتيجة النهائية بالترتيب المطلوب
                st.subheader(txt["table_header"])
                st.dataframe(df, use_container_width=True)

                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
                st.download_button(txt["down_btn"], output.getvalue(), f"Full_Audit_{selected_region}.xlsx")
            else:
                st.error("Format Error. Please retry.")
        except Exception as e:
            st.error(f"Error: {e}")