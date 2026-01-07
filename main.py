import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
from g4f.client import Client
import io
import time

# إعدادات الصفحة الاحترافية
st.set_page_config(page_title="UAE Federal Engineering Advisor", layout="wide", page_icon="🏗️")

# الجهات التنظيمية
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
    st.header("⚙️ الإعدادات الفيدرالية")
    selected_lang = st.radio("اللغة / Language", ["العربية", "English"])
    selected_emirate = st.selectbox("اختر الإمارة / Select Emirate", list(emirates_authorities.keys()))
    authority = emirates_authorities[selected_emirate]

# نصوص الواجهة
ui_text = {
    "العربية": {
        "title": "🏗️ المستشار الهندسي الذكي الشامل",
        "btn": "بدء التحليل الفني الكامل",
        "progress": "جاري معالجة البيانات...",
        "table_head": f"📊 التقرير التفصيلي - إمارة {selected_emirate}",
        "down_btn": "تحميل تقرير Excel التفصيلي"
    },
    "English": {
        "title": "🏗️ Full Smart Engineering Advisor",
        "btn": "Start Full Technical Analysis",
        "progress": "Processing Data...",
        "table_head": f"📊 Detailed Report - {selected_emirate}",
        "down_btn": "Download Detailed Excel Report"
    }
}
t = ui_text[selected_lang]

st.title(t["title"])

col1, col2 = st.columns(2)
with col1:
    specs_file = st.file_uploader("Specs PDF (المواصفات)", type=['pdf'])
with col2:
    offer_file = st.file_uploader("Offer PDF (العرض الفني)", type=['pdf'])

def extract_text(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    return "".join([page.get_text() for page in doc])

if st.button(t["btn"]):
    if specs_file and offer_file:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # 1. استخراج النصوص
        status_text.text("📖 جاري قراءة الملفات الهندسية..." if selected_lang == "العربية" else "Reading PDF Files...")
        specs_text = extract_text(specs_file)
        offer_text = extract_text(offer_file)
        progress_bar.progress(30)
        
        # 2. التحليل عبر الذكاء الاصطناعي
        status_text.text("🧠 جاري تحليل البنود والبحث عن البدائل والأسعار..." if selected_lang == "العربية" else "Analyzing Items & Searching Market...")
        
        client = Client()
        prompt = f"""
        Act as a Senior UAE Engineer. Match items between Specs and Offer.
        Return ONLY a CSV table (separator: ;) with 8 columns:
        1. Ref No (The Item Number/Name from Docs)
        2. Specs Requirement
        3. Offer Description
        4. Compliance Status (Match/Partial/No Match)
        5. Local Alternatives ({selected_emirate} Market)
        6. Estimated Price (AED)
        7. Technical Deviation
        8. Consultant Recommendation ({authority})
        
        Language: {selected_lang}.
        Data: Specs({specs_text[:6000]}) Offer({offer_text[:6000]})
        """
        
        try:
            response = client.chat.completions.create(model="", messages=[{"role": "user", "content": prompt}])
            res_data = response.choices[0].message.content
            progress_bar.progress(80)
            
            # 3. معالجة البيانات
            status_text.text("📊 جاري إعداد الجدول النهائي..." if selected_lang == "العربية" else "Preparing Final Table...")
            df = pd.read_csv(io.StringIO(res_data), sep=';')
            
            progress_bar.progress(100)
            status_text.success("✅ تم التحليل بنجاح!" if selected_lang == "العربية" else "Analysis Complete!")
            
            st.markdown(f"### {t['table_head']}")
            st.dataframe(df, use_container_width=True)

            # زر التحميل
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Full_Technical_Analysis')
            
            st.download_button(label=t["down_btn"], data=output.getvalue(), file_name=f"Detailed_Analysis_{selected_emirate}.xlsx")
            
        except Exception as e:
            st.error(f"Error during AI processing: {e}")
            progress_bar.empty()
    else:
        st.warning("Please upload both files.")