import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
from g4f.client import Client
import io

# إعدادات الصفحة الاحترافية
st.set_page_config(page_title="UAE Federal Engineering Advisor", layout="wide", page_icon="🏗️")

# قائمة الجهات التنظيمية حسب كل إمارة
emirates_authorities = {
    "Abu Dhabi": "DMT (Department of Municipalities and Transport) & Estidama",
    "Dubai": "Dubai Municipality (DM) & RTA Standards",
    "Sharjah": "Sharjah City Municipality & SEWA",
    "Ajman": "Ajman Municipality and Planning Department",
    "Umm Al Quwain": "UAQ Municipality",
    "Ras Al Khaimah": "RAK Municipality & Barjeel Standards",
    "Fujairah": "Fujairah Municipality"
}

# الشريط الجانبي للإعدادات الفيدرالية
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/cb/Flag_of_the_United_Arab_Emirates.svg/255px-Flag_of_the_United_Arab_Emirates.svg.png", width=100)
    st.header("⚙️ الإعدادات الفيدرالية")
    selected_lang = st.radio("اللغة / Language", ["العربية", "English"])
    selected_emirate = st.selectbox("اختر الإمارة / Select Emirate", list(emirates_authorities.keys()))
    authority = emirates_authorities[selected_emirate]
    st.info(f"الجهة التنظيمية: {authority}")

# نصوص الواجهة الموحدة
ui_text = {
    "العربية": {
        "title": f"🏗️ المستشار الهندسي الذكي - إمارة {selected_emirate}",
        "sub": f"مقارنة المواصفات والبحث عن بدائل وأسعار وفقاً لمعايير {authority}",
        "btn": "تحليل شامل والبحث في سوق الإمارات",
        "down_btn": "تحميل تقرير المقارنة والأسعار (Excel)",
        "loading": f"جاري الربط مع قواعد بيانات سوق {selected_emirate} والبحث عن البدائل...",
        "table_head": "📊 تقرير البدائل والأسعار التقديرية (درهم إماراتي)"
    },
    "English": {
        "title": f"🏗️ Smart Engineering Advisor - {selected_emirate}",
        "sub": f"Technical Analysis & Market Search per {authority} standards",
        "btn": "Full Analysis & UAE Market Search",
        "down_btn": "Download Comprehensive Report (Excel)",
        "loading": f"Connecting to {selected_emirate} market data and finding alternatives...",
        "table_head": "📊 Alternatives & Estimated Prices (AED)"
    }
}
t = ui_text[selected_lang]

st.title(t["title"])
st.subheader(t["sub"])

col1, col2 = st.columns(2)
with col1:
    specs_file = st.file_uploader("Specs PDF (المواصفات المطلوبة)", type=['pdf'])
with col2:
    offer_file = st.file_uploader("Offer PDF (العرض الفني المقدم)", type=['pdf'])

def extract_text(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    return "".join([page.get_text() for page in doc])

if st.button(t["btn"]):
    if specs_file and offer_file:
        with st.spinner(t["loading"]):
            specs_text = extract_text(specs_file)[:5000]
            offer_text = extract_text(offer_file)[:5000]

            client = Client()
            # برومبت فيدرالي يراعي خصوصية كل إمارة
            prompt = f"""
            You are a Senior UAE Engineering Consultant expert in {authority} regulations.
            Analyze the provided Specs vs Offer for a project in {selected_emirate}.
            For each material/technical item:
            1. Check compliance with {authority}.
            2. Propose 2 local alternatives available in the UAE market.
            3. Provide estimated unit price in AED based on recent UAE market trends.
            
            Return ONLY a CSV table (separator: ;).
            Columns: Item; Required Specs; Provided; Status; {selected_emirate} Market Alternatives; Est. Price (AED); Consultant Note ({authority}).
            Language: {selected_lang}.
            Context: Specs({specs_text}) Offer({offer_text})
            """

            try:
                response = client.chat.completions.create(model="", messages=[{"role": "user", "content": prompt}])
                res_data = response.choices[0].message.content

                df = pd.read_csv(io.StringIO(res_data), sep=';')
                st.markdown(f"### {t['table_head']}")
                st.dataframe(df, use_container_width=True)

                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name=f'{selected_emirate}_Analysis')
                
                st.download_button(label=t["down_btn"], data=output.getvalue(), file_name=f"UAE_Report_{selected_emirate}.xlsx")
            except Exception as e:
                st.error(f"Error: {e}")
    else:
        st.warning("يرجى تحميل الملفات أولاً")