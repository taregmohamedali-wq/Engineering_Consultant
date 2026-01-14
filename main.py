import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
from g4f.client import Client
import io

# 1. إعدادات الصفحة والواجهة الاحترافية
st.set_page_config(page_title="UAE Engineering Auditor Pro", layout="wide", page_icon="🏗️")

# تهيئة الذاكرة السحابية للجلسة (Session State)
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "full_context" not in st.session_state:
    st.session_state.full_context = ""
if "report_df" not in st.session_state:
    st.session_state.report_df = None

lang_data = {
    "English": {
        "sidebar_title": "Consultant Control Panel",
        "region_label": "Project Location (Emirate)",
        "title": "🏗️ Full Clause Auditor & AI Agent (Gemini Logic)",
        "run_btn": "🚀 Run 100% Comprehensive Audit",
        "table_header": "Technical Discrepancy & Gap Analysis",
        "chat_header": "💬 Chat with your Technical Consultant (Linked to Files)",
        "chat_placeholder": "Ask about specific values, missing items, or UAE standards...",
        "down_btn": "📥 Download Report (Excel)"
    },
    "العربية": {
        "sidebar_title": "لوحة التحكم الاستشارية",
        "region_label": "موقع المشروع (الإمارة)",
        "title": "🏗️ المستشار ",
        "run_btn": "🚀 بدء التدقيق الشامل بنسبة 100%",
        "table_header": "تقرير مطابقة البنود وتحليل الفوارق التفصيلي",
        "chat_header": "💬 حاور المستشار الفني (مرتبط بالملفات المرفوعة)",
        "chat_placeholder": "اسأل عن قيم محددة، بنود مفقودة، أو معايير بلدية الإمارات...",
        "down_btn": "📥 تحميل التقرير (Excel)"
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
    specs_file = st.file_uploader("1. Reference Specs (المواصفات)", type=['pdf'])
with col2:
    offer_file = st.file_uploader("2. Technical Offer (العرض الفني)", type=['pdf'])

def extract_text(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    return " ".join([page.get_text() for page in doc])

# --- محرك التدقيق (الجدول الرئيسي) ---
if st.button(txt["run_btn"]):
    if specs_file and offer_file:
        progress_bar = st.progress(0)
        specs_txt = extract_text(specs_file)[:30000]
        offer_txt = extract_text(offer_file)[:25000]
        
        # حفظ البيانات في سياق الأيجنت
        st.session_state.full_context = f"SPECIFICATIONS:\n{specs_txt}\n\nTECHNICAL OFFER:\n{offer_txt}"
        
        client = Client()
        prompt = f"""Act as a Senior UAE Technical Auditor. 
        Compare Specs vs Offer Clause-by-Clause. DO NOT SKIP ANY ITEM.
        COLUMNS: Clause_No; Clause_Title; Offer_Status; Consultant_Notes; Required_Action; UAE_Alternatives; Price_AED.
        Language: {ui_lang}. Separator: (;)"""
        
        try:
            response = client.chat.completions.create(model="", messages=[{"role": "user", "content": f"{prompt}\nData: {st.session_state.full_context[:15000]}"}])
            raw_data = response.choices[0].message.content
            if "Clause_No" in raw_data:
                clean_csv = raw_data[raw_data.find("Clause_No"):].strip()
                st.session_state.report_df = pd.read_csv(io.StringIO(clean_csv), sep=';', on_bad_lines='skip')
                st.success("Analysis Complete!")
                progress_bar.progress(100)
        except Exception as e:
            st.error(f"Audit Error: {e}")

# --- عرض الجدول ---
if st.session_state.report_df is not None:
    st.subheader(txt["table_header"])
    st.dataframe(st.session_state.report_df, use_container_width=True)

# --- محرك الحوار الذكي (AI Consultant Agent) ---
st.divider()
st.subheader(txt["chat_header"])

# عرض فقاعات الدردشة
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if user_query := st.chat_input(txt["chat_placeholder"]):
    st.session_state.chat_history.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    with st.chat_message("assistant"):
        if st.session_state.full_context == "":
            st.warning("Please upload files and run audit first to chat about them.")
        else:
            with st.spinner("Consulting Gemini Agent..."):
                client = Client()
                # بناء البرومبت ليكون مرتبطاً بالملفات المرفوعة
                agent_prompt = f"""
                You are Gemini, a Senior UAE Engineering Consultant.
                Your knowledge is based on the uploaded Project Specs and Technical Offer.
                
                CONTEXT FROM FILES:
                {st.session_state.full_context[:12000]} 

                USER QUESTION: {user_query}
                
                INSTRUCTIONS:
                1. Answer only based on the provided files and UAE engineering standards.
                2. Be precise about clause numbers, THD values, brands, and missing documents.
                3. If the user asks about a discrepancy, refer to the Specs vs Offer logic.
                """
                
                chat_response = client.chat.completions.create(
                    model="",
                    messages=[{"role": "system", "content": agent_prompt}, *st.session_state.chat_history]
                )
                answer = chat_response.choices[0].message.content
                st.markdown(answer)
                st.session_state.chat_history.append({"role": "assistant", "content": answer})