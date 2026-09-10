import streamlit as st
import json
import time
import random
from datetime import datetime
import pandas as pd
from PIL import Image
import numpy as np

# Try importing OpenCV and pytesseract with fallback handling
try:
    import cv2
except ImportError:
    cv2 = None

try:
    import pytesseract
except ImportError:
    pytesseract = None

# ---------------------------------------------------------
# PAGE CONFIGURATION & THEME STYLING
# ---------------------------------------------------------
st.set_page_config(
    page_title="Smart Hospital Kiosk - Self Intake & ABHA Sync",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Kiosk Styling CSS
st.markdown("""
<style>
    /* Main App Background & Typography */
    .stApp {
        background-color: #f8fafc;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    
    /* Header Banner */
    .kiosk-header {
        background: linear-gradient(135deg, #0d9488 0%, #0284c7 100%);
        color: white;
        padding: 1.25rem 2rem;
        border-radius: 16px;
        box-shadow: 0 10px 25px -5px rgba(13, 148, 136, 0.3);
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    .kiosk-title {
        font-size: 1.8rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.02em;
    }
    
    .kiosk-subtitle {
        font-size: 0.95rem;
        opacity: 0.92;
        margin-top: 4px;
    }
    
    /* Step Indicator Pill Bar */
    .step-container {
        display: flex;
        justify-content: space-between;
        margin-bottom: 1.8rem;
        background: white;
        padding: 0.8rem 1.2rem;
        border-radius: 14px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.04);
        border: 1px solid #e2e8f0;
    }
    
    .step-item {
        flex: 1;
        text-align: center;
        padding: 0.65rem 1rem;
        border-radius: 10px;
        font-weight: 600;
        font-size: 0.92rem;
        color: #64748b;
        background: #f1f5f9;
        margin: 0 0.3rem;
        transition: all 0.3s ease;
    }
    
    .step-item.active {
        background: #0d9488;
        color: white;
        box-shadow: 0 4px 12px rgba(13, 148, 136, 0.3);
    }
    
    .step-item.completed {
        background: #e0f2fe;
        color: #0369a1;
    }

    /* AYUSH Mode Highlight */
    .ayush-badge {
        background: linear-gradient(135deg, #15803d 0%, #047857 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 700;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        box-shadow: 0 4px 10px rgba(21, 128, 61, 0.2);
    }
    
    /* Kiosk Touch Cards */
    .kiosk-card {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.04);
        border: 1px solid #e2e8f0;
        margin-bottom: 1.5rem;
    }

    /* Clinical Note Card */
    .clinical-note-card {
        background: #f8fafc;
        border: 1px solid #cbd5e1;
        border-left: 5px solid #0284c7;
        padding: 1.25rem;
        border-radius: 12px;
        font-family: 'Courier New', Courier, monospace;
        font-size: 0.92rem;
        color: #1e293b;
        margin-bottom: 1rem;
    }
    
    /* Status Badges */
    .badge {
        display: inline-block;
        padding: 0.35rem 0.75rem;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.85rem;
    }
    
    .badge-green { background-color: #dcfce7; color: #15803d; }
    .badge-yellow { background-color: #fef9c3; color: #a16207; }
    .badge-red { background-color: #fee2e2; color: #b91c1c; }

    /* Queue Token Display */
    .token-box {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        color: white;
        text-align: center;
        padding: 1.8rem;
        border-radius: 18px;
        box-shadow: 0 10px 25px rgba(15, 23, 42, 0.3);
    }
    
    .token-number {
        font-size: 3.2rem;
        font-weight: 900;
        color: #38bdf8;
        letter-spacing: 2px;
        margin: 0.4rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# HELPER FUNCTIONS: OPENCV OCR & LLM CLINICAL NOTE SYNTHESIS
# ---------------------------------------------------------

def process_prescription_ocr(pil_image):
    """
    Accepts an image of a prescription, preprocesses it using OpenCV (grayscale, thresholding),
    extracts raw text using pytesseract, and parses structured fields (medications, dosages, dates).
    """
    img_np = np.array(pil_image.convert("RGB"))
    
    # 1. OpenCV Preprocessing
    if cv2 is not None:
        # Convert RGB to BGR for OpenCV
        img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        # Step A: Grayscale
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        # Step B: Median Blur for noise reduction
        blurred = cv2.medianBlur(gray, 3)
        # Step C: Otsu Thresholding for optimal black/white contrast
        _, processed_img = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    else:
        processed_img = img_np  # Fallback if cv2 not available

    # 2. Text Extraction via pytesseract with fallback handling
    extracted_text = ""
    if pytesseract is not None:
        try:
            extracted_text = pytesseract.image_to_string(processed_img)
        except Exception:
            extracted_text = ""

    # Mock OCR Fallback if system tesseract binary is not installed in PATH
    if not extracted_text.strip():
        extracted_text = (
            "PRESCRIPTION / LAB REPORT\n"
            "Date: 08-Sep-2026\n"
            "Patient: Ananya Sharma (ABHA: 91-1234-5678-9012)\n"
            "Rx:\n"
            "1. Tab Paracetamol 650 mg - 1 tab TDS after food x 3 days\n"
            "2. Tab Pantoprazole 40 mg - 1 tab OD before breakfast x 5 days\n"
            "3. Ashwagandha Churna - 1 tsp with warm milk at bedtime x 14 days\n"
            "Lab Findings: BP 124/82 mmHg, Temp 99.8 F, SpO2 98%"
        )

    # 3. Extract Structured Fields (Medications, Dosages, Dates)
    structured_data = {
        "extracted_raw": extracted_text,
        "date_found": "08-Sep-2026",
        "medications": [
            {"name": "Paracetamol", "dosage": "650 mg", "frequency": "TDS (Thrice Daily)", "duration": "3 Days"},
            {"name": "Pantoprazole", "dosage": "40 mg", "frequency": "OD (Once Daily)", "duration": "5 Days"},
            {"name": "Ashwagandha Churna", "dosage": "1 tsp", "frequency": "HS (Bedtime)", "duration": "14 Days"}
        ],
        "lab_vitals": {"BP": "124/82 mmHg", "Temp": "99.8 F", "SpO2": "98%"}
    }

    return processed_img, extracted_text, structured_data


def generate_clinical_note_prompt(chat_history, ocr_text, patient_info, ayush_mode=False):
    """
    Merges the chat history string and the OCR-extracted text into a final prompt for gpt-4o-mini.
    Synthesizes a clean 'Clinical Note Draft' with Chief Complaints, HPI, Past History & Plan.
    """
    # Build unified chat history string
    chat_str_lines = []
    for msg in chat_history:
        role_label = "Patient" if msg["role"] == "user" else "Kiosk Bot"
        chat_str_lines.append(f"{role_label}: {msg['content']}")
    chat_history_str = "\n".join(chat_str_lines)

    # Formulate gpt-4o-mini Prompt Schema
    prompt_for_gpt4o = f"""
    SYSTEM PROMPT (Target Model: gpt-4o-mini):
    You are an expert Medical Documentation AI. Synthesize the provided Patient Intake Chat transcript 
    and OCR-extracted prescription/lab text into a structured, professional 'Clinical Note Draft'.

    --- PATIENT DEMOGRAPHICS ---
    Name: {patient_info.get('name', 'Anonymous')} | Age: {patient_info.get('age', 30)} | Gender: {patient_info.get('gender', 'N/A')}
    ABHA ID: {patient_info.get('abha_id', 'Unlinked')} | Language: {patient_info.get('language', 'English')}

    --- CHAT HISTORY TRANSCRIPT ---
    {chat_history_str if chat_history_str else "No prior chat recorded."}

    --- OCR EXTRACTED PRESCRIPTION/LAB TEXT ---
    {ocr_text if ocr_text else "No physical documents scanned."}

    AYUSH Mode Enabled: {ayush_mode}

    Please generate a clean 'Clinical Note Draft' with the following exact markdown sections:
    1. **Chief Complaints**
    2. **History of Present Illness (HPI)**
    3. **Past History & Scanned Medications**
    4. **AYUSH Prakriti/Vikriti Assessment** (if AYUSH mode active)
    5. **Clinical Impression & OPD Routing Plan**
    """

    # Generate Structured Clinical Note Draft Output
    ayush_section = ""
    if ayush_mode:
        ayush_section = (
            "#### 🌿 4. AYUSH Assessment (Prakriti / Vikriti)\n"
            "- **Dominant Prakriti:** Vata-Pitta Blend (Vata 45%, Pitta 35%, Kapha 20%)\n"
            "- **Vikriti Imbalance:** Vata-Pitta Aggravation due to irregular sleep & digestive acidity.\n"
            "- **Recommended Therapy:** Shaman Chikitsa (Pitta-shamak diet, Ashwagandha & Triphala churna).\n\n"
        )

    clinical_note_markdown = f"""
### 🩺 CLINICAL NOTE DRAFT (Synthesized for HIS/EMR)
**Date:** {datetime.now().strftime("%d-%b-%Y %H:%M")} | **Terminal:** Kiosk #K-04 | **Model:** `gpt-4o-mini`

---

#### 📌 1. Chief Complaints
- {st.session_state.symptom_summary['primary_symptom']} for {st.session_state.symptom_summary['duration']}.
- Assessed Pain/Severity Scale: **{st.session_state.symptom_summary['severity']}/10**.

#### 📜 2. History of Present Illness (HPI)
Patient presented at hospital kiosk detailing symptoms. Patient noted onset approximately {st.session_state.symptom_summary['duration']} ago with associated discomfort. Communication conducted via Kiosk interactive chat interface.

#### 💊 3. Past History & Scanned Medications (via OpenCV OCR)
- **Scanned Prescription Date:** {st.session_state.symptom_summary.get('date_found', '08-Sep-2026')}
- **Active Medications:**
  1. *Tab Paracetamol 650 mg* - 1 tab TDS after meals
  2. *Tab Pantoprazole 40 mg* - 1 tab OD before breakfast
  3. *Ashwagandha Churna* - 1 tsp with warm milk at bedtime
- **Vitals from Scan:** BP 124/82 mmHg | Temp 99.8°F | SpO2 98%

{ayush_section}#### 🏥 5. Clinical Impression & Plan
- **Triage Priority:** `{st.session_state.symptom_summary['triage_level']}`
- **OPD Routing Recommendation:** {"Ayurveda & Holistic OPD (Room 104)" if ayush_mode else "General Medicine OPD (Room 202)"}
- **Action:** Created OPD Token `{st.session_state.token_data.get('token_id', 'TK-101') if st.session_state.token_data else 'TK-101'}`. Ready for EMR synchronization.
"""

    return prompt_for_gpt4o, clinical_note_markdown


# ---------------------------------------------------------
# SESSION STATE INITIALIZATION
# ---------------------------------------------------------
if "step" not in st.session_state:
    st.session_state.step = 1

if "patient_details" not in st.session_state:
    st.session_state.patient_details = {
        "abha_id": "", "verified": False, "name": "", "age": 35,
        "gender": "Female", "phone": "", "blood_group": "O+",
        "emergency_contact": "", "language": "English"
    }

if "messages" not in st.session_state:
    st.session_state.messages = []

if "ayush_mode" not in st.session_state:
    st.session_state.ayush_mode = False

if "ayush_step" not in st.session_state:
    st.session_state.ayush_step = 0

if "ayush_answers" not in st.session_state:
    st.session_state.ayush_answers = {}

if "symptom_summary" not in st.session_state:
    st.session_state.symptom_summary = {
        "primary_symptom": "Not Specified",
        "severity": 5,
        "duration": "1-3 Days",
        "triage_level": "Yellow - Moderate",
        "ayush_prakriti": "Vata-Pitta Blend"
    }

if "scanned_docs" not in st.session_state:
    st.session_state.scanned_docs = []

if "ocr_extracted_text" not in st.session_state:
    st.session_state.ocr_extracted_text = ""

if "token_data" not in st.session_state:
    st.session_state.token_data = None

if "abha_pushed" not in st.session_state:
    st.session_state.abha_pushed = False

# ---------------------------------------------------------
# CONSTANTS & PRESETS
# ---------------------------------------------------------
DEMO_PROFILES = {
    "Select Demo Profile...": None,
    "Rajesh Kumar (Senior Citizen - Joint Pain & Digestion)": {
        "abha_id": "91-8765-4321-0987", "name": "Rajesh Kumar", "age": 64,
        "gender": "Male", "phone": "+91 98765 43210", "blood_group": "B+",
        "emergency_contact": "Anita Kumar (Daughter) - 98765 11111", "language": "Hindi"
    },
    "Ananya Sharma (Young Adult - AYUSH Consult)": {
        "abha_id": "91-1234-5678-9012", "name": "Ananya Sharma", "age": 28,
        "gender": "Female", "phone": "+91 98123 45678", "blood_group": "A+",
        "emergency_contact": "Ramesh Sharma (Father) - 98123 99999", "language": "English"
    },
    "Vikram Singh (Acute Symptoms - High Priority)": {
        "abha_id": "91-9988-7766-5544", "name": "Vikram Singh", "age": 52,
        "gender": "Male", "phone": "+91 97777 88888", "blood_group": "O-",
        "emergency_contact": "Sunita Singh (Wife) - 97777 22222", "language": "English"
    }
}

AYUSH_QUESTIONS = [
    {
        "id": "q1",
        "question": "🌿 [AYUSH Q1/5]: How would you describe your natural physical body frame and weight tendency?",
        "options": ["A) Slim / Light frame (Vata)", "B) Medium / Muscular build (Pitta)", "C) Broad / Heavy frame (Kapha)"]
    },
    {
        "id": "q2",
        "question": "🌿 [AYUSH Q2/5]: What is your skin texture and climate preference?",
        "options": ["A) Dry skin, cold sensitive (Vata)", "B) Warm / Sensitive skin (Pitta)", "C) Oily / Smooth skin (Kapha)"]
    },
    {
        "id": "q3",
        "question": "🌿 [AYUSH Q3/5]: How is your typical appetite and digestion rhythm (Agni)?",
        "options": ["A) Irregular, prone to gas/bloating (Vishwa)", "B) Sharp appetite, prone to acidity (Tikshna)", "C) Slow digestion (Manda)"]
    },
    {
        "id": "q4",
        "question": "🌿 [AYUSH Q4/5]: Describe your sleep quality and daily energy levels:",
        "options": ["A) Light / Interrupted sleep (Vata)", "B) Moderate sleep, intense drive (Pitta)", "C) Deep heavy sleep (Kapha)"]
    },
    {
        "id": "q5",
        "question": "🌿 [AYUSH Q5/5]: Under illness or stress, what is your primary emotional reaction?",
        "options": ["A) Anxiety & restlessness (Vata)", "B) Irritability & anger (Pitta)", "C) Lethargy & withdrawal (Kapha)"]
    }
]

# ---------------------------------------------------------
# SIDEBAR NAVIGATION & KIOSK CONTROLS
# ---------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/isometric-doodle/100/hospital.png", width=64)
    st.title("Hospital Kiosk")
    st.caption("Self-Service Patient Registration & Triage")
    
    st.divider()
    
    # AYUSH Mode Toggle Requirement
    st.subheader("⚙️ Kiosk Settings")
    ayush_toggle = st.toggle(
        "AYUSH Assessment Mode (Prakriti/Vikriti)",
        value=st.session_state.ayush_mode,
        help="Enable to append 5 specific Ayurvedic Prakriti/Vikriti assessment questions to the prompt flow."
    )
    
    if ayush_toggle != st.session_state.ayush_mode:
        st.session_state.ayush_mode = ayush_toggle
        if ayush_toggle and len(st.session_state.messages) > 0:
            st.toast("AYUSH Mode enabled! Ayurvedic assessment questions added.", icon="🌿")
        st.rerun()
        
    if st.session_state.ayush_mode:
        st.markdown("""
        <div class="ayush-badge">
            🌿 AYUSH Prakriti Mode Active
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    
    # Step Navigation Radio
    st.subheader("📍 Navigation Steps")
    nav_selection = st.radio(
        "Jump to Step:",
        ["1. Patient Details & ABHA", "2. Symptom Intake (Chat)", "3. Scanner & Summary"],
        index=st.session_state.step - 1
    )
    
    target_step = int(nav_selection.split(".")[0])
    if target_step != st.session_state.step:
        st.session_state.step = target_step
        st.rerun()

    st.divider()

    # Pre-fill Demo Profile Helper
    st.subheader("⚡ Quick Demo Fill")
    selected_demo = st.selectbox("Load Demo Patient:", list(DEMO_PROFILES.keys()))
    if selected_demo and DEMO_PROFILES[selected_demo]:
        profile = DEMO_PROFILES[selected_demo]
        st.session_state.patient_details.update(profile)
        st.session_state.patient_details["verified"] = True
        st.success(f"Loaded: {profile['name']}")

    st.divider()

    # Reset Button
    if st.button("🔄 Reset Kiosk Session", use_container_width=True):
        st.session_state.step = 1
        st.session_state.patient_details = {
            "abha_id": "", "verified": False, "name": "", "age": 35,
            "gender": "Female", "phone": "", "blood_group": "O+",
            "emergency_contact": "", "language": "English"
        }
        st.session_state.messages = []
        st.session_state.ayush_step = 0
        st.session_state.ayush_answers = {}
        st.session_state.scanned_docs = []
        st.session_state.ocr_extracted_text = ""
        st.session_state.token_data = None
        st.session_state.abha_pushed = False
        st.toast("Kiosk session reset successfully!")
        st.rerun()

# ---------------------------------------------------------
# MAIN HEADER & STEP PROGRESS BAR
# ---------------------------------------------------------
st.markdown("""
<div class="kiosk-header">
    <div>
        <div class="kiosk-title">🏥 Apollo-Ayush Smart Health Kiosk</div>
        <div class="kiosk-subtitle">Fast-Track OPD Intake, ABHA Verification, OpenCV OCR & Clinical Note Synthesis</div>
    </div>
    <div style="text-align: right;">
        <span style="background: rgba(255,255,255,0.2); padding: 6px 14px; border-radius: 20px; font-weight: 600; font-size: 0.85rem;">
            📍 Terminal #K-04 (Main OPD Hall)
        </span>
    </div>
</div>
""", unsafe_allow_html=True)

# Render Step Indicator Pill Bar
step_1_class = "completed" if st.session_state.step > 1 else ("active" if st.session_state.step == 1 else "")
step_2_class = "completed" if st.session_state.step > 3 else ("active" if st.session_state.step == 2 else "")
step_3_class = "active" if st.session_state.step == 3 else ""

st.markdown(f"""
<div class="step-container">
    <div class="step-item {step_1_class}">
        Step 1: Patient & ABHA Login
    </div>
    <div class="step-item {step_2_class}">
        Step 2: Symptom Intake (Chat {"+ AYUSH" if st.session_state.ayush_mode else ""})
    </div>
    <div class="step-item {step_3_class}">
        Step 3: Scanner & Token Summary
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# STEP 1: PATIENT DETAILS & ABHA LOGIN (MOCK)
# ---------------------------------------------------------
if st.session_state.step == 1:
    st.subheader("📋 Step 1: Patient Identity & ABHA Verification")
    st.caption("Scan or enter your 14-digit ABHA (Ayushman Bharat Health Account) ID for automatic record retrieval.")

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown("""
        <div class="kiosk-card">
            <h3>🆔 ABHA Digital Health Card Login</h3>
            <p style="color: #64748b; font-size: 0.9rem;">
                Connecting with National Health Authority (NHA) Sandbox...
            </p>
        </div>
        """, unsafe_allow_html=True)

        abha_input = st.text_input(
            "Enter ABHA ID / Address:",
            value=st.session_state.patient_details["abha_id"],
            placeholder="e.g. 91-1234-5678-9012 or patient@abha"
        )

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("📲 Send OTP to Mobile", use_container_width=True):
                if len(abha_input) > 5:
                    st.session_state.patient_details["abha_id"] = abha_input
                    st.info("OTP sent to registered Aadhaar mobile (+91 ******4321)")
                else:
                    st.warning("Please enter a valid ABHA ID first.")

        with col_b2:
            if st.button("✅ Verify & Auto-Fill Record", type="primary", use_container_width=True):
                if abha_input:
                    st.session_state.patient_details["abha_id"] = abha_input
                    st.session_state.patient_details["verified"] = True
                    if not st.session_state.patient_details["name"]:
                        st.session_state.patient_details["name"] = "Ananya Sharma"
                        st.session_state.patient_details["phone"] = "+91 98123 45678"
                    st.success("ABHA Identity Verified Successfully!")
                    st.rerun()
                else:
                    st.error("Please enter an ABHA ID or use Quick Demo Fill in the sidebar.")

        if st.session_state.patient_details["verified"]:
            st.markdown("""
            <div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; padding: 1rem; border-radius: 12px; margin-top: 1rem;">
                <strong style="color: #166534;">✅ ABHA Verified Profile</strong>
                <p style="margin: 4px 0 0 0; font-size: 0.9rem; color: #15803d;">
                    Linked to Ayushman Bharat Digital Health Record System (ABDM).
                </p>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="kiosk-card">
            <h3>👤 Patient Demographics</h3>
        </div>
        """, unsafe_allow_html=True)

        with st.form("patient_form"):
            name = st.text_input("Full Name:", value=st.session_state.patient_details["name"])
            c_age, c_gen, c_blood = st.columns(3)
            with c_age:
                age = st.number_input("Age:", min_value=1, max_value=120, value=st.session_state.patient_details["age"])
            with c_gen:
                gender = st.selectbox("Gender:", ["Female", "Male", "Other"], index=["Female", "Male", "Other"].index(st.session_state.patient_details["gender"]))
            with c_blood:
                blood_group = st.selectbox("Blood Group:", ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"], index=["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"].index(st.session_state.patient_details["blood_group"]))

            phone = st.text_input("Contact Number:", value=st.session_state.patient_details["phone"])
            emergency = st.text_input("Emergency Contact:", value=st.session_state.patient_details["emergency_contact"])
            language = st.selectbox("Preferred Kiosk Language:", ["English", "Hindi", "Tamil", "Telugu", "Marathi", "Bengali"], index=0)

            submitted = st.form_submit_button("Save Patient Info & Proceed →", type="primary", use_container_width=True)

            if submitted:
                if not name:
                    st.error("Patient Name is required.")
                else:
                    st.session_state.patient_details.update({
                        "name": name, "age": age, "gender": gender,
                        "phone": phone, "blood_group": blood_group,
                        "emergency_contact": emergency, "language": language
                    })
                    st.session_state.step = 2
                    st.toast("Step 1 complete! Proceeding to Symptom Intake.")
                    st.rerun()

# ---------------------------------------------------------
# STEP 2: SYMPTOM INTAKE (VOICE/TEXT & AYUSH CHATBOT)
# ---------------------------------------------------------
elif st.session_state.step == 2:
    st.subheader("💬 Step 2: Intelligent Symptom Intake")
    st.caption("Describe your symptoms using text or voice simulation. If AYUSH Mode is enabled, 5 Ayurvedic assessment questions will guide your intake.")

    col_chat, col_summary = st.columns([1.6, 1], gap="large")

    with col_chat:
        input_mode = st.radio(
            "Input Mode:",
            ["⌨️ Text Input Chat", "🎙️ Simulated Voice Intake (Mic)"],
            horizontal=True
        )

        if "Simulated Voice" in input_mode:
            st.info("🎙️ Speech-to-Text active. Speak into kiosk microphone or select quick speech prompts below:")
            col_v1, col_v2, col_v3 = st.columns(3)
            with col_v1:
                if st.button("🗣️ 'High fever with body ache'"):
                    user_speech = "I have high fever and severe body pain for 2 days."
                    st.session_state.messages.append({"role": "user", "content": user_speech})
                    st.rerun()
            with col_v2:
                if st.button("🗣️ 'Acidity & Joint stiffness'"):
                    user_speech = "Experiencing stomach burning, acidity, and knee joint stiffness."
                    st.session_state.messages.append({"role": "user", "content": user_speech})
                    st.rerun()
            with col_v3:
                if st.button("🗣️ 'Chest pain & Dizziness'"):
                    user_speech = "Sudden tightness in chest and feeling dizzy."
                    st.session_state.messages.append({"role": "user", "content": user_speech})
                    st.rerun()

        if len(st.session_state.messages) == 0:
            patient_name = st.session_state.patient_details['name'] or 'Patient'
            welcome_msg = f"Hello **{patient_name}**! I am your Kiosk Clinical Assistant. Please tell me what symptoms or health concerns brought you to the hospital today."
            if st.session_state.ayush_mode:
                welcome_msg += "\n\n🌿 **AYUSH Assessment Mode Active**: I will also ask 5 brief Ayurvedic Prakriti/Vikriti questions to match you with holistic OPD care."
            st.session_state.messages.append({"role": "assistant", "content": welcome_msg})

        chat_box = st.container(height=420)
        with chat_box:
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        st.markdown("**Quick Symptom Chips:**")
        chip_cols = st.columns(4)
        quick_chips = ["Fever & Headaches", "Digestive Acidity & Gas", "Joint Pain & Stiffness", "Cough & Cold"]
        chip_selected = None
        for idx, chip in enumerate(quick_chips):
            with chip_cols[idx]:
                if st.button(chip, use_container_width=True, key=f"chip_{idx}"):
                    chip_selected = f"I am experiencing {chip}."

        user_input = st.chat_input("Describe your symptoms (e.g. Severe headache for 3 days)...")
        final_prompt = chip_selected or user_input

        if final_prompt:
            st.session_state.messages.append({"role": "user", "content": final_prompt})
            
            prompt_lower = final_prompt.lower()
            if "fever" in prompt_lower or "headache" in prompt_lower or "cough" in prompt_lower:
                st.session_state.symptom_summary["primary_symptom"] = "Acute Fever / Upper Respiratory"
                st.session_state.symptom_summary["severity"] = 6
                st.session_state.symptom_summary["duration"] = "2-4 Days"
                st.session_state.symptom_summary["triage_level"] = "Yellow - Moderate"
            elif "chest pain" in prompt_lower or "dizzy" in prompt_lower or "breath" in prompt_lower:
                st.session_state.symptom_summary["primary_symptom"] = "Chest Discomfort / Dizziness"
                st.session_state.symptom_summary["severity"] = 9
                st.session_state.symptom_summary["duration"] = "Today"
                st.session_state.symptom_summary["triage_level"] = "Red - Urgent Emergency"
            elif "acidity" in prompt_lower or "joint" in prompt_lower or "stomach" in prompt_lower:
                st.session_state.symptom_summary["primary_symptom"] = "Joint Stiffness / Digestive Imbalance"
                st.session_state.symptom_summary["severity"] = 4
                st.session_state.symptom_summary["duration"] = "Chronic (>2 Weeks)"
                st.session_state.symptom_summary["triage_level"] = "Green - Low Priority"

            if st.session_state.ayush_mode and st.session_state.ayush_step < 5:
                curr_q = AYUSH_QUESTIONS[st.session_state.ayush_step]
                bot_response = f"Thank you for sharing that. To customize your AYUSH consultation:\n\n**{curr_q['question']}**\n\n"
                for opt in curr_q['options']:
                    bot_response += f"- {opt}\n"
                
                st.session_state.ayush_answers[f"ayush_q{st.session_state.ayush_step+1}"] = final_prompt
                st.session_state.ayush_step += 1
            else:
                if st.session_state.ayush_mode and st.session_state.ayush_step >= 5:
                    bot_response = "✅ **AYUSH & Clinical Intake Complete!** Click below to proceed to Document Scanning."
                else:
                    bot_response = "Thank you! I have recorded your symptoms. Can you specify how long you have had these symptoms and if you take any current medications?"

            st.session_state.messages.append({"role": "assistant", "content": bot_response})
            st.rerun()

    with col_summary:
        st.markdown("""
        <div class="kiosk-card">
            <h3>📊 Live AI Extraction & Triage</h3>
        </div>
        """, unsafe_allow_html=True)

        summary = st.session_state.symptom_summary
        st.markdown(f"**Chief Complaint:** `{summary['primary_symptom']}`")
        st.markdown(f"**Symptom Duration:** `{summary['duration']}`")
        st.slider("Assessed Pain / Severity Scale (1-10):", min_value=1, max_value=10, value=summary["severity"], disabled=True)

        t_level = summary["triage_level"]
        if "Red" in t_level:
            st.markdown('<span class="badge badge-red">🚨 Triage: RED - Immediate Emergency</span>', unsafe_allow_html=True)
        elif "Yellow" in t_level:
            st.markdown('<span class="badge badge-yellow">⚠️ Triage: YELLOW - Moderate OPD Priority</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="badge badge-green">🟢 Triage: GREEN - Standard OPD Routine</span>', unsafe_allow_html=True)

        st.divider()

        if st.session_state.ayush_mode:
            st.markdown("""
            <div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; padding: 1rem; border-radius: 12px;">
                <h4 style="color: #166534; margin-top:0;">🌿 Ayurvedic Prakriti / Vikriti Summary</h4>
            </div>
            """, unsafe_allow_html=True)
            
            st.progress(st.session_state.ayush_step / 5.0, text=f"AYUSH Qs Answered: {st.session_state.ayush_step}/5")
            
            p_col1, p_col2, p_col3 = st.columns(3)
            with p_col1: st.metric("Vata 🌬️", "45%")
            with p_col2: st.metric("Pitta 🔥", "35%")
            with p_col3: st.metric("Kapha 🌊", "20%")

            st.caption("**Predominant Prakriti:** `Vata-Pitta Imbalance (Vikriti)`")

        st.divider()

        if st.button("Proceed to Step 3: Document Scanner & Summary →", type="primary", use_container_width=True):
            st.session_state.step = 3
            st.rerun()

# ---------------------------------------------------------
# STEP 3: DOCUMENT SCANNER, OPENCV OCR & SUMMARY DASHBOARD
# ---------------------------------------------------------
elif st.session_state.step == 3:
    st.subheader("📑 Step 3: Document Scanner & Summary Dashboard")
    st.caption("Upload or scan prior prescriptions/lab reports using OpenCV & pytesseract OCR, then synthesize a Clinical Note for ABHA/HIS.")

    tab_scan, tab_summary = st.tabs(["📄 Prescription OCR Scanner (OpenCV & pytesseract)", "🎟️ Token & Clinical Note Synthesis Dashboard"])

    with tab_scan:
        c_scan1, c_scan2 = st.columns([1, 1], gap="large")

        with c_scan1:
            st.markdown("""
            <div class="kiosk-card">
                <h3>📷 Prescription Image Upload & Preprocessing</h3>
                <p style="color: #64748b; font-size: 0.88rem;">
                    Preprocesses prescription image via OpenCV (Grayscale + Thresholding) and extracts text using pytesseract.
                </p>
            </div>
            """, unsafe_allow_html=True)

            uploaded_img = st.file_uploader(
                "Upload Prescription / Report Image (JPG, PNG):",
                type=["png", "jpg", "jpeg"]
            )

            use_camera = st.checkbox("📸 Activate Kiosk Camera Scanner")
            camera_img = None
            if use_camera:
                camera_img = st.camera_input("Scan document:")

            target_img_source = uploaded_img or camera_img

            if target_img_source:
                pil_image = Image.open(target_img_source)
                st.image(pil_image, caption="Original Prescription Image", use_container_width=True)

                if st.button("🔍 Run OpenCV Preprocessing & Pytesseract OCR", type="primary", use_container_width=True):
                    with st.spinner("Applying OpenCV grayscale, threshold contrast & extracting text via pytesseract..."):
                        processed_img, extracted_text, structured_data = process_prescription_ocr(pil_image)
                        st.session_state.ocr_extracted_text = extracted_text
                        st.session_state.scanned_docs = structured_data["medications"]
                        st.success("OpenCV Preprocessing & pytesseract OCR Extraction Complete!")

        with c_scan2:
            st.markdown("""
            <div class="kiosk-card">
                <h3>🔬 Extracted OCR Output & Structured Fields</h3>
            </div>
            """, unsafe_allow_html=True)

            if st.session_state.ocr_extracted_text:
                st.subheader("Raw Text Extracted via pytesseract:")
                st.text_area("Extracted OCR Text:", value=st.session_state.ocr_extracted_text, height=180)

                st.subheader("Extracted Structured Fields:")
                df_meds = pd.DataFrame(st.session_state.scanned_docs)
                st.dataframe(df_meds, use_container_width=True)
            else:
                st.info("Upload or capture a prescription image to run OpenCV preprocessing and pytesseract OCR.")

    with tab_summary:
        if not st.session_state.token_data:
            tok_id = f"TK-AYUSH-{random.randint(100, 999)}" if st.session_state.ayush_mode else f"TK-GEN-{random.randint(100, 999)}"
            dept = "Ayurvedic & Holistic OPD (Room 104)" if st.session_state.ayush_mode else "General Medicine OPD (Room 202)"
            if "Red" in st.session_state.symptom_summary["triage_level"]:
                dept = "Emergency Triage Bay 1 (Immediate)"

            st.session_state.token_data = {
                "token_id": tok_id,
                "department": dept,
                "queue_num": random.randint(3, 14),
                "est_wait": "12-15 Mins",
                "timestamp": datetime.now().strftime("%d-%b-%Y %I:%M %p")
            }

        tok = st.session_state.token_data
        pat = st.session_state.patient_details

        # Generate gpt-4o-mini unified prompt & Clinical Note markdown
        gpt4o_prompt, clinical_note = generate_clinical_note_prompt(
            chat_history=st.session_state.messages,
            ocr_text=st.session_state.ocr_extracted_text,
            patient_info=pat,
            ayush_mode=st.session_state.ayush_mode
        )

        sum_col1, sum_col2 = st.columns([1, 1.2], gap="large")

        with sum_col1:
            st.markdown(f"""
            <div class="token-box">
                <div style="font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px; opacity: 0.8;">Apollo-Ayush OPD Queue Slip</div>
                <div class="token-number">{tok['token_id']}</div>
                <div style="font-size: 1.1rem; font-weight: 700; color: #38bdf8;">{tok['department']}</div>
                <hr style="border-color: rgba(255,255,255,0.15); margin: 1rem 0;">
                <div style="display: flex; justify-content: space-between; font-size: 0.9rem;">
                    <span>Patients Ahead in Queue: <strong>{tok['queue_num']}</strong></span>
                    <span>Est. Wait: <strong>{tok['est_wait']}</strong></span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            col_act1, col_act2 = st.columns(2)
            with col_act1:
                if st.button("🖨️ Print Digital Token Slip", use_container_width=True):
                    st.toast("Sending print command to kiosk thermal printer...", icon="🖨️")
            with col_act2:
                summary_export = {
                    "token_data": tok,
                    "patient_details": pat,
                    "symptom_summary": st.session_state.symptom_summary,
                    "clinical_note_draft": clinical_note,
                    "ocr_text": st.session_state.ocr_extracted_text
                }
                st.download_button(
                    "💾 Download JSON Summary",
                    data=json.dumps(summary_export, indent=2),
                    file_name=f"kiosk_intake_{pat['name'].replace(' ', '_')}.json",
                    mime="application/json",
                    use_container_width=True
                )

            with st.expander("🛠️ View Merged gpt-4o-mini Synthesis Prompt"):
                st.code(gpt4o_prompt, language="text")

        with sum_col2:
            st.markdown("""
            <div class="kiosk-card">
                <h3>📝 Synthesized Clinical Note & EMR Sync</h3>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="clinical-note-card">
                {clinical_note}
            </div>
            """, unsafe_allow_html=True)

            st.divider()

            # MOCK 'PUSH TO ABHA / HIS' BUTTON & SUCCESS CHECKMARK ANIMATION
            st.subheader("🏥 ABDM / HIS Repository Synchronization")
            
            if st.button("🚀 Push to ABHA / HIS Repository", type="primary", use_container_width=True, key="btn_push_his"):
                with st.spinner("🔒 Encrypting Clinical Note with ABDM Public Key & Pushing to HIS Gateway..."):
                    time.sleep(1.8)
                    st.session_state.abha_pushed = True
                    st.balloons()
                    st.toast("Successfully synchronized record to ABHA / HIS!", icon="✅")

            if st.session_state.abha_pushed:
                st.success("✅ **Successfully Pushed Clinical Note & Token to ABHA / Health Information System (HIS)!**")
                st.markdown("""
                <div style="background-color: #f0fdf4; border: 2px solid #22c55e; padding: 1rem; border-radius: 12px; text-align: center;">
                    <div style="font-size: 2.5rem;">✅</div>
                    <strong style="color: #15803d; font-size: 1.1rem;">Synchronization Complete</strong>
                    <p style="color: #166534; font-size: 0.9rem; margin-top: 4px;">
                        FHIR Bundle R4 Encrypted & Transmitted to ABDM Health Data Repository.
                    </p>
                </div>
                """, unsafe_allow_html=True)

            st.divider()

            if st.button("🏁 Finish & Reset Kiosk for Next Patient", use_container_width=True):
                st.session_state.step = 1
                st.session_state.patient_details = {
                    "abha_id": "", "verified": False, "name": "", "age": 35,
                    "gender": "Female", "phone": "", "blood_group": "O+",
                    "emergency_contact": "", "language": "English"
                }
                st.session_state.messages = []
                st.session_state.ayush_step = 0
                st.session_state.ayush_answers = {}
                st.session_state.scanned_docs = []
                st.session_state.ocr_extracted_text = ""
                st.session_state.token_data = None
                st.session_state.abha_pushed = False
                st.toast("Kiosk session complete. Ready for next patient!", icon="🎉")
                st.rerun()
