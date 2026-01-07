import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
from g4f.client import Client
import io

# إعدادات الصفحة
st.set_page_config(page_title="UAE Comprehensive Engineering Audit", layout="wide", page_icon="📝")

# الجهات التنظيمية حسب الإمارة
emirates_authorities = {
    "Abu Dhabi": "DMT & Estidama",
    "Dubai": "Dubai Municipality & RTA",
    "Sharjah": "Sharjah Municipality & SEWA",
    "Ajman": "Ajman Municipality",
    "Umm Al Quwain": "UAQ Municipality",
    "Ras Al Khaimah": "RAK Municipality & Barjeel",
    "Fujairah": "Fujairah Municipality"
}

with st.sidebar:
    st.header("⚙️ إعدادات التدقيق الفني")
    selected_lang = st.radio("اللغة / Language", ["العربية", "English"])
    selected_emirate = st.selectbox("إمارة المشروع", list(emirates_authorities.keys()))
    authority = emirates_authorities[selected_emirate]

# نصوص الواجهة
ui_text = {
    "العربية": {
        "title": "🏗️ نظام التدقيق الهندسي الشامل (حصر المطابقة)",
        "sub": "مقارنة كافة البنود - بما فيها الناقصة وغير المطابقة",
        "btn": "بدء التدقيق الشامل لكافة الصفحات",
        "loading": "جاري فحص كل سطر في المواصفات ومطابقته مع العرض...",
        "down_btn": "تحميل تقرير التدقيق النهائي (Excel)"
    },
    "English": {
        "title": "🏗️ Comprehensive Engineering Audit System",
        "sub": "Matching ALL items - including missing and non-compliant ones",
        "btn": "Start Full Audit of All Pages",
        "loading": "Auditing every line in specs vs offer...",
        "down_btn": "Download Final Audit Report (Excel)"
    }
}
t = ui_text[selected_lang]

st.title(t["title"])
st.subheader(t["sub"])

col1, col2 = st.columns(2)
with col1:
    specs_file = st.file_uploader("ملف المواصفات (المرجع)", type=['pdf'])
with col2:
    offer_file = st.file_uploader("ملف العرض الفني (للفحص)", type=['pdf'])

def extract_text(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    return "".join([page.get_text() for page in doc])

if st.button(t["btn"]):
    if specs_file and offer_file:
        progress_bar = st.progress(0)
        
        # استخراج النص بالكامل
        specs_text = extract_text(specs_file)
        offer_text = extract_text(offer_file)
        progress_bar.progress(30)
        
        client = Client()
        # برومبت صارم لضمان عدم إهمال أي بند
        prompt = f"""
        Instructions for UAE Engineering Auditor:
        1. List EVERY single technical item/section found in the 'Specs'.
        2. Match it with the 'Offer'.
        3. If an item exists in Specs but NOT in Offer, mark Status as 'MISSING/NOT PROVIDED'.
        4. If it exists but differs, mark as 'NON-COMPLIANT'.
        5. For each item, suggest a local UAE alternative and estimated price in AED.
        
        Format: ONLY a CSV table (separator: ;)
        Columns: Item Ref; Spec Requirement; Offer Response; Status (Compliant/Non-Compliant/Missing); Local Alternatives; Est. Price (AED); Auditor's Technical Comment ({authority}).
        
        Language: {selected_lang}.
        Specs Data: {specs_text[:7000]}
        Offer Data: {offer_text[:7000]}
        """
        
        with st.spinner(t["loading"]):
            try:
                response = client.chat.completions.create(model="", messages=[{"role": "user", "content": prompt}])
                res_data = response.choices[0].message.content
                progress_bar.progress(80)
                
                df = pd.read_csv(io.StringIO(res_data), sep=';')
                progress_bar.progress(100)
                
                st.markdown("### 📊 نتيجة التدقيق الفني والحصر")
                # تلوين الجدول (اختياري بصرياً)
                st.dataframe(df, use_container_width=True)

                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Audit_Report')
                
                st.download_button(label=t["down_btn"], data=output.getvalue(), file_name=f"Full_Audit_{selected_emirate}.xlsx")
                
            except Exception as e:
                st.error(f"حدث خطأ أثناء التحليل: {e}")
    else:
        st.warning("الرجاء رفع الملفات")