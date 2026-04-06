import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import io
import requests
import time
import base64
from google.api_core import exceptions
from gtts import gTTS

# --- Configuración de Versión ---
APP_VERSION = "2026.04.005"

# --- Traducción de Tipos al Español ---
TYPE_TRANSLATIONS = {
    "normal": "Normal", "fire": "Fuego", "water": "Agua", "electric": "Eléctrico",
    "grass": "Planta", "ice": "Hielo", "fighting": "Lucha", "poison": "Veneno",
    "ground": "Tierra", "flying": "Volador", "psychic": "Psíquico", "bug": "Bicho",
    "rock": "Roca", "ghost": "Fantasma", "dragon": "Dragón", "dark": "Siniestro",
    "steel": "Acero", "fairy": "Hada", "desconocido": "Desconocido"
}

# --- Configuración de la Página ---
st.set_page_config(page_title="Pokedex IA Master", page_icon="🎴", layout="centered")

# --- Estilos Globales de Pokedex (Responsivo) ---
def inject_pokedex_ui():
    st.markdown(f"""
        <style>
        .stApp {{
            background-color: #dc0a2d !important;
            background-image: radial-gradient(#ff1f1f 2px, transparent 2px);
            background-size: 30px 30px;
        }}
        [data-testid="stHeader"], [data-testid="stToolbar"] {{
            display: none !important;
        }}
        .pokedex-screen {{
            background-color: #dedede;
            border: 8px solid #333;
            border-radius: 10px 10px 10px 40px;
            padding: 10px;
            box-shadow: inset 5px 5px 15px rgba(0,0,0,0.4);
            margin-bottom: 15px;
            max-width: 100%;
        }}
        h1, h2, h3, p, span {{
            color: white !important;
            text-shadow: 1px 1px 2px black;
            text-align: center;
        }}
        .stButton>button {{
            background-color: #0075be !important;
            color: white !important;
            border-radius: 50px !important;
            border: 4px solid #333 !important;
            font-weight: bold !important;
            width: 100% !important;
            height: 55px !important;
            box-shadow: 0 4px #005a92 !important;
            font-size: 1.2rem !important;
        }}
        .pokemon-tcg-card {{
            background: linear-gradient(135deg, #f8d030 0%, #ffffff 50%, #f8d030 100%);
            padding: 10px;
            border-radius: 10px;
            max-width: 320px;
            box-shadow: 0 10px 20px rgba(0,0,0,0.5);
            border: 5px solid #333;
            margin: 20px auto;
            color: #333 !important;
        }}
        .inner-card {{
            background-color: #fffde7;
            border: 2px solid #555;
            padding: 8px;
            color: #333 !important;
        }}
        .inner-card * {{
            color: #333 !important;
            text-shadow: none !important;
            text-align: left;
        }}
        .version-footer {{
            position: fixed;
            bottom: 5px;
            right: 10px;
            color: white !important;
            font-size: 0.6rem;
            z-index: 1000;
        }}
        </style>
        <div class="version-footer">v{APP_VERSION}</div>
    """, unsafe_allow_html=True)

inject_pokedex_ui()

# --- Lógica de Audio ---
def autoplay_audio(audio_fp):
    audio_bytes = audio_fp.getvalue()
    b64 = base64.b64encode(audio_bytes).decode()
    md = f'<audio autoplay="true"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
    st.markdown(md, unsafe_allow_html=True)

# --- Lógica de PokéAPI (Traducción Forzada) ---
def get_pokeapi_full_data(name):
    try:
        res = requests.get(f"https://pokeapi.co/api/v2/pokemon/{name.lower()}").json()
        species_res = requests.get(res['species']['url']).json()
        
        # Buscar género en español
        category = "Pokémon"
        for genus in species_res["genera"]:
            if genus["language"]["name"] == "es":
                category = genus["genus"]
                break
                
        # Evoluciones
        evo_res = requests.get(species_res['evolution_chain']['url']).json()
        chain = evo_res['chain']
        evolutions = []
        def extract_evo(node):
            evolutions.append(node['species']['name'])
            for next_evo in node['evolves_to']: extract_evo(next_evo)
        extract_evo(chain)

        return {
            "id": res["id"], "height": res["height"] / 10, "weight": res["weight"] / 10,
            "types": [t["type"]["name"] for t in res["types"]],
            "sprite": res["sprites"]["other"]["official-artwork"]["front_default"],
            "evolutions": evolutions,
            "category": category
        }
    except: return None

def text_to_speech_full(data, fun_fact):
    tipos_es = [TYPE_TRANSLATIONS.get(t, t) for t in data['types']]
    evos = f"Evoluciona en {', '.join(data['evolutions'][1:])}." if len(data['evolutions']) > 1 else "No tiene evoluciones."
    text = f"{data['name']}. Pokémon {data['category']}. Tipo {' y '.join(tipos_es)}. Mide {data['height']} metros. {fun_fact}. {evos}"
    try:
        tts = gTTS(text=text, lang='es')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        return fp
    except: return None

# --- Motor de Reconocimiento ---
SYSTEM_PROMPT = "Analiza Pokémon. Responde SOLO JSON: {\"pokemon_name\": \"...\", \"confidence\": 0.0, \"detected_color\": \"#hex\", \"fun_fact\": \"...\"}"

def identify_pokemon(image):
    models = ['models/gemini-2.0-flash-lite', 'models/gemini-2.0-flash', 'models/gemini-2.5-flash']
    image.thumbnail((300, 300))
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG', quality=65)
    img_bytes = img_byte_arr.getvalue()
    for m in models:
        try:
            model = genai.GenerativeModel(m)
            response = model.generate_content([SYSTEM_PROMPT, {"mime_type": "image/jpeg", "data": img_bytes}])
            if response.text: return json.loads(response.text.replace('```json', '').replace('```', '').strip())
        except: continue
    return {"error": "quota", "message": "Cuota agotada. Espera 60s."}

# --- INTERFAZ ---
st.title("📟 Pokedex IA")

with st.sidebar:
    st.header("🎒 Colección")
    if not st.session_state.get('pokedex_history'):
        st.write("Vacío")
    else:
        for p in reversed(st.session_state.pokedex_history):
            st.write(f"• {p['name'].capitalize()}")

st.markdown('<div class="pokedex-screen">', unsafe_allow_html=True)
img_file = st.camera_input("ESCÁNER") or st.file_uploader("Subir Imagen", type=["jpg", "png"])
st.markdown('</div>', unsafe_allow_html=True)

if img_file:
    image = Image.open(img_file)
    if st.button("🔴 ¡IDENTIFICAR!", use_container_width=True):
        with st.spinner("Buscando datos..."):
            res = identify_pokemon(image)
            if "error" in res: st.error(res["message"])
            else:
                data = get_pokeapi_full_data(res["pokemon_name"]) or {
                    "name": res["pokemon_name"], "id": "???", "height": "??", "weight": 0,
                    "types": ["desconocido"], "sprite": "", "evolutions": [], "category": "Misterioso"
                }
                data["name"] = res["pokemon_name"]
                if "pokedex_history" not in st.session_state: st.session_state.pokedex_history = []
                st.session_state.pokedex_history.append(data)
                st.balloons()
                
                # CARTA TCG (TRADUCIDA)
                type_icons = "".join([f'<div style="display:inline-block; width:12px; height:12px; border-radius:50%; background:{TYPE_COLORS.get(t,"#777")}; margin-left:5px;"></div>' for t in data["types"]])
                st.markdown(f"""
                <div class="pokemon-tcg-card">
                    <div class="inner-card">
                        <div style="display:flex; justify-content:space-between; font-weight:bold; font-size:1.1rem;">
                            <span>{data['name'].upper()}</span>
                            <span>PS {data['weight']*10:.0f} {type_icons}</span>
                        </div>
                        <div style="background:white; border:2px solid #333; margin:5px 0; text-align:center;">
                            <img src="{data['sprite']}" width="100%">
                        </div>
                        <div style="font-size:0.65rem; text-align:center; background:#eee; padding:2px; font-style:italic;">
                            {data['category']}. Altura: {data['height']}m, Peso: {data['weight']}kg
                        </div>
                        <div style="margin-top:8px; font-size:0.8rem;">
                            <b>Dato Curioso:</b> {res['fun_fact']}<br>
                            <b>Evoluciones:</b> {' → '.join(data['evolutions']).upper()}
                        </div>
                        <div style="display:flex; justify-content:space-between; font-size:0.6rem; margin-top:10px; font-weight:bold; border-top:1px solid #ccc; padding-top:5px;">
                            <span>Nº {data['id']}</span>
                            <span>©2026 Pokedex IA</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                audio = text_to_speech_full(data, res["fun_fact"])
                if audio:
                    autoplay_audio(audio)
                    st.audio(audio, format='audio/mp3')
