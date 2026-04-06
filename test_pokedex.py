import google.generativeai as genai
import PIL.Image
import os
import io
import json
import streamlit as st # Usamos los mismos secretos que la app

# Intentar cargar la clave de los secretos de Streamlit
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    print("✅ API Key cargada correctamente.")
except Exception as e:
    print(f"❌ Error al cargar la API Key: {e}")
    exit()

def run_diagnostic():
    print("\n--- DIAGNÓSTICO DE MODELOS ---")
    try:
        models = genai.list_models()
        available_models = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
        print("Modelos que soportan generación de contenido en tu cuenta:")
        for m in available_models:
            print(f" - {m}")
        return available_models
    except Exception as e:
        print(f"❌ Error al listar modelos: {e}")
        return []

def test_identification(image_path, model_name):
    print(f"\n--- TEST DE IDENTIFICACIÓN CON {model_name} ---")
    try:
        model = genai.GenerativeModel(model_name)
        img = PIL.Image.open(image_path)
        
        # El mismo prompt de la app
        system_prompt = "Actúa como un motor de reconocimiento Pokémon. Responde SOLO con un JSON: {\"pokemon_name\": \"...\", \"confidence\": 0.0, \"detected_color\": \"...\", \"fun_fact\": \"...\"}"
        
        response = model.generate_content([system_prompt, img])
        print("Respuesta de la IA:")
        print(response.text)
        
        # Validar JSON
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        json.loads(clean_json)
        print("✅ Test exitoso: JSON válido recibido.")
    except Exception as e:
        print(f"❌ Error durante el test con {model_name}: {e}")

if __name__ == "__main__":
    # 1. Diagnóstico
    available = run_diagnostic()
    
    # 2. Buscar imagen
    test_folder = r"c:\DEV\python\unit_tests\pokemons"
    images = [f for f in os.listdir(test_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    if not images:
        print(f"\n⚠️ No se encontraron imágenes en {test_folder}. Por favor, añade una.")
    else:
        test_img = os.path.join(test_folder, images[0])
        print(f"\n🖼️ Usando imagen de test: {test_img}")
        
        # Probar con el primero de la lista de disponibles si Flash falla
        model_to_test = "models/gemini-2.0-flash" if "models/gemini-2.0-flash" in str(available) else None
        if not model_to_test and available:
            model_to_test = available[0]
            print(f"⚠️ 'gemini-2.0-flash' no parece estar disponible. Probando con el primero de tu lista: {model_to_test}")
        
        if model_to_test:
            test_identification(test_img, model_to_test)
        else:
            print("❌ No hay modelos disponibles para probar.")
