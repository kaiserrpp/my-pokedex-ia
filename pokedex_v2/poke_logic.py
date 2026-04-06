import requests
import google.generativeai as genai
import json
import io
import base64
from gtts import gTTS
import streamlit as st

import subprocess
import os

# --- Lógica de Sincronización ---
def deploy_to_github():
    try:
        # El script está en el directorio padre de pokedex_v2
        sync_script = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sync.ps1"))
        if not os.path.exists(sync_script):
             return "Error: No se encontró el script de sincronización."
             
        # Ejecutar PowerShell -NoProfile para evitar retrasos
        result = subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", sync_script], 
                              capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error al sincronizar: {e.stderr}"
    except Exception as e:
        return f"Error inesperado: {str(e)}"

# --- Configuración de Datos Constantes ---
TYPE_COLORS = {
    "normal": "#A8A77A", "fire": "#EE8130", "water": "#6390F0", "electric": "#F7D02C",
    "grass": "#7AC74C", "ice": "#96D9D6", "fighting": "#C22E28", "poison": "#A040A0",
    "ground": "#E2BF65", "flying": "#A98FF3", "psychic": "#F95587", "bug": "#A6B91A",
    "rock": "#B6A136", "ghost": "#735797", "dragon": "#6F35FC", "dark": "#705746",
    "steel": "#B7B7CE", "fairy": "#D685AD"
}

TYPE_TRANSLATIONS = {
    "normal": "Normal", "fire": "Fuego", "water": "Agua", "electric": "Eléctrico",
    "grass": "Planta", "ice": "Hielo", "fighting": "Lucha", "poison": "Veneno",
    "ground": "Tierra", "flying": "Volador", "psychic": "Psíquico", "bug": "Bicho",
    "rock": "Roca", "ghost": "Fantasma", "dragon": "Dragón", "dark": "Siniestro",
    "steel": "Acero", "fairy": "Hada", "desconocido": "Desconocido"
}

SYSTEM_PROMPT = "Analiza la imagen. Si es un Pokémon, responde SOLO JSON con: {\"pokemon_name\": \"[nombre del pokemon]\" (en español si es posible), \"confidence\": 0.0 (confianza de 0.0 a 1.0), \"detected_color\": \"#hex\" (color dominante del pokemon), \"fun_fact\": \"[un dato curioso del pokemon]\" (en español)}. Si NO es un Pokémon, responde SOLO JSON con: {\"error\": \"no_pokemon\", \"message\": \"La imagen no contiene un Pokémon detectable.\"}"

def load_api_key():
    return st.secrets.get("GEMINI_API_KEY", "")

def get_pokeapi_data(name):
    try:
        res = requests.get(f"https://pokeapi.co/api/v2/pokemon/{name.lower()}").json()
        species_res = requests.get(res['species']['url']).json()
        
        category = "Pokémon"
        for genus in species_res["genera"]:
            if genus["language"]["name"] == "es":
                category = genus["genus"]
                break
                
        evo_res = requests.get(species_res['evolution_chain']['url']).json()
        chain = evo_res['chain']
        evolutions = []
        def extract_evo(node):
            evolutions.append(node['species']['name'])
            for next_evo in node['evolves_to']: extract_evo(next_evo)
        extract_evo(chain)

        return {
            "id": res["id"], 
            "height": res["height"] / 10, 
            "weight": res["weight"] / 10,
            "types": [t["type"]["name"] for t in res["types"]],
            "sprite": res["sprites"]["other"]["official-artwork"]["front_default"],
            "evolutions": evolutions,
            "category": category,
            "name": name.capitalize()
        }
    except Exception as e:
        print(f"Error PokeAPI: {e}")
        return None

def identify_pokemon_ia(image, api_key):
    if not api_key:
        return {"error": "no_key", "message": "Falta la API Key de Google. Configúrala en .streamlit/secrets.toml"}
    
    genai.configure(api_key=api_key)
    # Modelos disponibles para tareas de visión. gemini-pro-vision es recomendado.
    # Los modelos 'gemini-1.5-flash' y 'gemini-2.0-flash' pueden no ser válidos o estar en la cuota gratuita.
    models = ['gemini-pro-vision', 'gemini-2.0-flash-lite', 'gemini-2.5-flash'] 
    
    # Reducir el tamaño de la imagen para optimizar el envío a la API
    image.thumbnail((600, 600)) # Un poco más grande para mantener detalle
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG', quality=75) # Aumentar calidad a 75
    img_bytes = img_byte_arr.getvalue()
    
    for m in models:
        try:
            # Verificar si el modelo es realmente accesible antes de usarlo si es necesario
            # (Para este caso, asumimos que los nombres listados son los correctos a intentar)
            model = genai.GenerativeModel(m)
            response = model.generate_content([SYSTEM_PROMPT, {"mime_type": "image/jpeg", "data": img_bytes}])
            
            if response.text:
                clean_text = response.text.replace('```json', '').replace('```', '').strip()
                try:
                    json_response = json.loads(clean_text)
                    # Si la IA dice que no es un Pokémon, pasamos ese error directamente
                    if "error" in json_response and json_response["error"] == "no_pokemon":
                        return json_response
                    return json_response
                except json.JSONDecodeError:
                    print(f"Error: La respuesta de la IA no es un JSON válido: {clean_text}")
                    continue # Intentar con el siguiente modelo si la respuesta no es JSON
        except Exception as e:
            # Manejo específico para errores de cuota
            if 'quota' in str(e).lower() or 'exceeded' in str(e).lower():
                print(f"Error de cuota o acceso con el modelo {m}: {e}")
                print("Por favor, revisa la configuración de facturación de tu proyecto en Google Cloud.")
                # Si es un error de cuota, es probable que todos los modelos gratuitos fallen, pero continuamos por si acaso.
            else:
                print(f"Error genérico con el modelo {m}: {e}")
            continue # Intentar con el siguiente modelo
    return {"error": "fail", "message": "No se pudo identificar el Pokémon después de probar todos los modelos disponibles. Revisa los logs para más detalles."}

def text_to_speech(data, fun_fact):
    tipos_es = [TYPE_TRANSLATIONS.get(t, t) for t in data['types']]
    evos = f"Evoluciona en {', '.join(data['evolutions'][1:])}." if len(data['evolutions']) > 1 else "No tiene evoluciones."
    text = f"{data['name']}. Pokémon {data['category']}. Tipo {', '.join(tipos_es)}. Mide {data['height']} metros. {fun_fact}. {evos}"
    try:
        tts = gTTS(text=text, lang='es')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        return fp
    except:
        return None

def autoplay_audio(audio_fp):
    audio_bytes = audio_fp.getvalue()
    b64 = base64.b64encode(audio_bytes).decode()
    md = f'<audio autoplay="true"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
    st.markdown(md, unsafe_allow_html=True)

