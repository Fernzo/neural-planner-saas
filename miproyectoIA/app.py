import streamlit as st
import google.generativeai as genai
import os
import uuid
from fpdf import FPDF
from PyPDF2 import PdfReader

# --- 1. CONFIGURACIÓN DE PÁGINA PREMIUM ---
st.set_page_config(
    page_title="Strategic AI Platform",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- 2. CSS AVANZADO (DISEÑO VISUAL DE ALTO NIVEL) ---
st.markdown("""
    <style>
    /* Importamos fuente moderna */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');

    /* Fondo general oscuro pero con matiz azulado muy sutil */
    .stApp {
        background-color: #0E1117;
        color: #E0E0E0;
        font-family: 'Inter', sans-serif;
    }

    /* Títulos con Gradiente (Efecto WOW) */
    h1 {
        background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        font-size: 2.5rem;
        padding-bottom: 10px;
    }

    /* Sidebar más profesional */
    [data-testid="stSidebar"] {
        background-color: #161B22;
        border-right: 1px solid #30363D;
    }
    
    /* Input del chat estilizado */
    .stTextInput>div>div>input {
        background-color: #21262D;
        color: white;
        border: 1px solid #30363D;
        border-radius: 10px;
        padding: 10px;
    }
    
    /* Botones de acción (Nuevo chat, etc) */
    .stButton>button {
        background-color: #238636; /* Verde GitHub */
        color: white;
        border: none;
        border-radius: 6px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #2EA043;
        box-shadow: 0 4px 12px rgba(46, 160, 67, 0.4);
    }
    
    /* Botones secundarios (Historial) */
    div[data-testid="stSidebar"] .stButton>button {
        background-color: transparent;
        border: 1px solid #30363D;
        color: #C9D1D9;
        text-align: left;
    }
    div[data-testid="stSidebar"] .stButton>button:hover {
        border-color: #58A6FF;
        color: #58A6FF;
    }

    /* MENSAJES DEL CHAT (Burbujas) */
    /* Usuario: Azul vibrante */
    [data-testid="stChatMessage"]:nth-child(odd) {
        background-color: rgba(31, 111, 235, 0.1); 
        border: 1px solid rgba(31, 111, 235, 0.2);
        border-radius: 10px;
    }
    /* IA: Gris oscuro limpio */
    [data-testid="stChatMessage"]:nth-child(even) {
        background-color: transparent;
    }

    /* Ocultar marcas de agua de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 3. GESTIÓN DE ESTADO (CEREBRO) ---
if "chats" not in st.session_state:
    st.session_state.chats = {} 
if "current_chat_id" not in st.session_state:
    new_id = str(uuid.uuid4())
    st.session_state.chats[new_id] = []
    st.session_state.current_chat_id = new_id
if "license_level" not in st.session_state:
    st.session_state.license_level = "GRATIS"
if "document_context" not in st.session_state:
    st.session_state.document_context = ""

# --- 4. FUNCIONES AUXILIARES ---
def create_new_chat():
    new_id = str(uuid.uuid4())
    st.session_state.chats[new_id] = []
    st.session_state.current_chat_id = new_id
    st.session_state.document_context = ""

def delete_chat(chat_id):
    if chat_id in st.session_state.chats:
        del st.session_state.chats[chat_id]
        if st.session_state.current_chat_id == chat_id:
            if len(st.session_state.chats) > 0:
                st.session_state.current_chat_id = list(st.session_state.chats.keys())[0]
            else:
                create_new_chat()

# --- 5. BARRA LATERAL (CONTROL PANEL) ---
with st.sidebar:
    # Encabezado con estilo
    st.markdown("### ⚡ Strategic AI `v4.0`")
    
    if st.button("✨ Nuevo Análisis", use_container_width=True, type="primary"):
        create_new_chat()
        st.rerun()

    st.markdown("---")
    st.caption("HISTORIAL DE SESIONES")
    
    # Lista de chats
    chat_ids = list(st.session_state.chats.keys())
    for chat_id in reversed(chat_ids):
        messages = st.session_state.chats[chat_id]
        chat_name = messages[0]["content"][:22] + "..." if messages else "Nueva Sesión"
        
        # Icono diferente si es el activo
        icon = "🟢" if chat_id == st.session_state.current_chat_id else "💭"
        
        col1, col2 = st.columns([0.85, 0.15])
        with col1:
            if st.button(f"{icon} {chat_name}", key=f"btn_{chat_id}"):
                st.session_state.current_chat_id = chat_id
                st.rerun()
        with col2:
            if st.button("✕", key=f"del_{chat_id}", help="Borrar"):
                delete_chat(chat_id)
                st.rerun()

    st.markdown("---")
    
    # Panel de Licencia con "Estado del Sistema" (Fake pero visual)
    with st.expander("🛠️ Panel de Control", expanded=True):
        license_key = st.text_input("License Key", type="password")
        
        if license_key == "PRO_USER":
            st.session_state.license_level = "PRO"
            st.success("💎 PLAN PRO: ACTIVO")
        elif license_key == "ULTRA_USER":
            st.session_state.license_level = "ULTRA"
            st.success("🚀 PLAN ULTRA: ACTIVO")
        else:
            st.session_state.license_level = "GRATIS"
            st.info("Plan Estándar (Limitado)")
            
        # Indicadores visuales
        st.markdown("**System Status:**")
        st.progress(100, text="Motor IA: Online")
        if st.session_state.license_level == "ULTRA":
            st.write("📂 **Analizador de Archivos**")
            uploaded_file = st.file_uploader("Sube PDF/TXT", type=["pdf", "txt"], label_visibility="collapsed")
            if uploaded_file:
                try:
                    if uploaded_file.type == "application/pdf":
                        reader = PdfReader(uploaded_file)
                        text = "\n".join([page.extract_text() for page in reader.pages])
                    else:
                        text = uploaded_file.read().decode("utf-8")
                    st.session_state.document_context = text
                    st.toast("✅ Datos cargados en memoria neural", icon="🧠")
                except Exception as e:
                    st.error(f"Error: {e}")

# --- 6. CONFIGURACIÓN DEL MOTOR IA (OPTIMIZADO PARA VELOCIDAD) ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    # CONFIGURACIÓN DE SEGURIDAD (Para que no se bloquee ni vaya lento)
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]
    
    # MODELO FLASH 1.5 (El más rápido y estable actualmente)
    model = genai.GenerativeModel('gemini-1.5-flash', safety_settings=safety_settings)

except Exception as e:
    st.error(f"⚠️ Error de Conexión: {e}")

# --- 7. INTERFAZ DE CHAT PRINCIPAL ---

# Recuperamos chat actual
current_id = st.session_state.current_chat_id
current_messages = st.session_state.chats[current_id]

# Título de bienvenida si está vacío
if not current_messages:
    st.markdown("""
    <div style="text-align: center; margin-top: 50px;">
        <h1>Strategic Consultant AI</h1>
        <p style="color: #888; font-size: 1.2rem;">Tu socio estratégico de alto rendimiento.</p>
    </div>
    """, unsafe_allow_html=True)

# Renderizar mensajes
for msg in current_messages:
    with st.chat_message(msg["role"], avatar="👤" if msg["role"]=="user" else "⚡"):
        st.markdown(msg["content"])

# Input de usuario
if prompt := st.chat_input("Escribe tu consulta estratégica..."):
    # Guardar y mostrar
    st.session_state.chats[current_id].append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    try:
        # Prompt Engineering según licencia
        system_instruction = "Eres un asistente útil."
        if st.session_state.license_level in ["PRO", "ULTRA"]:
            system_instruction = "Eres un Consultor Estratégico de Élite. Tus respuestas son tácticas, usan formato Markdown, tablas y listas. Ve al grano."
        
        context_data = ""
        if st.session_state.document_context:
            context_data = f"\n[DATOS DEL DOCUMENTO]:\n{st.session_state.document_context[:15000]}\n"

        history_context = "\n".join([f"{m['role']}: {m['content']}" for m in current_messages[-6:]])
        final_prompt = f"{system_instruction}\n{context_data}\nCHAT PREVIO:\n{history_context}\nUSUARIO ACTUAL: {prompt}"

        # Generación con Streaming (Efecto escritura)
        with st.chat_message("assistant", avatar="⚡"):
            response_placeholder = st.empty()
            full_response = ""
            # Stream activado para sensación de velocidad
            response = model.generate_content(final_prompt, stream=True)
            
            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    response_placeholder.markdown(full_response + "▌")
            
            response_placeholder.markdown(full_response)
            
        st.session_state.chats[current_id].append({"role": "assistant", "content": full_response})
        
        # Recarga sutil para actualizar nombre del chat en sidebar
        if len(current_messages) == 2: # Solo recargar si es el primer mensaje para ponerle nombre
            st.rerun()

    except Exception as e:
        st.error(f"Error del sistema: {e}")

# Botón de exportación (Discreto)
if st.session_state.license_level in ["PRO", "ULTRA"] and current_messages:
    st.markdown("---")
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("📥 Descargar Informe PDF", use_container_width=True):
            # Lógica de PDF simplificada para evitar errores
            try:
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=10)
                pdf.cell(0, 10, txt="INFORME ESTRATÉGICO", ln=True, align='C')
                for m in current_messages:
                    role = "USER" if m["role"]=="user" else "AI"
                    clean_text = m["content"].encode('latin-1', 'replace').decode('latin-1')
                    pdf.multi_cell(0, 5, txt=f"\n[{role}]\n{clean_text}")
                
                html = pdf.output(dest='S').encode('latin-1')
                st.download_button("Guardar PDF", html, "informe.pdf", "application/pdf")
            except:
                st.error("Error generando PDF (caracteres no compatibles).")
