import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
from g4f.client import Client
import io

# 1. إعدادات الصفحة الاحترافية
st.set_page_config(page_title="UAE Engineering Auditor Pro", layout="wide", page_icon="🏗️")

# 2. قاموس اللغات والواجهة
lang_data = {
    "English": {
        "sidebar_title": "Settings",
        "lang_select": "Interface Language",
        "region_select": "Select Project Location",
        "title": "🏗️ UAE Smart Engineering Auditor Pro",
        "status_label": "Audit Mode",
        "standard_label": "Authority Standard",
        "upload_specs": "1. Reference Specs (PDF)",
        "upload_offer": "2. Technical Offer (PDF)",
        "run_btn": "🚀 Start Full Audit & Gap Analysis",
        "extracting": "Scanning pages for all specs and missing gaps...",
        "auditing": "Consulting {auth} standards for compliance...",
        "success": "Full Audit & Gap Analysis Completed for {region}!",
        "table_header": "Detailed Compliance, Gaps & Pricing Report",
        "down_btn": "📥 Download Comprehensive Excel Report",
        "error_format": "Data structure error. Please try running the audit again.",
        "warning_files": "Please upload both PDF files to start the check."
    },
    "العربية": {
        "sidebar_title": "الإعدادات",
        "lang_select": "لغة الواجهة",
        "region_select": "اختر منطقة المشروع",
        "title": "🏗️ المستشار الهندسي الذكي - الإصدار الشامل",
        "status_label": "وضع التدقيق",
        "standard_label": "المعيار المعتمد",
        "upload_specs": "1. ملف المواصفات المرجعي (PDF)",
        "upload_offer": "2. العرض الفني للفحص (PDF)",
        "run_btn": "🚀 بدء التدقيق الشامل وحصر النواقص",
        "extracting": "جاري فحص الصفحات واستخراج البنود والفجوات...",
        "auditing": "جاري التدقيق وفقاً لاشتراطات {auth}...",
        "success": "تم التدقيق وحصر النواقص والأسعار بنجاح لإمارة {region}!",
        "table_header": "تقرير المطابقة، النواقص، والتسعير التفصيلي",
        "down_btn": "📥 تحميل التقرير الهندسي الشامل (Excel)",
        "error_format": "خطأ في تنظيم البيانات. يرجى إعادة محاولة التدقيق.",
        "warning_files": "يرجى رفع الملفات المطلوبة أولاً."
    }
}

# 3. قاعدة بيانات البلديات والمعايير (حسب المنطقة المختارة)
municipalities_db = {
    "Abu Dhabi": {
        "auth": "DMT (Dept. of Municipalities and Transport)",
        "std": "Estidama & AD International Building Codes",
        "focus": "Focus on Estidama Pearl Rating and Pearl Qualified Materials."
    },
    "Dubai": {
        "auth": "Dubai Municipality (DM)",
        "std": "Al Sa'fat Green Building System & DCD Safety",
        "focus": "Focus on Al Sa'fat compliance and DM technical circulars."
    },
    "Sharjah": {
        "auth": "Sharjah City Municipality",
        "std": "Sharjah Building Code & SEWA standards",
        "focus": "Focus on SEWA electrical requirements and municipality approvals."
    },
    "Ras Al Khaimah": {
        "auth": "RAK Municipality",
        "std": "Barjeel Green Building Code",
        "focus": "Focus on Barjeel energy efficiency and thermal insulation."
    },
    "Other Emirates": {
        "auth": "Local Municipality / Civil Defense",
        "std": "UAE Fire & Life Safety Code",
        "focus": "Focus on General Safety and UAE Building Codes."
    }
}

# 4. الشريط الجانبي (Sidebar)
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/cb/Flag_of_the_United_Arab_Emirates.svg/255px-Flag_of_the_United_Arab_Emirates.svg.png", width=120)
    ui_lang = st.selectbox("Language / اللغة", ["العربية", "English"])
    txt = lang_data[ui_lang]
    st.title(txt["sidebar_title"])
    selected_region = st.selectbox(txt["region_select"], list(municipalities_db.keys()))
    current_spec = municipalities_db[selected_region]
    st.success(f"📍 {txt['status_label']}: {selected_region}")
    st.info(f"📜 {txt['standard_label']}: {current_spec['auth']}")

# 5. الواجهة الرئيسية
st.title(txt["title"])
st.markdown(f"**Applied Standard:** {current_spec['auth']} ({current_spec['std']})")

col1, col2 = st.columns(2)
with col1:
    specs_file = st.file_uploader(txt["upload_specs"], type=['pdf'])
with col2:
    offer_file = st.file_uploader(txt["upload_offer"], type=['pdf'])

def extract_text(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    return "".join([page.get_text() for page in doc])

# 6. منطق التدقيق وحصر النواقص والأسعار
if st.button(txt["run_btn"]):
    if specs_file and offer_file:
        progress_bar = st.progress(0)
        status_msg = st.empty()
        
        status_msg.text(txt["extracting"])
        specs_txt = extract_text(specs_file)[:12000]
        offer_txt = extract_text(offer_file)[:12000]
        progress_bar.progress(30)
        
        status_msg.text(txt["auditing"].format(auth=current_spec['auth']))
        client = Client()
        
        # البرومبت الاحترافي الشامل لجميع طلباتك
        prompt = f"""
        Act as a Senior UAE Technical Consultant for {current_spec['auth']}.
        Focus on {current_spec['std']} and {current_spec['focus']}.
        
        MANDATORY TASK:
        1. List EVERY requirement from 'Specs'.
        2. Identify GAPS: If an item is in Specs but not in Offer, mark as 'MISSING'.
        3. Identify NON-COMPLIANCE: If it differs from {current_spec['auth']} standards.
        4. Provide 2 Best UAE Alternatives for each item.
        5. Provide a realistic Price Range in AED (e.g. 10,000 - 15,000).
        6. AI Proposal: Give a specific advice based on {selected_region} local laws.
        
        OUTPUT FORMAT: Return ONLY a CSV table using (;) as a separator. 
        COLUMNS: Item_Ref; Specs_Requirement; Status; Best_Alternatives_UAE; Price_Range_AED; AI_Municipality_Proposal.
        
        Language: {ui_lang}.
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
                status_msg.success(txt["success"].format(region=selected_region))
                
                # 7. عرض الجدول المنظم (نفس شكل الصورة الأولى)
                st.subheader(f"{txt['table_header']} - {selected_region}")
                st.dataframe(df, use_container_width=True)

                # تصدير الملف
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Final_Audit_Report')
                st.download_button(txt["down_btn"], output.getvalue(), f"Full_Audit_{selected_region}.xlsx")
            else:
                st.error(txt["error_format"])
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.warning(txt["warning_files"])