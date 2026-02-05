import streamlit as st
import google.generativeai as genai
import os

st.title("MODO DIAGNÓSTICO")

# 1. Verificamos la versión de la librería (para saber si es vieja)
import google.generativeai
st.write(f"Versión de librería Google: **{google.generativeai.__version__}**")

# 2. Intentamos conectar
try:
    # Usamos la clave de los secretos
    api_key = st.secrets["GOOGLE_API_KEY"]
    masked_key = f"{api_key[:5]}...{api_key[-4:]}"
    st.write(f"Usando API Key: `{masked_key}`")
    
    genai.configure(api_key=api_key)
    
    # 3. LE PEDIMOS LA LISTA DE MODELOS (Aquí está la clave)
    st.write("Conectando con Google para pedir la lista de modelos...")
    
    available_models = []
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            available_models.append(m.name)
            
    if available_models:
        st.success("¡CONEXIÓN EXITOSA! Estos son los modelos que TU cuenta permite:")
        st.code("\n".join(available_models))
        st.info("Copia uno de estos nombres exactos para usarlo en la App.")
    else:
        st.error("Conectamos, pero no devolvió ningún modelo. Tu cuenta podría no tener acceso a Gemini todavía.")

except Exception as e:
    st.error(f"ERROR FATAL DE CONEXIÓN:\n{str(e)}")
    st.write("Revisa que la clave en Secrets no tenga espacios y sea la correcta.")








