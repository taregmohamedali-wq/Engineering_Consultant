import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
from g4f.client import Client
import io

# إعدادات الواجهة الاحترافية
st.set_page_config(page_title="UAE Engineering Auditor Pro", layout="wide", page_icon="🏗️")

# قاموس المعايير والبلديات في الإمارات
municipalities_specs = {
    "Abu Dhabi": {
        "authority": "DMT (Department of Municipalities and Transport)",
        "standards": "Estidama Pearl Rating & Abu Dhabi International Building Code",
        "focus": "Sustainability, Infrastructure, and Estidama Compliance."
    },
    "Dubai": {
        "authority": "Dubai Municipality (DM)",
        "standards": "Al Sa'fat - Dubai Green Building System & DM Technical Guidelines",
        "focus": "Green Building, Fire Safety (DCD), and Structural Specs."
    },
    "Sharjah": {
        "authority": "Sharjah City Municipality",
        "standards": "Sharjah Building Code & SEWA Regulations",
        "focus": "Electrical Load Management and Traditional/Modern mix."
    },
    "Ajman": {
        "authority": "Ajman Municipality & Planning Dept",
        "standards": "Ajman Building Standards",
        "focus": "Urban Planning and Environmental Safety."
    },
    "Ras Al Khaimah": {
        "authority": "RAK Municipality",
        "standards": "Barjeel (RAK Green Building Code)",
        "focus": "Energy Efficiency and Thermal Insulation."
    },
    "Fujairah/UAQ": {
        "authority": "Local Municipality",
        "standards": "UAE Fire & Life Safety Code of Practice",
        "focus": "Safety and General Engineering Standards."
    }
}

# الشريط الجانبي - اختيار المنطقة
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/cb/Flag_of_the_United_Arab_Emirates.svg/255px-Flag_of_the_United_Arab_Emirates.svg.png", width=120)
    st.title("Control Panel")
    selected_region = st.selectbox("Select Project Location", list(municipalities_specs.keys()))
    
    # استدعاء بيانات المنطقة المختارة
    current_spec = municipalities_specs[selected_region]
    st.success(f"📍 Active Authority: {current_spec['authority']}")
    st.info(f"📜 Applied Standard: {current_spec['standards']}")

# الواجهة الرئيسية
st.title("🏗️ UAE Multi-Municipality Engineering Auditor")
st.markdown(f"**Current Audit Mode:** Custom Analysis based on **{selected_region}** Regulations.")

col1, col2 = st.columns(2)
with col1:
    specs_file = st.file_uploader("Upload Specs (Reference)", type=['pdf'])
with col2:
    offer_file = st.file_uploader("Upload Offer (Technical)", type=['pdf'])

def extract_text(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    return "".join([page.get_text() for page in doc])

if st.button("🚀 Start Region-Specific Audit"):
    if specs_file and offer_file:
        progress_bar = st.progress(0)
        status = st.empty()
        
        specs_txt = extract_text(specs_file)[:12000] # زيادة حجم القراءة
        offer_txt = extract_text(offer_file)[:12000]
        progress_bar.progress(30)
        
        status.text(f"Consulting AI for {selected_region} Building Codes...")
        client = Client()
        
        # برومبت ذكي يتغير بتغير المنطقة المختارة
        prompt = f"""
        Act as a Senior Auditor expert in {current_spec['authority']} and {current_spec['standards']}.
        Focus points for this region: {current_spec['focus']}.
        
        Compare the Specs vs Offer and return a CSV table (separator: ;)
        COLUMNS: Item_Ref; Specs_Requirement; Status; Best_Alternatives_UAE; Price_Range_AED; AI_Municipality_Proposal.
        
        Instructions:
        1. If region is Dubai, use DM/Al Sa'fat logic.
        2. If region is Abu Dhabi, use DMT/Estidama logic.
        3. Provide Price Range in AED based on local suppliers.
        4. Suggest the best 2 brands (e.g., Ducab, ABB, etc.).
        
        Specs: {specs_txt}
        Offer: {offer_txt}
        """
        
        try:
            response = client.chat.completions.create(model="", messages=[{"role": "user", "content": prompt}])
            raw_data = response.choices[0].message.content
            
            if "Item_Ref" in raw_data:
                clean_csv = raw_data[raw_data.find("Item_Ref"):].replace('|', '').strip()
                df = pd.read_csv(io.StringIO(clean_csv), sep=';', on_bad_lines='skip')
                
                progress_bar.progress(100)
                status.success(f"✅ Audit Completed for {selected_region}!")
                st.dataframe(df, use_container_width=True)

                # Export Excel
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name=f'{selected_region}_Audit')
                
                st.download_button(f"📥 Download {selected_region} Report", output.getvalue(), f"Audit_{selected_region}.xlsx")
            else:
                st.error("AI processing error. Please try again.")
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.warning("Please upload both files.")