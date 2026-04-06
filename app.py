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
APP_VERSION = "2026.04.004"

# --- Traducción de Tipos al Español ---
TYPE_TRANSLATIONS = {
    "normal": "Normal", "fire": "Fuego", "water": "Agua", "electric": "Eléctrico",
    "grass": "Planta", "ice": "Hielo", "fighting": "Lucha", "poison": "Veneno",
    "ground": "Tierra", "flying": "Volador", "psychic": "Psíquico", "bug": "Bicho",
    "rock": "Roca", "ghost": "Fantasma", "dragon": "Dragón", "dark": "Siniestro",
    "steel": "Acero", "fairy": "Hada", "desconocido": "Desconocido"
}

# --- Configuración de la Página ---
st.set_page_config(page_title="Pokedex IA Master", page_icon="🎴", layout="wide")

# --- Estilos Globales de Pokedex ---
def inject_pokedex_ui():
    st.markdown(f"""
        <style>
        /* Fondo Rojo Pokedex forzado desde el inicio */
        .stApp {{
            background-color: #dc0a2d !important;
            background-image: radial-gradient(#ff1f1f 2px, transparent 2px);
            background-size: 30px 30px;
        }}
        [data-testid="stHeader"] {{
            background: rgba(0,0,0,0) !important;
        }}
        [data-testid="stSidebar"] {{
            background-color: #af0924 !important;
            border-right: 5px solid #333;
        }}
        
        /* Contenedor tipo pantalla de Pokedex */
        .pokedex-screen {{
            background-color: #dedede;
            border: 10px solid #333;
            border-radius: 10px 10px 10px 40px;
            padding: 15px;
            box-shadow: inset 5px 5px 15px rgba(0,0,0,0.4);
            margin-bottom: 20px;
            min-height: 300px;
        }}
        
        h1, h2, h3, p, span {{
            color: white !important;
            text-shadow: 1px 1px 2px black;
        }}
        
        /* Botón de la Pokedex (Azul circular) */
        .stButton>button {{
            background-color: #0075be !important;
            color: white !important;
            border-radius: 50px !important;
            border: 4px solid #333 !important;
            font-weight: bold !important;
            height: 50px !important;
            box-shadow: 0 4px #005a92 !important;
        }}
        .stButton>button:active {{
            box-shadow: 0 0 #005a92 !important;
            transform: translateY(4px);
        }}

        /* Carta Pokémon TCG */
        .pokemon-tcg-card {{
            background: linear-gradient(135deg, #f8d030 0%, #ffffff 50%, #f8d030 100%);
            padding: 10px;
            border-radius: 10px;
            max-width: 320px;
            box-shadow: 0 10px 20px rgba(0,0,0,0.5);
            border: 5px solid #333;
            margin: auto;
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
        }}

        .version-footer {{
            position: fixed;
            bottom: 5px;
            right: 10px;
            color: white !important;
            font-size: 0.7rem;
            z-index: 1000;
        }}
        </style>
        <div class="version-footer">v{APP_VERSION}</div>
    """, unsafe_allow_html=True)

inject_pokedex_ui()

# --- Inicialización de Historial ---
if "pokedex_history" not in st.session_state:
    st.session_state.pokedex_history = []

# --- Colores de Tipos ---
TYPE_COLORS = {
    "normal": "#A8A77A", "fire": "#EE8130", "water": "#6390F0", "electric": "#F7D02C",
    "grass": "#7AC74C", "ice": "#96D9D6", "fighting": "#C22E28", "poison": "#A040A0",
    "ground": "#E2BF65", "flying": "#A98FF3", "psychic": "#F95587", "bug": "#A6B91A",
    "rock": "#B6A136", "ghost": "#735797", "dragon": "#6F35FC", "dark": "#705746",
    "steel": "#B7B7CE", "fairy": "#D685AD"
}

# --- Lógica de Audio (Base64 para Autoplay en Móvil) ---
def autoplay_audio(audio_fp):
    audio_bytes = audio_fp.getvalue()
    b64 = base64.b64encode(audio_bytes).decode()
    md = f"""
        <audio autoplay="true">
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
    """
    st.markdown(md, unsafe_allow_html=True)

# --- Lógica de PokéAPI ---
def get_evolutions(chain_url):
    try:
        res = requests.get(chain_url).json()
        chain = res['chain']
        evo_list = []
        def extract_evo(node):
            evo_list.append(node['species']['name'])
            for next_evo in node['evolves_to']: extract_evo(next_evo)
        extract_evo(chain)
        return evo_list
    except: return []

def get_pokeapi_full_data(name):
    try:
        res = requests.get(f"https://pokeapi.co/api/v2/pokemon/{name.lower()}").json()
        species_res = requests.get(res['species']['url']).json()
        evolutions = get_evolutions(species_res['evolution_chain']['url'])
        return {
            "id": res["id"], "height": res["height"] / 10, "weight": res["weight"] / 10,
            "types": [t["type"]["name"] for t in res["types"]],
            "sprite": res["sprites"]["other"]["official-artwork"]["front_default"],
            "evolutions": evolutions,
            "category": species_res["genera"][7]["genus"] if len(species_res["genera"]) > 7 else "Pokémon"
        }
    except: return None

def text_to_speech_full(data, fun_fact):
    # Traducimos los tipos para que se lean correctamente en español
    tipos_es = [TYPE_TRANSLATIONS.get(t, t) for t in data['types']]
    tipos_str = " y ".join(tipos_es)
    
    evos = f"Evoluciona en {', '.join(data['evolutions'][1:])}." if len(data['evolutions']) > 1 else "No tiene evoluciones conocidas."
    text = f"{data['name']}. Es un Pokémon de tipo {tipos_str}. Mide {data['height']} metros. {fun_fact}. {evos}"
    try:
        tts = gTTS(text=text, lang='es')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        return fp
    except: return None

# --- Motor de Reconocimiento ---
SYSTEM_PROMPT = "Analiza Pokémon. Responde SOLO JSON: {\"pokemon_name\": \"...\", \"confidence\": 0.0, \"detected_color\": \"#hex\", \"fun_fact\": \"...\"}"

def identify_pokemon(image):
    # Lista extendida de modelos confirmados en 2026
    models = [
        'models/gemini-2.0-flash-lite', 
        'models/gemini-2.0-flash',
        'models/gemini-2.5-flash',
        'models/gemini-1.5-flash'
    ]
    
    image.thumbnail((300, 300))
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG', quality=65)
    img_bytes = img_byte_arr.getvalue()
    
    last_err = "No se pudo conectar con ningún modelo."
    for m in models:
        try:
            model = genai.GenerativeModel(m)
            response = model.generate_content([
                SYSTEM_PROMPT, 
                {"mime_type": "image/jpeg", "data": img_bytes}
            ])
            if response.text:
                return json.loads(response.text.replace('```json', '').replace('```', '').strip())
        except exceptions.ResourceExhausted:
            last_err = f"Cuota agotada en {m}. Espera 60s."
            continue
        except Exception as e:
            last_err = f"Error en {m}: {str(e)}"
            continue
            
    return {"error": "quota", "message": last_err}

# --- INTERFAZ ---
st.title("📟 Pokedex IA Master")

with st.sidebar:
    st.header("🎒 Inventario")
    for p in reversed(st.session_state.pokedex_history):
        st.write(f"• {p['name'].capitalize()}")

col_left, col_right = st.columns([1, 1.2])

with col_left:
    st.markdown('<div class="pokedex-screen">', unsafe_allow_html=True)
    img_file = st.camera_input("SCANNER") or st.file_uploader("Subir", type=["jpg", "png"])
    st.markdown('</div>', unsafe_allow_html=True)

if img_file:
    image = Image.open(img_file)
    with col_right:
        if st.button("🔴 IDENTIFICAR", use_container_width=True):
            with st.spinner("Buscando en base de datos..."):
                res = identify_pokemon(image)
                if "error" in res: st.error(res["message"])
                else:
                    data = get_pokeapi_full_data(res["pokemon_name"]) or {
                        "name": res["pokemon_name"], "id": "???", "height": "??", "weight": 0,
                        "types": ["desconocido"], "sprite": "", "evolutions": [], "category": "Misterioso"
                    }
                    data["name"] = res["pokemon_name"]
                    st.session_state.pokedex_history.append(data)
                    st.balloons()
                    
                    # CARTA TCG
                    type_icons = "".join([f'<div style="display:inline-block; width:15px; height:15px; border-radius:50%; background:{TYPE_COLORS.get(t,"#777")}; margin-left:5px;"></div>' for t in data["types"]])
                    st.markdown(f"""
                    <div class="pokemon-tcg-card">
                        <div class="inner-card">
                            <div style="display:flex; justify-content:space-between; font-weight:bold;">
                                <span>{data['name'].upper()}</span>
                                <span>HP {data['weight']*10:.0f} {type_icons}</span>
                            </div>
                            <div style="background:white; border:3px solid #333; margin:5px 0; text-align:center;">
                                <img src="{data['sprite']}" width="100%">
                            </div>
                            <div style="font-size:0.7rem; text-align:center; background:#eee; padding:2px;">
                                {data['category']}. Altura: {data['height']}m
                            </div>
                            <div style="margin-top:10px; font-size:0.85rem;">
                                <b>Dato:</b> {res['fun_fact']}<br>
                                <b>Evos:</b> {' → '.join(data['evolutions']).upper()}
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # AUDIO AUTO-PLAY
                    audio = text_to_speech_full(data, res["fun_fact"])
                    if audio:
                        autoplay_audio(audio)
                        st.audio(audio, format='audio/mp3') # Backup manual
