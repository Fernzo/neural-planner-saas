import streamlit as st
import google.generativeai as genai
import os
from fpdf import FPDF
from PyPDF2 import PdfReader
import io

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Strategic Consultant AI",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILO CSS MINIMALISTA (Dark Mode) ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; font-family: 'Inter', sans-serif; }
    [data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #30363D; }
    .stTextInput>div>div>input { background-color: #0E1117; color: white; border: 1px solid #30363D; }
    .stButton>button { background-color: #238636; color: white; border: none; border-radius: 6px; }
    .stButton>button:hover { background-color: #2ea043; }
    
    /* Mensajes del Chat */
    .user-msg { background-color: #1F6FEB; color: white; padding: 10px; border-radius: 8px; margin: 5px 0 5px 20%; text-align: right; }
    .ai-msg { background-color: #21262D; color: #E6EDF3; padding: 10px; border-radius: 8px; margin: 5px 20% 5px 0; border: 1px solid #30363D; }
    </style>
    """, unsafe_allow_html=True)

# --- GESTIÓN DE ESTADO ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "license_level" not in st.session_state:
    st.session_state.license_level = "GRATIS"
if "document_context" not in st.session_state:
    st.session_state.document_context = ""

# --- BARRA LATERAL (Licencias y Archivos) ---
with st.sidebar:
    st.title("🧠 Strategic AI")
    st.caption("v2.0 - Powered by Gemini Flash")
    st.markdown("---")
    
    # Sistema de Licencias
    license_key = st.text_input("License Key", type="password")
    
    if license_key == "PRO_USER":
        st.session_state.license_level = "PRO"
        st.success("💎 PLAN PRO ACTIVO")
    elif license_key == "ULTRA_USER":
        st.session_state.license_level = "ULTRA"
        st.success("🚀 PLAN ULTRA ACTIVO")
    else:
        st.session_state.license_level = "GRATIS"
        st.info("Plan Estándar")

    # Subida de Archivos (Solo ULTRA)
    if st.session_state.license_level == "ULTRA":
        st.markdown("---")
        st.write("📂 **Analista de Documentos**")
        uploaded_file = st.file_uploader("Sube PDF o TXT", type=["pdf", "txt"])
        
        if uploaded_file:
            try:
                if uploaded_file.type == "application/pdf":
                    reader = PdfReader(uploaded_file)
                    text = "\n".join([page.extract_text() for page in reader.pages])
                else:
                    text = uploaded_file.read().decode("utf-8")
                
                st.session_state.document_context = text
                st.toast("Documento indexado con éxito!", icon="✅")
            except Exception as e:
                st.error(f"Error leyendo archivo: {e}")

    st.markdown("---")
    if st.button("🗑️ Borrar Historial"):
        st.session_state.messages = []
        st.session_state.document_context = ""
        st.rerun()

# --- MOTOR DE INTELIGENCIA ARTIFICIAL ---
try:
    # Configuración Segura
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    # USA EL MODELO QUE VIMOS EN TU LISTA (EL MÁS RÁPIDO Y NUEVO)
    model = genai.GenerativeModel('gemini-2.0-flash')

except Exception as e:
    st.error(f"❌ Error de configuración: {e}")

# --- INTERFAZ DE CHAT ---
st.markdown("### Asistente Estratégico IA")

# Mostrar historial
for msg in st.session_state.messages:
    css_class = "user-msg" if msg["role"] == "user" else "ai-msg"
    st.markdown(f"<div class='{css_class}'>{msg['content']}</div>", unsafe_allow_html=True)

# Input de usuario
if prompt := st.chat_input("Escribe tu consulta estratégica aquí..."):
    # 1. Guardar y mostrar mensaje usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

# Respuesta de la IA (se ejecuta al recargar)
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    with st.spinner("💡 Analizando estrategia..."):
        try:
            # Preparar contexto
            user_msg = st.session_state.messages[-1]["content"]
            system_instruction = "Eres un consultor experto. Responde de forma breve y profesional."
            
            if st.session_state.license_level in ["PRO", "ULTRA"]:
                system_instruction = "Eres un Consultor Estratégico Senior. Usa formato Markdown, listas y tablas."
            
            context_data = ""
            if st.session_state.document_context:
                context_data = f"\nCONTEXTO DEL DOCUMENTO:\n{st.session_state.document_context[:10000]}\n"

            final_prompt = f"{system_instruction}\n{context_data}\nUSUARIO: {user_msg}"

            # Generar respuesta
            response = model.generate_content(final_prompt)
            ai_reply = response.text
            
            st.session_state.messages.append({"role": "assistant", "content": ai_reply})
            st.rerun()
            
        except Exception as e:
            st.error(f"⚠️ Error al generar respuesta: {e}")

# --- EXPORTAR A PDF (Solo PRO/ULTRA) ---
if st.session_state.license_level in ["PRO", "ULTRA"] and len(st.session_state.messages) > 0:
    st.markdown("---")
    if st.button("📄 Descargar Informe PDF"):
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt="Informe Estratégico IA", ln=True, align='C')
            pdf.ln(10)
            
            for msg in st.session_state.messages:
                role = "USUARIO" if msg["role"] == "user" else "IA"
                text = f"{role}: {msg['content']}\n\n"
                # Limpieza básica de caracteres para FPDF
                safe_text = text.encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 10, txt=safe_text)
            
            pdf_output = pdf.output(dest='S').encode('latin-1')
            st.download_button("⬇️ Guardar PDF", data=pdf_output, file_name="informe_ia.pdf", mime="application/pdf")
        except Exception as e:
            st.warning("Nota: La exportación PDF básica no soporta algunos caracteres especiales (emojis).")
