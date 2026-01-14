import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
from g4f.client import Client
import io

# 1. إعدادات الصفحة والواجهة
st.set_page_config(page_title="UAE Engineering Auditor Pro", layout="wide", page_icon="🏗️")

# تهيئة ذاكرة الدردشة في حال لم تكن موجودة
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "audit_context" not in st.session_state:
    st.session_state.audit_context = ""

lang_data = {
    "English": {
        "sidebar_title": "Consultant Control Panel",
        "region_label": "Project Location (Emirate)",
        "title": "🏗️ Full Clause-by-Clause Auditor & AI Agent",
        "run_btn": "🚀 Run 100% Comprehensive Audit",
        "table_header": "Detailed Technical Discrepancy Report",
        "down_btn": "📥 Download Report (Excel)",
        "chat_title": "💬 Consultant AI Agent (Gemini Logic)",
        "chat_placeholder": "Ask me about the specs, offer, or discrepancies...",
        "processing": "Scrutinizing EVERY clause... Acting as Gemini Agent."
    },
    "العربية": {
        "sidebar_title": "لوحة التحكم الاستشارية",
        "region_label": "موقع المشروع (الإمارة)",
        "title": "🏗️ مدقق البنود الشامل والمستشار الذكي",
        "run_btn": "🚀 بدء التدقيق الشامل بنسبة 100%",
        "table_header": "تقرير مطابقة البنود وتحليل الفوارق التفصيلي",
        "down_btn": "📥 تحميل التقرير (Excel)",
        "chat_title": "💬 المستشار الهندسي الذكي (منطق جيميناي)",
        "chat_placeholder": "اسألني عن أي تفاصيل في المواصفات أو العرض أو الفوارق...",
        "processing": "جاري فحص كل بند... أعمل الآن كمستشار هندسي ذكي."
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
    st.info(f"📍 Authority: {current['auth']}")

st.title(txt["title"])

col1, col2 = st.columns(2)
with col1:
    specs_file = st.file_uploader("1. Reference Specs (المواصفات المرجعية)", type=['pdf'])
with col2:
    offer_file = st.file_uploader("2. Technical Offer (العرض الفني)", type=['pdf'])

def extract_full_text(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    return " ".join([page.get_text() for page in doc])

# --- محرك التدقيق ---
if st.button(txt["run_btn"]):
    if specs_file and offer_file:
        progress_bar = st.progress(0)
        specs_txt = extract_full_text(specs_file)[:30000]
        offer_txt = extract_full_text(offer_file)[:25000]
        
        # حفظ النصوص في الذاكرة للدردشة لاحقاً
        st.session_state.audit_context = f"Specs: {specs_txt}\n\nOffer: {offer_txt}"
        
        client = Client()
        prompt = f"""Act as a Senior Technical Auditor. Compare EVERY clause from Specs against Offer. 
        COLUMNS: Clause_No; Clause_Title_Description; Offer_Status; Consultant_Notes_Discrepancies; Required_Action; UAE_Alternatives; Price_Range_AED.
        Language: {ui_lang}. Separator: (;)"""
        
        try:
            response = client.chat.completions.create(model="", messages=[{"role": "user", "content": f"{prompt}\nSpecs: {specs_txt}\nOffer: {offer_txt}"}])
            raw_data = response.choices[0].message.content
            if "Clause_No" in raw_data:
                clean_csv = raw_data[raw_data.find("Clause_No"):].strip()
                df = pd.read_csv(io.StringIO(clean_csv), sep=';', on_bad_lines='skip')
                st.session_state.report_df = df
                st.success("Audit Completed!")
            else:
                st.error("Audit data error.")
        except Exception as e:
            st.error(f"Error: {e}")

# --- عرض الجدول إذا كان موجوداً ---
if "report_df" in st.session_state:
    st.subheader(txt["table_header"])
    st.dataframe(st.session_state.report_df, use_container_width=True)

# --- قسم الدردشة والمناقشة (AI Consultant Agent) ---
st.divider()
st.subheader(txt["chat_title"])

# عرض تاريخ الدردشة
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# إدخال سؤال جديد من المستخدم
if user_input := st.chat_input(txt["chat_placeholder"]):
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # توليد الرد من المستشار (Gemini Logic)
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            client = Client()
            # إرسال سياق التدقيق مع سؤال المستخدم
            system_instruction = f"You are Gemini, a Senior Engineering Consultant in the UAE. Use the following context to answer precisely: {st.session_state.audit_context[:10000]}"
            
            chat_response = client.chat.completions.create(
                model="",
                messages=[
                    {"role": "system", "content": system_instruction},
                    *st.session_state.chat_history
                ]
            )
            reply = chat_response.choices[0].message.content
            st.markdown(reply)
            st.session_state.chat_history.append({"role": "assistant", "content": reply})