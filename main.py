import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
from g4f.client import Client
import g4f

# إعدادات الصفحة
st.set_page_config(page_title="AI Engineering Consultant", layout="wide")

# قاموس اللغات
text_content = {
    "العربية": {
        "title": "🏗️ المستشار الهندسي الذكي",
        "sub": "تحليل ومقارنة المواصفات الفنية بـ 6 أعمدة",
        "spec_label": "ملف المواصفات (PDF)",
        "offer_label": "ملف العرض الفني (PDF)",
        "btn": "بدء التحليل الفني",
        "loading": "جاري التحليل... قد يستغرق دقيقة",
        "result": "النتائج النهائية",
        "sidebar_head": "الإعدادات"
    },
    "English": {
        "title": "🏗️ Smart Engineering Consultant",
        "sub": "Technical Analysis & Comparison (6 Columns)",
        "spec_label": "Specifications File (PDF)",
        "offer_label": "Technical Offer File (PDF)",
        "btn": "Start Analysis",
        "loading": "Analyzing... please wait",
        "result": "Final Results",
        "sidebar_head": "Settings"
    }
}

# اختيار اللغة في الأعلى
selected_lang = st.radio("Language / اللغة", ["العربية", "English"], horizontal=True)
content = text_content[selected_lang]

st.title(content["title"])
st.subheader(content["sub"])

# رفع الملفات
col1, col2 = st.columns(2)
with col1:
    specs_file = st.file_uploader(content["spec_label"], type=['pdf'], key="specs")
with col2:
    offer_file = st.file_uploader(content["offer_label"], type=['pdf'], key="offer")

def extract_text(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    return "".join([page.get_text() for page in doc])[:4000]

if st.button(content["btn"]):
    if specs_file and offer_file:
        with st.spinner(content["loading"]):
            try:
                specs_text = extract_text(specs_file)
                offer_text = extract_text(offer_file)

                client = Client()
                # تعديل البرومبت ليجبر الذكاء الاصطناعي على استخدام الموديل المتاح
                prompt = f"""
                Act as a Senior Engineer. Compare:
                Specs: {specs_text}
                Offer: {offer_text}
                Return a table with 6 columns in {selected_lang}: 
                (Item, Required Specs, Provided Description, Status, Deviations, Consultant Note).
                """

                # استخدام موديل فارغ ليدع المكتبة تختار أفضل مزود متاح تلقائياً
                response = client.chat.completions.create(
                    model="", # ترك الموديل فارغاً يحل مشكلة الـ ModelNotFoundError
                    messages=[{"role": "user", "content": prompt}]
                )
                
                st.markdown(f"### {content['result']}")
                st.write(response.choices[0].message.content)
                
            except Exception as e:
                st.error(f"حدث خطأ في الاتصال: {str(e)}")
    else:
        st.warning("يرجى رفع الملفات")