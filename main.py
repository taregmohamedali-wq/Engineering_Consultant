import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
from g4f.client import Client
import io

# إعدادات الصفحة
st.set_page_config(page_title="AI Engineering Consultant", layout="wide")

# اختيار اللغة
selected_lang = st.radio("Language / اللغة", ["العربية", "English"], horizontal=True)

# نصوص الواجهة
ui_text = {
    "العربية": {
        "title": "🏗️ المستشار الهندسي الشامل",
        "sub": "تحليل كامل لجميع البنود مع إمكانية استخراج Excel",
        "btn": "بدء التحليل الشامل",
        "down_btn": "تحميل ملف Excel",
        "loading": "جاري تحليل كافة البنود... قد يستغرق الأمر بعض الوقت",
        "done": "تم التحليل بنجاح!"
    },
    "English": {
        "title": "🏗️ Full Engineering Consultant",
        "sub": "Full items analysis with Excel export",
        "btn": "Start Full Analysis",
        "down_btn": "Download Excel File",
        "loading": "Analyzing all items... please wait",
        "done": "Analysis completed!"
    }
}
t = ui_text[selected_lang]

st.title(t["title"])
st.subheader(t["sub"])

col1, col2 = st.columns(2)
with col1:
    specs_file = st.file_uploader("Specs PDF", type=['pdf'])
with col2:
    offer_file = st.file_uploader("Offer PDF", type=['pdf'])

def extract_text(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    return "".join([page.get_text() for page in doc])

if st.button(t["btn"]):
    if specs_file and offer_file:
        with st.spinner(t["loading"]):
            specs_text = extract_text(specs_file)
            offer_text = extract_text(offer_file)

            client = Client()
            # تعديل البرومبت ليحلل كل شيء ويرد بصيغة CSV ليسهل تحويلها
            prompt = f"""
            Analyze ALL technical items between these two documents.
            Return the result ONLY as a CSV formatted table using (;) as separator.
            Columns: Item; Required Specs; Provided Description; Status; Deviations; Consultant Note.
            Language: {selected_lang}.
            Docs: Specs({specs_text[:5000]}), Offer({offer_text[:5000]})
            """

            response = client.chat.completions.create(model="", messages=[{"role": "user", "content": prompt}])
            res_data = response.choices[0].message.content

            # عرض النتائج في الموقع
            st.markdown("### 📊 النتائج المستخرجة")
            
            try:
                # تحويل النص المستلم إلى DataFrame
                df = pd.read_csv(io.StringIO(res_data), sep=';')
                st.table(df)

                # إنشاء ملف Excel في الذاكرة للتحميل
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Technical_Analysis')
                
                st.download_button(
                    label=t["down_btn"],
                    data=output.getvalue(),
                    file_name="Engineering_Analysis.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                st.success(t["done"])
            except:
                st.write(res_data)
                st.warning("تم استخراج النص، ولكن تعذر تحويله لجدول تلقائي. يمكنك نسخه يدوياً.")
    else:
        st.error("Missing files!")