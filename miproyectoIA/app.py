import streamlit as st
import google.generativeai as genai
import os
from fpdf import FPDF
from PyPDF2 import PdfReader

# --- CONFIGURACIÓN DE PÁGINA (ESTILO CHATGPT) ---
st.set_page_config(
    page_title="Strategic AI",
    page_icon="🧠",
    layout="centered",  # Centrado como ChatGPT, no 'wide' que lo estira demasiado
    initial_sidebar_state="expanded"
)

# --- CSS PARA LIMPIEZA VISUAL (LOOK & FEEL CHATGPT) ---
st.markdown("""
    <style>
    /* Fondo principal oscuro */
    .stApp { background-color: #343541; color: #ECECF1; }
    
    /* Ocultar elementos de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Estilo del Input (abajo) */
    .stTextInput>div>div>input {
        background-color: #40414F;
        color: white;
        border: 1px solid #565869;
        border-radius: 12px;
    }
    
    /* Sidebar estilo oscuro */
    [data-testid="stSidebar"] {
        background-color: #202123;
        border-right: 1px solid #4D4D4F;
    }
    
    /* Ajustes de texto */
    h1, h2, h3 { color: #ECECF1; font-family: 'Söhne', sans-serif; }
    p { font-size: 16px; line-height: 1.6; }
    </style>
    """, unsafe_allow_html=True)

# --- GESTIÓN DE ESTADO ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "license_level" not in st.session_state:
    st.session_state.license_level = "GRATIS"
if "document_context" not in st.session_state:
    st.session_state.document_context = ""

# --- BARRA LATERAL (MENU) ---
with st.sidebar:
    st.title("🧠 Neural Planner")
    st.caption("Strategic Consultant v2.1")
    st.markdown("---")
    
    # Login
    license_key = st.text_input("Clave de Acceso", type="password", placeholder="Introduce tu clave...")
    
    if license_key == "PRO_USER":
        st.session_state.license_level = "PRO"
        st.success("💎 MODO PRO ACTIVO")
    elif license_key == "ULTRA_USER":
        st.session_state.license_level = "ULTRA"
        st.success("🚀 MODO ULTRA ACTIVO")
    else:
        st.session_state.license_level = "GRATIS"
        st.info("Plan Básico")

    # Módulo de Archivos (Solo ULTRA)
    if st.session_state.license_level == "ULTRA":
        st.markdown("---")
        st.write("📂 **Contexto (PDF/TXT)**")
        uploaded_file = st.file_uploader("Analizar documento", type=["pdf", "txt"], label_visibility="collapsed")
        
        if uploaded_file:
            try:
                if uploaded_file.type == "application/pdf":
                    reader = PdfReader(uploaded_file)
                    text = "\n".join([page.extract_text() for page in reader.pages])
                else:
                    text = uploaded_file.read().decode("utf-8")
                
                st.session_state.document_context = text
                st.toast("✅ Documento asimilado en memoria")
            except Exception as e:
                st.error(f"Error de lectura: {e}")

    st.markdown("---")
    if st.button("🗑️ Nuevo Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.document_context = ""
        st.rerun()

# --- MOTOR IA (CONEXIÓN) ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    # Usamos el modelo robusto que funcionó
    model = genai.GenerativeModel('gemini-flash-latest')
except Exception as e:
    st.error(f"❌ Error de conexión: {e}")

# --- INTERFAZ PRINCIPAL (ESTILO CHATGPT NATIVO) ---

# Título discreto
if not st.session_state.messages:
    st.markdown("<h1 style='text-align: center; margin-top: 50px;'>¿En qué puedo ayudarte hoy?</h1>", unsafe_allow_html=True)

# 1. MOSTRAR MENSAJES ANTERIORES
# Usamos st.chat_message que crea el formato avatar + texto automáticamente
for msg in st.session_state.messages:
    role = msg["role"]
    # Iconos personalizados
    avatar = "👤" if role == "user" else "🧠"
    
    with st.chat_message(role, avatar=avatar):
        st.markdown(msg["content"])

# 2. CAPTURA DE INPUT Y RESPUESTA
if prompt := st.chat_input("Envía un mensaje..."):
    # Guardar y mostrar mensaje usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
