import streamlit as st
import google.generativeai as genai
import os
import uuid
from fpdf import FPDF
from PyPDF2 import PdfReader

# --- 1. CONFIGURACIÓN (SIN EMOJIS) ---
st.set_page_config(
    page_title="Strategic AI Platform",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- 2. CSS (ESTILO CORPORATIVO SOBRIO) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');

    /* Fondo oscuro corporativo */
    .stApp {
        background-color: #0E1117;
        color: #E6E6E6;
        font-family: 'Inter', sans-serif;
    }

    /* Título elegante */
    h1 {
        background: linear-gradient(90deg, #FFFFFF 0%, #999999 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 600;
        letter-spacing: -1px;
    }

    /* MENSAJES: LIMPIEZA TOTAL */
    [data-testid="stChatMessage"] {
        background-color: transparent !important;
        border: none !important;
        padding: 1.5rem 0 !important;
    }
    
    /* Iconos de usuario/IA por defecto (Grises y limpios) */
    [data-testid="stChatMessageAvatar"] {
        background-color: #1F242D !important;
        border: 1px solid #30363D;
    }

    /* Sidebar oscuro */
    [data-testid="stSidebar"] {
        background-color: #161B22;
        border-right: 1px solid #30363D;
    }
    
    /* Input limpio */
    .stTextInput>div>div>input {
        background-color: #21262D;
        color: white;
        border: 1px solid #30363D;
        border-radius: 6px;
    }
    
    /* Botones Sidebar (Texto plano) */
    .stButton>button {
        border-radius: 4px;
        text-transform: uppercase;
        font-size: 0.8rem;
        letter-spacing: 0.05em;
        font-weight: 600;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 3. ESTADO ---
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

# --- 4. FUNCIONES ---
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

# --- 5. SIDEBAR (TEXTO PURO) ---
with st.sidebar:
    st.markdown("### STRATEGIC AI")
    st.caption("v2.1 Enterprise")
    
    if st.button("NUEVA SESIÓN", use_container_width=True, type="primary"):
        create_new_chat()
        st.rerun()
    
    st.markdown("---")
    st.caption("HISTORIAL")
    
    # Historial limpio
    chat_ids = list(st.session_state.chats.keys())
    for chat_id in reversed(chat_ids):
        msgs = st.session_state.chats[chat_id]
        name = msgs[0]["content"][:20] + "..." if msgs else "Sesión Vacía"
        
        # Indicador de selección simple (•)
        indicator = "•" if chat_id == st.session_state.current_chat_id else ""
        label = f"{indicator} {name}"
        
        c1, c2 = st.columns([0.85, 0.15])
        with c1:
            if st.button(label, key=f"b_{chat_id}"):
                st.session_state.current_chat_id = chat_id
                st.rerun()
        with c2:
            if st.button("x", key=f"d_{chat_id}"):
                delete_chat(chat_id)
                st.rerun()

    st.markdown("---")
    with st.expander("SISTEMA"):
        key = st.text_input("Licencia", type="password")
        if key == "ULTRA_USER":
            st.session_state.license_level = "ULTRA"
            st.success("ULTRA HABILITADO")
        elif key == "PRO_USER":
            st.session_state.license_level = "PRO"
            st.success("PRO HABILITADO")
            
        if st.session_state.license_level == "ULTRA":
            up = st.file_uploader("Cargar Contexto (PDF)", type=["pdf"])
            if up:
                try:
                    r = PdfReader(up)
                    st.session_state.document_context = "\n".join([p.extract_text() for p in r.pages])
                    st.success("Datos cargados en memoria")
                except: pass

# --- 6. MOTOR IA (CONFIGURADO CON EL MODELO QUE FUNCIONA) ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    safety = [{"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
              {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
              {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
              {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}]
    
    # Usamos gemini-flash-latest que es el que tu cuenta reconoce
    model = genai.GenerativeModel('gemini-flash-latest', safety_settings=safety)

except: st.error("Error de conexión con API")

# --- 7. CHAT (LÓGICA DE AVATARES ROBUSTA) ---
curr_id = st.session_state.current_chat_id
curr_msgs = st.session_state.chats[curr_id]

# 1. BUSCAMOS LOS LOGOS DONDE REALMENTE ESTÁN (Junto a app.py)
# Obtenemos la ruta exacta de este archivo script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construimos la ruta completa a las imágenes
user_img_path = os.path.join(script_dir, "user_icon.png")
ai_img_path = os.path.join(script_dir, "ai_icon.png")

# 2. DEFINIMOS LOS AVATARES
# Si encuentra el archivo, usa la imagen. Si no, usa None (Icono gris default de Streamlit, NO emoji)
user_avatar = user_img_path if os.path.exists(user_img_path) else None
ai_avatar = ai_img_path if os.path.exists(ai_img_path) else None

# Verificación silenciosa (para ti): Si quieres saber si fallan, descomenta esto:
# if not user_avatar: st.toast("⚠️ No encuentro user_icon.png", icon="❌")

if not curr_msgs:
    st.markdown("<h1 style='text-align: center; margin-top: 100px; color: #666;'>Strategic AI</h1>", unsafe_allow_html=True)

for msg in curr_msgs:
    # Asignar avatar correcto
    avatar_use = user_avatar if msg["role"] == "user" else ai_avatar
    with st.chat_message(msg["role"], avatar=avatar_use):
        st.markdown(msg["content"])

if prompt := st.chat_input("Escriba su consulta..."):
    st.session_state.chats[curr_id].append({"role": "user", "content": prompt})
    
    # Mostrar input usuario con su logo
    with st.chat_message("user", avatar=user_avatar):
        st.markdown(prompt)

    try:
        sys_prompt = "Eres un consultor experto. Sé directo y profesional."
        if st.session_state.license_level in ["PRO", "ULTRA"]:
            sys_prompt += " Usa Markdown avanzado, tablas y listas."
            
        ctx = f"CONTEXTO:\n{st.session_state.document_context[:10000]}" if st.session_state.document_context else ""
        hist = "\n".join([f"{m['role']}: {m['content']}" for m in curr_msgs[-6:]])
        
        # Mostrar respuesta IA con su logo
        with st.chat_message("assistant", avatar=ai_avatar):
            box = st.empty()
            full = ""
            resp = model.generate_content(f"{sys_prompt}\n{ctx}\n{hist}\nUSER: {prompt}", stream=True)
            for chunk in resp:
                if chunk.text:
                    full += chunk.text
                    box.markdown(full + "▌")
            box.markdown(full)
            
        st.session_state.chats[curr_id].append({"role": "assistant", "content": full})
        if len(curr_msgs) == 2: st.rerun() 
    except Exception as e:
        st.error(str(e))

# --- 8. EXPORTAR A PDF (ESTO SE HABÍA BORRADO) ---
if st.session_state.license_level in ["PRO", "ULTRA"] and curr_msgs:
    st.markdown("---")
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("📥 DESCARGAR INFORME", use_container_width=True):
            try:
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=10)
                pdf.cell(0, 10, txt="INFORME ESTRATÉGICO", ln=True, align='C')
                
                for m in curr_msgs:
                    role = "CLIENTE" if m["role"]=="user" else "CONSULTOR"
                    # Limpieza técnica para evitar errores de caracteres raros
                    clean_text = m["content"].encode('latin-1', 'replace').decode('latin-1')
                    
                    pdf.set_font("Arial", 'B', 10)
                    pdf.cell(0, 8, txt=role, ln=True)
                    pdf.set_font("Arial", '', 10)
                    pdf.multi_cell(0, 5, txt=clean_text)
                    pdf.ln(4)
                
                html = pdf.output(dest='S').encode('latin-1')
                st.download_button("Guardar PDF", html, "informe_estrategico.pdf", "application/pdf")
            except Exception as e:
                st.error(f"Error generando PDF: {e}")

