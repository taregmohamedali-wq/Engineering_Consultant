import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
from g4f.client import Client
import io

# إعدادات الصفحة
st.set_page_config(page_title="Engineering AI", layout="wide")

# خيار تبديل اللغة في الشريط الجانبي
language = st.sidebar.selectbox("Select Language / اختر اللغة", ["Arabic", "English"])

# قاموس النصوص للتبديل بين اللغات
text_content = {
    "Arabic": {
        "title": "🏗️ نظام التحليل الفني للمشاريع الهندسية",
        "sub": "قم برفع ملفات المواصفات والعروض للحصول على مقارنة شاملة",
        "spec_label": "تحميل ملف المواصفات (Specs)",
        "offer_label": "تحميل ملف العرض الفني (Offer)",
        "btn": "بدء التحليل الفني الشامل",
        "error": "يرجى رفع الملفين أولاً",
        "success": "تم التحليل بنجاح!",
        "loading": "جاري تحليل البيانات عبر الذكاء الاصطناعي...",
        "result_head": "📊 نتيجة المقارنة الفنية (6 أعمدة)"
    },
    "English": {
        "title": "🏗️ AI Engineering Technical Analysis",
        "sub": "Upload Specifications and Technical Offers for AI Comparison",
        "spec_label": "Upload Specs PDF",
        "offer_label": "Upload Offer PDF",
        "btn": "Start Technical Analysis",
        "error": "Please upload both files first",
        "success": "Analysis completed successfully!",
        "loading": "AI is analyzing data...",
        "result_head": "📊 Technical Comparison Results (6 Columns)"
    }
}

content = text_content[language]

st.title(content["title"])
st.write(content["sub"])

# واجهة رفع الملفات
col1, col2 = st.columns(2)
with col1:
    specs_file = st.file_uploader(content["spec_label"], type=['pdf'])
with col2:
    offer_file = st.file_uploader(content["offer_label"], type=['pdf'])

def extract_text(file):
    try:
        doc = fitz.open(stream=file.read(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return ""

if st.button(content["btn"]):
    if specs_file and offer_file:
        with st.spinner(content["loading"]):
            specs_text = extract_text(specs_file)[:5000]
            offer_text = extract_text(offer_file)[:5000]

            client = Client()
            # البرومبت يتغير حسب لغة الواجهة المختارة
            prompt_lang = "باللغة العربية" if language == "Arabic" else "in English"
            prompt = f"""
            Compare the Specs and Offer. Return a table with 6 columns: 
            (Item, Required Specs, Provided Description, Status, Deviations, Consultant Note).
            Language: {prompt_lang}.
            Specs: {specs_text}
            Offer: {offer_text}
            """
            
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}]
                )
                st.markdown(f"### {content['result_head']}")
                st.write(response.choices[0].message.content)
                st.success(content["success"])
            except Exception as e:
                st.error(f"AI Connection Error: {e}")
    else:
        st.error(content["error"])