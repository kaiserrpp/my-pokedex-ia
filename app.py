import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import io
import requests
import time
from google.api_core import exceptions
from gtts import gTTS

# --- Configuración de la Página ---
st.set_page_config(page_title="Pokedex IA Master", page_icon="🎴", layout="wide")

# --- Inicialización de Historial ---
if "pokedex_history" not in st.session_state:
    st.session_state.pokedex_history = []

# --- Estilos CSS de la Carta Pokémon ---
def apply_card_styles(color="#F7D02C"):
    st.markdown(f"""
        <style>
        .main {{
            background-color: #f0f2f6;
        }}
        .pokemon-tcg-card {{
            background: linear-gradient(135deg, {color} 0%, #ffd700 50%, {color} 100%);
            padding: 15px;
            border-radius: 18px;
            width: 380px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.3);
            border: 8px solid #f8d030;
            margin: auto;
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            color: #333;
        }}
        .inner-card {{
            background-color: #fffde7;
            border-radius: 10px;
            padding: 10px;
            border: 2px solid #b8860b;
        }}
        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-weight: bold;
            font-size: 1.4rem;
            margin-bottom: 5px;
        }}
        .hp-text {{
            color: #e53935;
            font-size: 1.1rem;
        }}
        .image-frame {{
            background: #fff;
            border: 4px solid #d3d3d3;
            margin: 5px 0;
            text-align: center;
            box-shadow: inset 0 0 10px rgba(0,0,0,0.1);
        }}
        .stats-bar {{
            background: linear-gradient(to right, #e0e0e0, #f5f5f5);
            font-size: 0.75rem;
            padding: 3px;
            text-align: center;
            border: 1px solid #ccc;
            font-style: italic;
            margin-bottom: 10px;
        }}
        .ability-section {{
            margin-top: 10px;
            padding: 5px;
        }}
        .ability-name {{
            font-weight: bold;
            font-size: 1rem;
            border-bottom: 1px solid #ccc;
            display: block;
        }}
        .ability-desc {{
            font-size: 0.85rem;
            line-height: 1.2;
            margin-top: 5px;
            display: block;
        }}
        .card-footer {{
            display: flex;
            justify-content: space-between;
            font-size: 0.7rem;
            margin-top: 15px;
            font-weight: bold;
        }}
        .type-icon {{
            width: 20px;
            height: 20px;
            border-radius: 50%;
            display: inline-block;
            margin-left: 5px;
        }}
        </style>
    """, unsafe_allow_html=True)

# --- Colores de Tipos ---
TYPE_COLORS = {
    "normal": "#A8A77A", "fire": "#EE8130", "water": "#6390F0", "electric": "#F7D02C",
    "grass": "#7AC74C", "ice": "#96D9D6", "fighting": "#C22E28", "poison": "#A040A0",
    "ground": "#E2BF65", "flying": "#A98FF3", "psychic": "#F95587", "bug": "#A6B91A",
    "rock": "#B6A136", "ghost": "#735797", "dragon": "#6F35FC", "dark": "#705746",
    "steel": "#B7B7CE", "fairy": "#D685AD"
}

# --- Lógica de PokeAPI Extendida ---
def get_evolutions(chain_url):
    try:
        res = requests.get(chain_url).json()
        chain = res['chain']
        evo_list = []
        
        def extract_evo(node):
            evo_list.append(node['species']['name'])
            for next_evo in node['evolves_to']:
                extract_evo(next_evo)
        
        extract_evo(chain)
        return evo_list
    except:
        return []

def get_pokeapi_full_data(name):
    try:
        # 1. Datos base
        res = requests.get(f"https://pokeapi.co/api/v2/pokemon/{name.lower()}").json()
        # 2. Especie para evoluciones
        species_res = requests.get(res['species']['url']).json()
        evolutions = get_evolutions(species_res['evolution_chain']['url'])
        
        return {
            "id": res["id"],
            "height": res["height"] / 10,
            "weight": res["weight"] / 10,
            "types": [t["type"]["name"] for t in res["types"]],
            "sprite": res["sprites"]["other"]["official-artwork"]["front_default"],
            "evolutions": evolutions,
            "category": species_res["genera"][7]["genus"] if len(species_res["genera"]) > 7 else "Pokémon"
        }
    except:
        return None

def text_to_speech_full(data, fun_fact):
    """Genera una explicación completa en audio."""
    evos_text = f"Sus evoluciones son {', '.join(data['evolutions'])}." if len(data['evolutions']) > 1 else "No tiene evoluciones conocidas."
    explanation = (
        f"Este es {data['name'].capitalize()}. "
        f"Es un Pokémon de tipo {', '.join(data['types'])}. "
        f"Mide {data['height']} metros y pesa {data['weight']} kilos. "
        f"Dato curioso: {fun_fact}. "
        f"{evos_text}"
    )
    try:
        tts = gTTS(text=explanation, lang='es')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        return fp
    except:
        return None

# --- Motor de Reconocimiento ---
SYSTEM_PROMPT = """
Actúa como un motor de reconocimiento Pokémon. Responde SOLO JSON:
{
  "pokemon_name": "nombre_en_ingles",
  "confidence": 0.0,
  "detected_color": "hex_code",
  "fun_fact": "frase_corta_en_español"
}
"""

def identify_pokemon(image):
    # Lista extendida de modelos según tu diagnóstico de 2026
    models = [
        'models/gemini-2.0-flash-lite', 
        'models/gemini-2.0-flash',
        'models/gemini-2.5-flash',
        'models/gemini-1.5-flash'
    ]
    
    # Reducción agresiva para maximizar probabilidad de éxito en Free Tier
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

# --- UI ---
st.title("🎴 Pokedex Master: Edición Coleccionista")

with st.sidebar:
    st.header("🎒 Mochila de Entrenador")
    if st.session_state.pokedex_history:
        for p in reversed(st.session_state.pokedex_history):
            st.button(f"📄 {p['name'].capitalize()}", key=f"hist_{p['name']}_{time.time()}")

col_input, col_card = st.columns([1, 1.2])

with col_input:
    st.subheader("Captura un Pokémon")
    img_file = st.camera_input("Scanner") or st.file_uploader("Subir imagen", type=["jpg", "png"])

if img_file:
    image = Image.open(img_file)
    with col_card:
        if st.button("✨ ¡Lanzar Poké Ball!", use_container_width=True):
            with st.spinner("Analizando..."):
                res = identify_pokemon(image)
                if "error" in res:
                    st.error(res["message"])
                else:
                    # 1. Intentar datos de PokéAPI
                    extra_data = get_pokeapi_full_data(res["pokemon_name"])
                    
                    # 2. Preparar datos finales (con o sin PokeAPI)
                    pokemon_display_name = res["pokemon_name"]
                    if extra_data:
                        data = extra_data
                        data["name"] = pokemon_display_name
                    else:
                        st.warning(f"⚠️ No he encontrado datos oficiales de {pokemon_display_name}, pero aquí tienes mi análisis.")
                        data = {
                            "name": pokemon_display_name,
                            "id": "???",
                            "height": "??",
                            "weight": 0,
                            "types": ["desconocido"],
                            "sprite": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/0.png",
                            "evolutions": [pokemon_display_name],
                            "category": "Pokémon Misterioso"
                        }
                    
                    st.session_state.pokedex_history.append(data)
                    apply_card_styles(res["detected_color"])
                    st.balloons()
                    
                    # 3. RENDER DE LA CARTA
                    type_icons = "".join([f'<div class="type-icon" style="background-color:{TYPE_COLORS.get(t, "#777")}"></div>' for t in data["types"]])
                    
                    st.markdown(f"""
                    <div class="pokemon-tcg-card">
                        <div class="inner-card">
                            <div class="card-header">
                                <span>{data['name'].upper()}</span>
                                <span class="hp-text">HP {data['weight']*10 if data['weight'] > 0 else '???'} {type_icons}</span>
                            </div>
                            <div class="image-frame">
                                <img src="{data['sprite']}" width="100%">
                            </div>
                            <div class="stats-bar">
                                {data['category']}. Altura: {data['height']}m, Peso: {data['weight']}kg
                            </div>
                            <div class="ability-section">
                                <span class="ability-name">Dato Curioso</span>
                                <span class="ability-desc">{res['fun_fact']}</span>
                            </div>
                            <div class="ability-section">
                                <span class="ability-name">Evoluciones</span>
                                <span class="ability-desc">{' → '.join(data['evolutions']).upper()}</span>
                            </div>
                            <div class="card-footer">
                                <span>Nº {data['id']}</span>
                                <span>©2026 Pokedex IA Master</span>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 4. AUDIO (Soporte móvil: Autoplay + Botón Manual)
                    audio = text_to_speech_full(data, res["fun_fact"])
                    if audio:
                        st.audio(audio, format='audio/mp3', autoplay=True)
                        st.button("📢 Volver a escuchar", on_click=None, use_container_width=True)
