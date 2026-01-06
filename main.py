import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
from g4f.client import Client
import io

# إعدادات الصفحة
st.set_page_config(page_title="المستشار الهندسي الذكي", layout="wide")

st.title("🏗️ نظام التحليل الفني للمشاريع الهندسية")
st.write("قم برفع ملفات المواصفات والعروض للحصول على مقارنة شاملة عبر الذكاء الاصطناعي")

# واجهة رفع الملفات
col1, col2 = st.columns(2)
with col1:
    specs_file = st.file_uploader("تحميل ملف المواصفات (Specs)", type=['pdf'])
with col2:
    offer_file = st.file_uploader("تحميل ملف العرض الفني (Offer)", type=['pdf'])

def extract_text(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

if st.button("بدء التحليل الفني الشامل"):
    if specs_file and offer_file:
        with st.spinner("جاري تحليل البيانات..."):
            # استخراج النصوص
            specs_text = extract_text(specs_file)[:4000] # تحديد جزء للسرعة
            offer_text = extract_text(offer_file)[:4000]

            # طلب التحليل من الذكاء الاصطناعي
            client = Client()
            prompt = f"""
            بصفتك مستشار هندسي، قارن بين المواصفة المطلوبة والعرض المقدم.
            المواصفات: {specs_text}
            العرض: {offer_text}
            أريد النتيجة في جدول يحتوي على: (البند، المواصفة المطلوبة، الوصف المقدم، الحالة، الفوارق، ملاحظة المستشار).
            استخرج أهم 5 بنود فنية.
            """
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            
            result_text = response.choices[0].message.content
            st.markdown("### 📊 نتيجة المقارنة الفنية")
            st.write(result_text)
            
            # زر لتحميل النتائج (تحتاج لإضافة منطق تحويل النص لجدول Excel هنا)
            st.success("تم التحليل بنجاح!")
    else:
        st.error("يرجى رفع الملفين أولاً")