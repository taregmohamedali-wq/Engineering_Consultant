import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
from g4f.client import Client
import io

# 1. إعدادات الصفحة (الحفاظ على الهوية البصرية الداكنة)
st.set_page_config(page_title="UAE Engineering Auditor Pro", layout="wide", page_icon="🏗️")

lang_data = {
    "English": {
        "sidebar_title": "Control Panel",
        "region_label": "Project Location (Emirate)",
        "title": "🏗️ Full Technical Compliance & Precise Gap Auditor",
        "run_btn": "🚀 Run Deep Item-by-Item Audit",
        "table_header": "Detailed Compliance, Differences & Gaps Report",
        "down_btn": "📥 Download Full Report (Excel)",
        "processing": "Analyzing all clauses... comparing Specs vs Offer."
    },
    "العربية": {
        "sidebar_title": "لوحة التحكم",
        "region_label": "موقع المشروع (الإمارة)",
        "title": "🏗️ مدقق المطابقة الفنية وحصر النواقص",
        "run_btn": "🚀 بدء التدقيق العميق",
        "table_header": "تقرير تحليل المطابقة الكاملة، الاختلافات، والنواقص",
        "down_btn": "📥 تحميل التقرير الشامل (Excel)",
        "processing": "جاري مراجعة كل بند (الموجود والمفقود)... يرجى الانتظار."
    }
}

municipalities_db = {
    "Abu Dhabi (DMT & Estidama)": {"auth": "DMT Abu Dhabi", "std": "Estidama"},
    "Dubai (Municipality & RTA)": {"auth": "Dubai Municipality", "std": "Al Sa'fat"},
    "Sharjah (Municipality)": {"auth": "Sharjah Municipality", "std": "Sharjah Code"},
    "Other Emirates": {"auth": "UAE Authority", "std": "General Code"}
}

# --- القائمة الجانبية (Sidebar) ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/cb/Flag_of_the_United_Arab_Emirates.svg/255px-Flag_of_the_United_Arab_Emirates.svg.png", width=100)
    ui_lang = st.selectbox("Language / اللغة", ["العربية", "English"])
    txt = lang_data[ui_lang]
    st.divider()
    selected_region = st.selectbox(txt["region_label"], list(municipalities_db.keys()))
    current = municipalities_db[selected_region]
    st.success(f"📍 Standard: {current['auth']}")

st.title(txt["title"])

col1, col2 = st.columns(2)
with col1:
    specs_file = st.file_uploader("1. Reference Specs (ملف المواصفات)", type=['pdf'])
with col2:
    offer_file = st.file_uploader("2. Technical Offer (العرض الفني)", type=['pdf'])

def extract_text(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    return " ".join([page.get_text() for page in doc])

# 3. محرك التدقيق (يستخرج المطابق وغير المطابق)
if st.button(txt["run_btn"]):
    if specs_file and offer_file:
        progress_bar = st.progress(0)
        status_msg = st.empty()
        
        status_msg.info(txt["processing"])
        specs_txt = extract_text(specs_file)[:20000]
        progress_bar.progress(30)
        
        offer_txt = extract_text(offer_file)[:20000]
        progress_bar.progress(60)
        
        client = Client()
        
        # برومبت يركز على استخراج "كل شيء" وتوضيح رقم واسم المواصفة
        prompt = f"""
        Act as a Senior UAE Engineering Auditor. 
        TASK: Compare EVERY Clause in 'Specs' against 'Offer'.
        
        OUTPUT RULES:
        1. List BOTH: Items that are found (Compliant) and items that are missing (Not Provided).
        2. Column 'Clause_Name_No': Extract the exact Number and Title from Specs (e.g., 260519 - Cables).
        3. Column 'Status': Mark as 'COMPLIANT' if found, 'PARTIAL' if different, or 'STRICTLY MISSING' if absent.
        4. Column 'Difference_Details': If status is Compliant, write 'Fully Matches'. If not, explain why.
        5. For ALL items (even missing), provide UAE market alternatives and AED price ranges.

        COLUMNS:
        Clause_Name_No; Specs_Requirement; Offer_Response; Status; Difference_Details; Best_Alternatives_UAE; Price_Range_AED; Expert_Recommendation.

        Separator: (;)
        Language: {ui_lang}.
        """
        
        try:
            response = client.chat.completions.create(model="", messages=[{"role": "user", "content": f"{prompt}\nSpecs: {specs_txt}\nOffer: {offer_txt}"}])
            raw_data = response.choices[0].message.content
            
            if "Clause_Name_No" in raw_data:
                clean_csv = raw_data[raw_data.find("Clause_Name_No"):].strip()
                df = pd.read_csv(io.StringIO(clean_csv), sep=';', on_bad_lines='skip')
                
                progress_bar.progress(100)
                status_msg.empty()
                
                # عرض النتائج بالشكل المعتمد
                st.subheader(txt["table_header"])
                st.dataframe(df, use_container_width=True)

                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
                st.download_button(txt["down_btn"], output.getvalue(), "Detailed_Engineering_Audit.xlsx")
            else:
                st.error("AI Error: Analysis was not structured correctly. Please try again.")
        except Exception as e:
            st.error(f"Error: {e}")