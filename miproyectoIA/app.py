import streamlit as st
import google.generativeai as genai
import os
from fpdf import FPDF
from PyPDF2 import PdfReader
import io

# Configuración de la página (Minimalista y Profesional)
st.set_page_config(
    page_title="Strategic Consultant AI",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo CSS Minimalista (Dark Mode Puro)
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .stApp {
        background-color: #0E1117;
        color: #FFFFFF;
        font-family: 'Inter', sans-serif;
    }
    
    [data-testid="stSidebar"] {
        background-color: #161B22;
        border-right: 1px solid #30363D;
    }
    
    .chat-container {
        max-width: 800px;
        margin: 0 auto;
    }
    
    .message {
        padding: 1rem 1.5rem;
        border-radius: 4px;
        margin-bottom: 1rem;
        line-height: 1.6;
        font-size: 0.95rem;
    }
    
    .user-msg {
        background-color: #1A73E8;
        color: #FFFFFF;
        margin-left: 20%;
        border: 1px solid #1A73E8;
    }
    
    .assistant-msg {
        background-color: #262730;
        color: #E6EDF3;
        margin-right: 20%;
        border: 1px solid #30363D;
    }
    
    .stTextInput>div>div>input {
        background-color: #0E1117;
        color: white;
        border: 1px solid #30363D;
    }
    
    .stButton>button {
        background-color: #21262D;
        color: #C9D1D9;
        border: 1px solid #30363D;
        border-radius: 4px;
        font-weight: 500;
        width: 100%;
    }
    
    .stButton>button:hover {
        background-color: #30363D;
        border-color: #8B949E;
    }

    div[data-testid="stExpander"] {
        background-color: #161B22;
        border: 1px solid #30363D;
    }
    </style>
    """, unsafe_allow_html=True)

# Inicialización de estado
if "messages" not in st.session_state:
    st.session_state.messages = []
if "license_level" not in st.session_state:
    st.session_state.license_level = "GRATIS"
if "document_context" not in st.session_state:
    st.session_state.document_context = ""

# Sidebar
with st.sidebar:
    st.title("Strategic AI")
    st.markdown("---")
    
    license_key = st.text_input("License Key", type="password", placeholder="Enter key...")
    
    if license_key == "PRO_USER":
        st.session_state.license_level = "PRO"
        st.info("PRO Access Verified")
    elif license_key == "ULTRA_USER":
        st.session_state.license_level = "ULTRA"
        st.info("ULTRA Access Verified")
    else:
        st.session_state.license_level = "GRATIS"
        st.text("Standard Access")

    if st.session_state.license_level == "ULTRA":
        st.markdown("---")
        uploaded_file = st.file_uploader("Data Source (PDF/TXT)", type=["pdf", "txt"])
        if uploaded_file:
            if uploaded_file.type == "application/pdf":
                reader = PdfReader(uploaded_file)
                st.session_state.document_context = "\n".join([p.extract_text() for p in reader.pages])
            else:
                st.session_state.document_context = uploaded_file.read().decode("utf-8")
            st.success("Data Indexed")

    st.markdown("---")
    if st.button("Clear Session"):
        st.session_state.messages = []
        st.session_state.document_context = ""
        st.rerun()

# Configuración IA (Uso de gemini-pro para estabilidad)
import os
# En lugar de poner la clave directa:
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# Selección de modelo con fallback
# --- BLOQUE DE CONEXIÓN ROBUSTA (ANTI-ERRORES) ---
try:
    # Intentamos conectar con el modelo más rápido primero
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    try:
        # Si falla, probamos el clásico
        model = genai.GenerativeModel('gemini-pro')
    except:
        # Si todo falla, intentamos el backup
        model = genai.GenerativeModel('gemini-1.0-pro')

# ------------------------------------------------

def get_system_prompt():
    if st.session_state.license_level == "ULTRA":
        return "Eres un Consultor Estratégico de alto nivel. Tus respuestas son directas, ejecutivas y estructuradas en tablas o listas. No uses saludos cordiales excesivos."
    elif st.session_state.license_level == "PRO":
        return "Eres un asistente profesional avanzado. Proporciona respuestas detalladas y estructuradas."
    return "Eres un asistente profesional. Responde de forma concisa."

# Interfaz Principal
st.markdown("### Strategic Consultant AI")
st.markdown(f"Access Level: {st.session_state.license_level}")

# Chat History
for message in st.session_state.messages:
    div_class = "user-msg" if message["role"] == "user" else "assistant-msg"
    st.markdown(f'<div class="message {div_class}">{message["content"]}</div>', unsafe_allow_html=True)

# Chat Input
if prompt := st.chat_input("Input command..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Preparar Prompt Final
    system_instruction = get_system_prompt()
    context = f"\nContext: {st.session_state.document_context[:10000]}" if st.session_state.document_context else ""
    final_prompt = f"{system_instruction}{context}\n\nUser: {prompt}"

    try:
        with st.spinner("Processing..."):
            response = model.generate_content(final_prompt)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            st.rerun()
    except Exception as e:
        # ESTO ES EL CHIVATO
        st.error(f"⚠️ ERROR REAL: {str(e)}")
        st.write(e) # Esto imprime detalles técnicos

# Export functionality for PRO/ULTRA
if st.session_state.license_level in ["PRO", "ULTRA"] and st.session_state.messages:
    if st.button("Export Report (PDF)"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=10)
        pdf.cell(200, 10, txt="Strategic Report", ln=True, align='L')
        pdf.ln(5)
        
        last_msg = st.session_state.messages[-1]["content"]
        safe_text = last_msg.encode('latin-1', 'ignore').decode('latin-1')
        pdf.multi_cell(0, 8, txt=safe_text)
        
        pdf_bytes = pdf.output(dest='S')
        st.download_button(
            label="Download PDF",
            data=pdf_bytes,
            file_name="strategic_report.pdf",
            mime="application/pdf"
        )








