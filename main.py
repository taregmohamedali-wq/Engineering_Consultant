import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
from g4f.client import Client
import io

# 1. إعدادات الصفحة والواجهة الاحترافية (نفس الثيم الداكن)
st.set_page_config(page_title="UAE Engineering Auditor Pro", layout="wide", page_icon="🏗️")

# 2. قاموس اللغات لضمان مرونة الواجهة
lang_data = {
    "English": {
        "sidebar_title": "Control Panel",
        "lang_select": "Interface Language",
        "region_select": "Project Location (Emirate)",
        "title": "🏗️ Full Technical Compliance Auditor",
        "run_btn": "🚀 Run Comprehensive Audit (All Clauses)",
        "success": "Full Audit Completed for {region}!",
        "table_header": "Comprehensive Compliance & Gap Analysis Report",
        "down_btn": "📥 Download Full Excel Report",
        "error": "Format Error: AI returned non-structured data. Please retry.",
        "warning": "Please upload both PDF files to start the gap analysis."
    },
    "العربية": {
        "sidebar_title": "لوحة التحكم",
        "lang_select": "لغة الواجهة",
        "region_select": "موقع المشروع (الإمارة)",
        "title": "🏗️ مدقق المطابقة الفنية وحصر النواقص الشامل",
        "run_btn": "🚀 بدء التدقيق الشامل (كافة البنود)",
        "success": "تم التدقيق وحصر النواقص بنجاح لإمارة {region}!",
        "table_header": "تقرير حصر المطابقة والنواقص المرجعي الشامل",
        "down_btn": "📥 تحميل التقرير الشامل (Excel)",
        "error": "خطأ في التنسيق: لم يتم استرداد الجدول بشكل صحيح. حاول مرة أخرى.",
        "warning": "يرجى رفع ملف المواصفات والعرض الفني معاً."
    }
}

# 3. معايير البلديات (تتغير بناءً على اختيارك)
municipalities_db = {
    "Abu Dhabi": {"auth": "DMT & Estidama", "std": "AD Building Codes", "focus": "Pearl Rating & Sustainability"},
    "Dubai": {"auth": "Dubai Municipality (DM)", "std": "Al Sa'fat Green Building", "focus": "DM Technical Standards & Safety"},
    "Sharjah": {"auth": "Sharjah Municipality", "std": "Sharjah Code & SEWA", "focus": "Electrical & Structural Compliance"},
    "Other Emirates": {"auth": "Local Authority", "std": "UAE Fire Safety Code", "focus": "General Engineering Standards"}
}

# 4. الشريط الجانبي (Sidebar)
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/cb/Flag_of_the_United_Arab_Emirates.svg/255px-Flag_of_the_United_Arab_Emirates.svg.png", width=120)
    ui_lang = st.selectbox("Language / اللغة", ["العربية", "English"])
    txt = lang_data[ui_lang]
    st.title(txt["sidebar_title"])
    selected_region = st.selectbox(txt["region_select"], list(municipalities_db.keys()))
    current = municipalities_db[selected_region]
    st.info(f"📍 {current['auth']}")

# 5. الواجهة الرئيسية وتحميل الملفات
st.title(txt["title"])
st.markdown(f"**Standard Applied:** {current['auth']} | **Specific Focus:** {current['focus']}")

col1, col2 = st.columns(2)
with col1:
    specs_file = st.file_uploader("1. Reference Specs (المواصفات)", type=['pdf'])
with col2:
    offer_file = st.file_uploader("2. Technical Offer (العرض الفني)", type=['pdf'])

def extract_text(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    return "".join([page.get_text() for page in doc])

# 6. منطق التدقيق الاحترافي
if st.button(txt["run_btn"]):
    if specs_file and offer_file:
        progress_bar = st.progress(0)
        status_msg = st.empty()
        
        # استخراج النصوص
        specs_txt = extract_text(specs_file)[:15000]
        offer_txt = extract_text(offer_file)[:15000]
        progress_bar.progress(30)
        
        client = Client()
        
        # البرومبت الصارم لضمان الشكل الجدولي وعدم تداخل النصوص
        prompt = f"""
        Act as a Senior UAE Engineering Auditor for {current['auth']}.
        TASK: Perform a 100% item-by-item audit.
        
        MANDATORY RULES:
        1. LIST EVERY CLAUSE FROM SPECS.
        2. IF AN ITEM IS IN SPECS BUT NOT IN OFFER, MARK STATUS AS 'MISSING'.
        3. IF IN OFFER BUT DIFFERENT, MARK AS 'NON-COMPLIANT'.
        4. IF MATCHING, MARK AS 'COMPLIANT'.
        5. RETURN ONLY A CSV TABLE USING (;) AS THE ONLY SEPARATOR.
        6. DO NOT USE (|) OR ANY MARKDOWN FORMATTING.

        COLUMNS ORDER:
        Item_Ref; Clause_No; Specs_Requirement; Offer_Response; Status; Best_Alternatives_UAE; Price_Range_AED; AI_Municipality_Proposal.

        Language of report: {ui_lang}.
        Specs: {specs_txt}
        Offer: {offer_txt}
        """
        
        try:
            response = client.chat.completions.create(model="", messages=[{"role": "user", "content": prompt}])
            raw_data = response.choices[0].message.content
            
            # معالجة البيانات لضمان ظهورها كجدول مقسم
            if "Item_Ref" in raw_data:
                # تنظيف أي رموز قد تسبب تداخل في الأعمدة
                clean_csv = raw_data[raw_data.find("Item_Ref"):].replace('|', '').strip()
                df = pd.read_csv(io.StringIO(clean_csv), sep=';', on_bad_lines='skip')
                
                progress_bar.progress(100)
                st.success(txt["success"].format(region=selected_region))
                
                # 7. عرض النتيجة النهائية بالتقسيم الجدولي الصحيح (نفس صورتك الأولى)
                st.subheader(txt["table_header"])
                st.dataframe(df, use_container_width=True)

                # خيار تحميل التقرير
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Audit_Report')
                st.download_button(txt["down_btn"], output.getvalue(), f"Full_Audit_{selected_region}.xlsx")
            else:
                st.error(txt["error"])
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.warning(txt["warning"])