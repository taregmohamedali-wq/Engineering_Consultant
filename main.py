import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
from g4f.client import Client
import io

# 1. Professional Page Configuration
st.set_page_config(page_title="UAE Engineering Auditor Pro", layout="wide", page_icon="🏗️")

# 2. Translation Dictionary / قاموس اللغات
lang_data = {
    "English": {
        "sidebar_title": "Settings",
        "lang_select": "Interface Language",
        "region_select": "Select Project Location",
        "title": "🏗️ UAE Smart Engineering Auditor Pro",
        "status_label": "Audit Mode",
        "standard_label": "Standard",
        "upload_specs": "1. Reference Specs (PDF)",
        "upload_offer": "2. Technical Offer (PDF)",
        "run_btn": "🚀 Start Comprehensive Audit",
        "extracting": "Reading engineering documents...",
        "auditing": "Auditing according to {auth}...",
        "success": "Audit Completed Successfully for {region}!",
        "table_header": "Detailed Compliance Report",
        "down_btn": "📥 Download Excel Report",
        "error_format": "Format Error: AI returned non-structured text. Please run again.",
        "warning_files": "Please upload both files."
    },
    "العربية": {
        "sidebar_title": "الإعدادات",
        "lang_select": "لغة الواجهة",
        "region_select": "اختر منطقة المشروع",
        "title": "🏗️ المستشار الهندسي الذكي - الإمارات",
        "status_label": "وضع التدقيق",
        "standard_label": "المعيار المتبع",
        "upload_specs": "1. ملف المواصفات المرجعي (PDF)",
        "upload_offer": "2. العرض الفني للفحص (PDF)",
        "run_btn": "🚀 بدء التدقيق الفني الشامل",
        "extracting": "جاري قراءة الملفات الهندسية...",
        "auditing": "جاري التدقيق وفقاً لمعايير {auth}...",
        "success": "تم التدقيق بنجاح لإمارة {region}!",
        "table_header": "تقرير المطابقة التفصيلي",
        "down_btn": "📥 تحميل تقرير Excel",
        "error_format": "خطأ في التنسيق: الذكاء الاصطناعي لم يرسل جدولاً منظماً. يرجى المحاولة مرة أخرى.",
        "warning_files": "يرجى رفع الملفين معاً."
    }
}

# 3. Municipality Standards Mapping
municipalities_specs = {
    "Abu Dhabi": {"auth": "DMT & Estidama", "logic": "Abu Dhabi International Building Code & Pearl Rating."},
    "Dubai": {"auth": "Dubai Municipality (DM)", "logic": "Al Sa'fat Green Building System & DM Standards."},
    "Sharjah": {"auth": "Sharjah Municipality", "logic": "Sharjah Building Code & SEWA Regulations."},
    "Other Emirates": {"auth": "Local Municipality", "logic": "UAE Fire & Life Safety Code."}
}

# 4. Sidebar for Language and Regional Control
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/cb/Flag_of_the_United_Arab_Emirates.svg/255px-Flag_of_the_United_Arab_Emirates.svg.png", width=120)
    
    # خيار تغيير اللغة
    ui_lang = st.selectbox("Language / اللغة", ["العربية", "English"])
    txt = lang_data[ui_lang]
    
    st.title(txt["sidebar_title"])
    selected_region = st.selectbox(txt["region_select"], list(municipalities_specs.keys()))
    current = municipalities_specs[selected_region]
    st.info(f"{txt['standard_label']}: {current['auth']}")

# 5. Main Interface
st.title(txt["title"])
st.markdown(f"**{txt['status_label']}:** {selected_region} | **{txt['standard_label']}:** {current['auth']}")

col1, col2 = st.columns(2)
with col1:
    specs_file = st.file_uploader(txt["upload_specs"], type=['pdf'])
with col2:
    offer_file = st.file_uploader(txt["upload_offer"], type=['pdf'])

def extract_text(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    return "".join([page.get_text() for page in doc])

# 6. Execution Logic
if st.button(txt["run_btn"]):
    if specs_file and offer_file:
        progress_bar = st.progress(0)
        status_msg = st.empty()
        
        # Text Extraction
        status_msg.text(txt["extracting"])
        specs_txt = extract_text(specs_file)[:10000]
        offer_txt = extract_text(offer_file)[:10000]
        progress_bar.progress(30)
        
        status_msg.text(txt["auditing"].format(auth=current['auth']))
        client = Client()
        
        # برومبت ذكي يتكيف مع اللغة المختارة
        prompt = f"""
        Act as a Senior UAE Engineering Auditor for {current['auth']}.
        Analyze Specs vs Offer. 
        MANDATORY: Return the result as a CLEAN CSV TABLE using the symbol (;) as the ONLY separator.
        DO NOT use any other separators like (|).
        
        Columns: Item_Ref; Specs_Requirement; Status; Best_Alternatives; Price_Range_AED; AI_Municipality_Proposal.
        
        Requirements:
        - Analyze for {selected_region} compliance.
        - Realistic Price Ranges in AED.
        - Language of report content: {ui_lang}.
        
        Specs: {specs_txt}
        Offer: {offer_txt}
        """
        
        try:
            response = client.chat.completions.create(model="", messages=[{"role": "user", "content": prompt}])
            raw_data = response.choices[0].message.content
            
            if "Item_Ref" in raw_data:
                clean_data = raw_data[raw_data.find("Item_Ref"):].replace('|', '').strip()
                df = pd.read_csv(io.StringIO(clean_data), sep=';', on_bad_lines='skip')
                
                progress_bar.progress(100)
                status_msg.success(txt["success"].format(region=selected_region))
                
                # 7. Display result in structured table
                st.subheader(f"{txt['table_header']} - {selected_region}")
                st.dataframe(df, use_container_width=True)

                # Export Logic
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Audit_Report')
                st.download_button(txt["down_btn"], output.getvalue(), f"Audit_{selected_region}.xlsx")
            else:
                st.error(txt["error_format"])
                
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.warning(txt["warning_files"])