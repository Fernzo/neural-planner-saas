import streamlit as st
import google.generativeai as genai
import os
import uuid
from fpdf import FPDF
from PyPDF2 import PdfReader

# --- CONFIGURACIÓN DE PÁGINA (ESTILO CHATGPT) ---
st.set_page_config(
    page_title="Strategic AI",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- CSS MEJORADO (LOOK & FEEL CHATGPT) ---
st.markdown("""
    <style>
    /* Fondo oscuro y limpio */
    .stApp { background-color: #343541; color: #ECECF1; }
    
    /* Ocultar elementos de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Estilo del Input (Chatbox) */
    .stTextInput>div>div>input {
        background-color: #40414F;
        color: white;
        border: 1px solid #565869;
        border-radius: 12px;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #202123;
        border-right: 1px solid #4D4D4F;
    }
    
    /* Botones del Sidebar (Historial) */
    .stButton>button {
        background-color: transparent;
        color: #ECECF1;
        border: 1px solid #4D4D4F;
        width: 100%;
        text-align: left;
        margin-bottom: 5px;
    }
    .stButton>button:hover {
        background-color: #2A2B32;
        border-color: #ECECF1;
    }

    h1, h2, h3 { font-family: 'Söhne', sans-serif; }
    </style>
    """, unsafe_allow_html=True)

# --- GESTIÓN DE MEMORIA (SISTEMA MULTI-CHAT) ---
if "chats" not in st.session_state:
    # Aquí guardamos TODOS los chats: { "id_chat": [mensajes], ... }
    st.session_state.chats = {} 

if "current_chat_id" not in st.session_state:
    # Creamos el primer chat por defecto
    new_id = str(uuid.uuid4())
    st.session_state.chats[new_id] = []
    st.session_state.current_chat_id = new_id

if "license_level" not in st.session_state:
    st.session_state.license_level = "GRATIS"
if "document_context" not in st.session_state:
    st.session_state.document_context = ""

# --- FUNCIONES DE GESTIÓN ---
def create_new_chat():
    new_id = str(uuid.uuid4())
    st.session_state.chats[new_id] = []
    st.session_state.current_chat_id = new_id
    st.session_state.document_context = "" # Reseteamos contexto de documento para el nuevo chat

def delete_chat(chat_id):
    if chat_id in st.session_state.chats:
        del st.session_state.chats[chat_id]
        # Si borramos el actual, creamos uno nuevo o saltamos a otro
        if st.session_state.current_chat_id == chat_id:
            if len(st.session_state.chats) > 0:
                st.session_state.current_chat_id = list(st.session_state.chats.keys())[0]
            else:
                create_new_chat()

# --- BARRA LATERAL (MENU & HISTORIAL) ---
with st.sidebar:
    st.title("🧠 Neural Planner")
    
    # 1. BOTÓN NUEVO CHAT (Principal)
    if st.button("➕ Nuevo Chat", use_container_width=True, type="primary"):
        create_new_chat()
        st.rerun()

    st.markdown("---")
    st.caption("Historial de Sesión")
    
    # 2. LISTA DE CHATS (Historial)
    # Recorremos los chats guardados y creamos un botón para cada uno
    chat_ids = list(st.session_state.chats.keys())
    # Invertimos para que el más nuevo salga arriba
    for chat_id in reversed(chat_ids):
        messages = st.session_state.chats[chat_id]
        
        # Ponemos un nombre bonito al botón (ej: Primeros 20 caracteres del primer mensaje)
        if messages:
            chat_name = messages[0]["content"][:25] + "..."
        else:
            chat_name = "Chat Vacío"
            
        # Estilo visual si es el chat activo
        if chat_id == st.session_state.current_chat_id:
            label = f"🟢 {chat_name}"
        else:
            label = f"💬 {chat_name}"
            
        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            if st.button(label, key=f"btn_{chat_id}"):
                st.session_state.current_chat_id = chat_id
                st.rerun()
        with col2:
            if st.button("x", key=f"del_{chat_id}"):
                delete_chat(chat_id)
                st.rerun()

    st.markdown("---")
    
    # 3. LICENCIAS (Abajo del todo)
    with st.expander("🔐 Licencia & Acceso"):
        license_key = st.text_input("Clave", type="password")
        if license_key == "PRO_USER":
            st.session_state.license_level = "PRO"
            st.success("💎 PRO")
        elif license_key == "ULTRA_USER":
            st.session_state.license_level = "ULTRA"
            st.success("🚀 ULTRA")
        else:
            st.session_state.license_level = "GRATIS"
            st.info("Básico")
            
        # Módulo de Archivos (Solo ULTRA)
        if st.session_state.license_level == "ULTRA":
            st.write("📂 **Subir Contexto**")
            uploaded_file = st.file_uploader("", type=["pdf", "txt"], label_visibility="collapsed")
            if uploaded_file:
                try:
                    if uploaded_file.type == "application/pdf":
                        reader = PdfReader(uploaded_file)
                        text = "\n".join([page.extract_text() for page in reader.pages])
                    else:
                        text = uploaded_file.read().decode("utf-8")
                    st.session_state.document_context = text
                    st.toast("Documento indexado en este chat")
                except Exception as e:
                    st.error(f"Error: {e}")

# --- MOTOR IA ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-flash-latest')
except Exception as e:
    st.error(f"Error conexión: {e}")

# --- INTERFAZ PRINCIPAL ---

# Identificamos el chat actual
current_id = st.session_state.current_chat_id
current_messages = st.session_state.chats[current_id]

# Mensaje de bienvenida si está vacío
if not current_messages:
    st.markdown("<h1 style='text-align: center; margin-top: 50px; color: #565869;'>Strategic AI</h1>", unsafe_allow_html=True)

# 1. MOSTRAR MENSAJES DEL CHAT ACTUAL
for msg in current_messages:
    with st.chat_message(msg["role"], avatar="👤" if msg["role"]=="user" else "🧠"):
        st.markdown(msg["content"])

# 2. INPUT Y RESPUESTA
if prompt := st.chat_input("Escribe tu consulta..."):
    # Guardar mensaje usuario en el chat actual
    st.session_state.chats[current_id].append({"role": "user", "content": prompt})
    
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    try:
        # Preparar Prompt
        system_instruction = "Eres un asistente útil."
        if st.session_state.license_level in ["PRO", "ULTRA"]:
            system_instruction = "Eres un Consultor Estratégico Senior. Usa Markdown, tablas y listas."
        
        context_data = ""
        if st.session_state.document_context:
            context_data = f"\n[DOC CONTEXT]:\n{st.session_state.document_context[:10000]}\n"

        # Historial de contexto para la IA (últimos 5 mensajes para que tenga memoria corta)
        history_context = "\n".join([f"{m['role']}: {m['content']}" for m in current_messages[-5:]])
        final_prompt = f"{system_instruction}\n{context_data}\nCHAT HISTORY:\n{history_context}\nUSUARIO: {prompt}"

        # Streaming respuesta
        with st.chat_message("assistant", avatar="🧠"):
            response_placeholder = st.empty()
            full_response = ""
            response = model.generate_content(final_prompt, stream=True)
            
            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    response_placeholder.markdown(full_response + "▌")
            
            response_placeholder.markdown(full_response)
            
        # Guardar respuesta IA en el chat actual
        st.session_state.chats[current_id].append({"role": "assistant", "content": full_response})
        
        # Forzamos recarga para que se actualice el nombre del chat en la barra lateral
        st.rerun()

    except Exception as e:
        st.error(f"Error: {e}")
