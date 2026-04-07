import streamlit as st
from PIL import Image
from ui_components import inject_pokedex_assets, draw_tcg_card
from poke_logic import (
    load_api_key, get_pokeapi_data, identify_pokemon_ia, 
    text_to_speech, autoplay_audio, TYPE_COLORS, deploy_to_github
)

# --- Configuración de Página ---
st.set_page_config(page_title="Pokédex Master V2", page_icon="🔴", layout="centered")

# --- Estado de la Aplicación ---
if 'history' not in st.session_state:
    st.session_state.history = []

APP_VERSION = "2026.04.008"

# --- Inyectar Interfaz Física ---
inject_pokedex_assets(APP_VERSION)

# --- Sidebar (Colección y Herramientas) ---
with st.sidebar:
    st.markdown("### 🎒 MOCHILA")
    if not st.session_state.history:
        st.write("Está vacía...")
    else:
        for p in reversed(st.session_state.history):
            with st.expander(f"• {p['name']}"):
                st.image(p['sprite'], width=100)
                st.write(f"ID: {p['id']}")
    
    st.divider()
    st.markdown("### ⚙️ ADMINISTRACIÓN")
    if st.button("🚀 DESPLEGAR CAMBIOS"):
        with st.spinner("Sincronizando con GitHub..."):
            output = deploy_to_github()
            st.success("¡Despliegue completado!")
            st.code(output)

# --- Cuerpo Principal ---
st.markdown("<h1>POKÉDEX IA</h1>", unsafe_allow_html=True)

# Marco de la pantalla
st.markdown('<div class="pokedex-screen-frame">', unsafe_allow_html=True)
st.markdown('<div class="lcd-display">', unsafe_allow_html=True)

# Entrada de Imagen
img_input = st.camera_input(" ") # Espacio vacío para que el botón original no moleste
img_upload = st.file_uploader("O sube una foto", type=["jpg", "png", "jpeg"])

active_image = img_input or img_upload

if active_image:
    image = Image.open(active_image)
    if st.button("🔴 ESCANEAR POKÉMON"):
        with st.spinner("Analizando con IA..."):
            api_key = load_api_key()
            res = identify_pokemon_ia(image, api_key)
            
            if "error" in res:
                st.error(res["message"])
            else:
                data = get_pokeapi_data(res["pokemon_name"])
                if data:
                    st.balloons()
                    # Dibujar Carta TCG
                    draw_tcg_card(data, res["fun_fact"], TYPE_COLORS)
                    
                    # Guardar en historial
                    st.session_state.history.append(data)
                    
                    # Audio
                    audio = text_to_speech(data, res["fun_fact"])
                    if audio:
                        autoplay_audio(audio)
                else:
                    st.warning(f"Se identificó a {res['pokemon_name']} pero no hay datos en la PokéAPI.")

st.markdown('</div>', unsafe_allow_html=True) # Cierre lcd-display
st.markdown('</div>', unsafe_allow_html=True) # Cierre pokedex-screen-frame

# Instrucciones en la parte inferior
st.markdown("""
    <p style='font-size: 1.2rem;'>
        [ APUNTA LA CÁMARA A UN POKÉMON Y PULSA EL BOTÓN ROJO ]
    </p>
""", unsafe_allow_html=True)
