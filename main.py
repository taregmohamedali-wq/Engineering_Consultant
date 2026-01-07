import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
from g4f.client import Client
import io

# 1. إعدادات الصفحة والواجهة (ثابتة تماماً كما طلبت)
st.set_page_config(page_title="UAE Engineering Auditor Pro", layout="wide", page_icon="🏗️")

lang_data = {
    "English": {
        "sidebar_title": "Control Panel",
        "region_label": "Project Location (Emirate)",
        "title": "🏗️ Full Technical Compliance & Precise Gap Auditor",
        "run_btn": "🚀 Run Ultra-Deep Audit (Clause-by-Clause)",
        "table_header": "Ultra-Precise Compliance, Differences & Gap Analysis",
        "down_btn": "📥 Download Detailed Audit (Excel)",
        "processing": "Performing deep scanning of all clauses... Please wait."
    },
    "العربية": {
        "sidebar_title": "لوحة التحكم",
        "region_label": "موقع المشروع (الإمارة)",
        "title": "🏗️ مدقق المطابقة الفنية وحصر النواقص ",
        "run_btn": "🚀 بدء التدقيق العميق (بند مقابل بند)",
        "table_header": "تقرير تحليل المطابقة، الفروقات، والنواقص التفصيلي",
        "down_btn": "📥 تحميل التقرير التفصيلي (Excel)",
        "processing": "جاري المسح الشامل لكل بند وتحليل الفروقات بدقة... يرجى الانتظار."
    }
}

municipalities_db = {
    "Abu Dhabi (DMT & Estidama)": {"auth": "DMT Abu Dhabi", "std": "Estidama"},
    "Dubai (Municipality & RTA)": {"auth": "Dubai Municipality", "std": "Al Sa'fat"},
    "Sharjah (Municipality)": {"auth": "Sharjah Municipality", "std": "Sharjah Code"},
    "Other Emirates": {"auth": "UAE Authority", "std": "General Code"}
}

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/cb/Flag_of_the_United_Arab_Emirates.svg/255px-Flag_of_the_United_Arab_Emirates.svg.png", width=100)
    ui_lang = st.selectbox("Language / اللغة", ["العربية", "English"])
    txt = lang_data[ui_lang]
    st.divider()
    selected_region = st.selectbox(txt["region_label"], list(municipalities_db.keys()))
    current = municipalities_db[selected_region]
    st.success(f"📍 Region Set: {current['auth']}")

st.title(txt["title"])

col1, col2 = st.columns(2)
with col1:
    specs_file = st.file_uploader("1. Reference Specs (المواصفات المرجعية)", type=['pdf'])
with col2:
    offer_file = st.file_uploader("2. Technical Offer (العرض الفني)", type=['pdf'])

def extract_full_text(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    return " ".join([page.get_text() for page in doc])

# 3. محرك التدقيق فائق الدقة (Ultra-Deep Audit)
if st.button(txt["run_btn"]):
    if specs_file and offer_file:
        progress_bar = st.progress(0)
        status_msg = st.empty()
        
        status_msg.info(txt["processing"])
        specs_txt = extract_full_text(specs_file)[:20000] # زيادة سعة المسح
        progress_bar.progress(30)
        
        offer_txt = extract_full_text(offer_file)[:20000]
        progress_bar.progress(60)
        
        client = Client()
        
        # برومبت صارم جداً يجبر على مراجعة "كل" بند ويوضح الفروقات والمفقودات
        prompt = f"""
        Act as a Senior UAE Technical Auditor for {current['auth']}.
        You MUST perform an ULTRA-PRECISE comparison between 'Specs' and 'Offer'.

        CORE REQUIREMENTS:
        1. REVIEW EVERY SINGLE CLAUSE found in the Specs text. DO NOT SUMMARIZE.
        2. If a clause is missing in the offer, mark as 'STRICTLY MISSING'.
        3. If it exists but differs (different material, brand, or capacity), explain the EXACT technical difference.
        4. Provide local UAE alternatives (e.g., Ducab, Schneider) and real price ranges in AED.
        5. Provide a professional 'Municipality-Standard' recommendation for each gap.

        COLUMNS:
        Clause_No; Specs_Requirement; Offer_Response; Status; Technical_Difference; Best_Alternatives_UAE; Price_Range_AED; Recommended_Solution.

        OUTPUT: Return ONLY a CSV table using (;) separator. No text before or after.
        Language: {ui_lang}.
        """
        
        try:
            response = client.chat.completions.create(
                model="", 
                messages=[{"role": "user", "content": f"{prompt}\nSpecs Data: {specs_txt}\nOffer Data: {offer_txt}"}]
            )
            raw_data = response.choices[0].message.content
            
            if "Clause_No" in raw_data:
                clean_csv = raw_data[raw_data.find("Clause_No"):].strip()
                df = pd.read_csv(io.StringIO(clean_csv), sep=';', on_bad_lines='skip')
                
                # إكمال شريط التقدم
                progress_bar.progress(100)
                status_msg.empty()
                
                # 4. عرض التقرير النهائي بنفس التنسيق المعتمد
                st.subheader(txt["table_header"])
                st.dataframe(df, use_container_width=True)

                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
                st.download_button(txt["down_btn"], output.getvalue(), "Ultra_Deep_Audit_Report.xlsx")
            else:
                st.error("AI Error: Could not generate a structured table. Please ensure the PDFs contain readable text.")
        except Exception as e:
            st.error(f"Audit failed: {e}")