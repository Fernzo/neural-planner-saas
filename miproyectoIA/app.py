import streamlit as st
import google.generativeai as genai
import os
import uuid
from fpdf import FPDF
from PyPDF2 import PdfReader

# --- 1. CONFIGURACIÓN ---
st.set_page_config(
    page_title="Strategic AI Platform",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- 2. CSS (LIMPIEZA TOTAL - SIN CAJAS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');

    /* Fondo oscuro limpio */
    .stApp {
        background-color: #0E1117;
        color: #E6E6E6;
        font-family: 'Inter', sans-serif;
    }

    /* Título con gradiente sutil */
    h1 {
        background: linear-gradient(90deg, #FFFFFF 0%, #888888 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 600;
    }

    /* ELIMINAR CAJAS DE MENSAJES */
    [data-testid="stChatMessage"] {
        background-color: transparent !important;
        border: none !important;
        padding: 1rem 0 !important; /* Espacio vertical entre mensajes */
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
        border-radius: 8px;
    }
    
    /* Ocultar elementos extra */
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

# --- 5. SIDEBAR ---
with st.sidebar:
    st.markdown("### ⚡ Strategic AI")
    if st.button("Nuevo Chat", use_container_width=True, type="primary"):
        create_new_chat()
        st.rerun()
    
    st.markdown("---")
    
    # Historial minimalista
    chat_ids = list(st.session_state.chats.keys())
    for chat_id in reversed(chat_ids):
        msgs = st.session_state.chats[chat_id]
        name = msgs[0]["content"][:20] + "..." if msgs else "Nueva Sesión"
        icon = "🔹" if chat_id == st.session_state.current_chat_id else "▫️"
        
        c1, c2 = st.columns([0.85, 0.15])
        with c1:
            if st.button(f"{icon} {name}", key=f"b_{chat_id}"):
                st.session_state.current_chat_id = chat_id
                st.rerun()
        with c2:
            if st.button("×", key=f"d_{chat_id}"):
                delete_chat(chat_id)
                st.rerun()

    st.markdown("---")
    with st.expander("Ajustes"):
        key = st.text_input("Licencia", type="password")
        if key == "ULTRA_USER":
            st.session_state.license_level = "ULTRA"
            st.success("ULTRA ACTIVO")
        elif key == "PRO_USER":
            st.session_state.license_level = "PRO"
            st.success("PRO ACTIVO")
            
        if st.session_state.license_level == "ULTRA":
            up = st.file_uploader("Contexto PDF", type=["pdf"])
            if up:
                try:
                    r = PdfReader(up)
                    st.session_state.document_context = "\n".join([p.extract_text() for p in r.pages])
                    st.toast("Datos cargados")
                except: pass

# --- 6. MOTOR IA ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    safety = [{"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
              {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
              {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
              {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}]
    model = genai.GenerativeModel('gemini-1.5-flash', safety_settings=safety)
except: st.error("Error API")

# --- 7. CHAT ---
curr_id = st.session_state.current_chat_id
curr_msgs = st.session_state.chats[curr_id]

if not curr_msgs:
    st.markdown("<h1 style='text-align: center; margin-top: 100px; color: #444;'>Strategic AI</h1>", unsafe_allow_html=True)

for msg in curr_msgs:
    # AVATARES: Puedes cambiar los emojis aquí si quieres
    av = "🧑‍💻" if msg["role"]=="user" else "🧠"
    with st.chat_message(msg["role"], avatar=av):
        st.markdown(msg["content"])

if prompt := st.chat_input("..."):
    st.session_state.chats[curr_id].append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(prompt)

    try:
        sys_prompt = "Eres un consultor experto. Sé directo y profesional."
        if st.session_state.license_level in ["PRO", "ULTRA"]:
            sys_prompt += " Usa Markdown avanzado."
            
        ctx = f"CONTEXTO:\n{st.session_state.document_context[:10000]}" if st.session_state.document_context else ""
        hist = "\n".join([f"{m['role']}: {m['content']}" for m in curr_msgs[-6:]])
        
        with st.chat_message("assistant", avatar="🧠"):
            box = st.empty()
            full = ""
            resp = model.generate_content(f"{sys_prompt}\n{ctx}\n{hist}\nUSER: {prompt}", stream=True)
            for chunk in resp:
                if chunk.text:
                    full += chunk.text
                    box.markdown(full + "▌")
            box.markdown(full)
            
        st.session_state.chats[curr_id].append({"role": "assistant", "content": full})
        if len(curr_msgs) == 2: st.rerun() # Actualizar nombre chat
    except Exception as e:
        st.error(str(e))

