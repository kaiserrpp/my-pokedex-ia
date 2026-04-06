import streamlit as st

def inject_pokedex_assets(version):
    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=VT323&display=swap');

        /* Configuración base del contenedor de Streamlit */
        .stApp {{
            background-color: #dc0a2d !important;
            background-image: 
                linear-gradient(135deg, #ff1f1f 0%, #dc0a2d 50%, #8b0000 100%);
            border-left: 20px solid #8b0000;
        }}

        [data-testid="stHeader"], [data-testid="stToolbar"] {{
            display: none !important;
        }}

        /* Cabecera Física (Sensor y LEDs) */
        .pokedex-physical-header {{
            display: flex;
            align-items: flex-start;
            padding: 25px;
            background: #dc0a2d;
            border-bottom: 6px solid #8b0000;
            margin-bottom: 30px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.4);
            border-radius: 0 0 60px 0;
            position: relative;
        }}

        .main-lens {{
            width: 70px;
            height: 70px;
            background: radial-gradient(circle at 30% 30%, #b3e5fc, #0288d1 70%, #01579b);
            border: 6px solid #efefef;
            border-radius: 50%;
            box-shadow: 0 0 20px #0288d1, inset 4px 4px 8px rgba(0,0,0,0.6);
            margin-right: 20px;
        }}

        .led-container {{
            display: flex;
            gap: 12px;
            margin-top: 10px;
        }}

        .led {{
            width: 18px;
            height: 18px;
            border-radius: 50%;
            border: 3px solid #333;
        }}
        .led-red {{ background: #ff1744; box-shadow: 0 0 10px #ff1744; }}
        .led-yellow {{ background: #ffea00; box-shadow: 0 0 10px #ffea00; }}
        .led-green {{ background: #00e676; box-shadow: 0 0 10px #00e676; }}

        /* El Marco de la Pantalla */
        .pokedex-screen-frame {{
            background-color: #cccccc;
            border: 12px solid #333333;
            border-radius: 10px 10px 10px 60px;
            padding: 25px;
            box-shadow: inset 8px 8px 15px rgba(0,0,0,0.5), 8px 8px 0px #8b0000;
            margin: 0 auto 30px auto;
            max-width: 95%;
            position: relative;
        }}

        /* Tornillos decorativos */
        .screw {{
            position: absolute;
            width: 12px;
            height: 12px;
            background: #555;
            border-radius: 50%;
            box-shadow: inset 2px 2px 2px rgba(255,255,255,0.3);
        }}
        .s-tl {{ top: 8px; left: 8px; }}
        .s-tr {{ top: 8px; right: 8px; }}

        /* Pantalla LCD */
        .lcd-display {{
            background: #1a1a1a;
            border-radius: 8px;
            padding: 15px;
            min-height: 250px;
            border: 4px solid #444;
            box-shadow: inset 0 0 20px #000;
        }}

        /* Estilo de los Botones */
        .stButton>button {{
            background: linear-gradient(#555, #222) !important;
            color: #4ef037 !important; /* Verde Neón */
            font-family: 'VT323', monospace !important;
            font-size: 2rem !important;
            border: 4px solid #111 !important;
            border-radius: 12px !important;
            padding: 10px 20px !important;
            box-shadow: 5px 5px 0px #600000 !important;
            width: 100% !important;
            text-transform: uppercase;
            letter-spacing: 2px;
        }}

        .stButton>button:hover {{
            background: linear-gradient(#666, #333) !important;
            color: #fff !important;
            border-color: #4ef037 !important;
        }}

        /* Textos */
        h1, h2, h3, p {{
            font-family: 'VT323', monospace !important;
            color: #fff !important;
            text-align: center;
        }}
        
        .pokedex-id-tag {{
            background: #222;
            padding: 5px 15px;
            border-radius: 5px;
            border: 1px solid #4ef037;
            color: #4ef037 !important;
            font-family: 'VT323', monospace;
            display: inline-block;
            margin-bottom: 10px;
        }}

        .version-tag {{
            position: fixed;
            bottom: 10px;
            left: 30px;
            color: #8b0000;
            font-family: 'VT323', monospace;
            font-size: 0.9rem;
        }}
        </style>
        
        <div class="pokedex-physical-header">
            <div class="main-lens"></div>
            <div class="led-container">
                <div class="led led-red"></div>
                <div class="led led-yellow"></div>
                <div class="led led-green"></div>
            </div>
        </div>
        <div class="version-tag">OS_POKEDEX_v{version}</div>
    """, unsafe_allow_html=True)

def draw_tcg_card(data, fun_fact, type_colors):
    type_icons = "".join([f'<div style="display:inline-block; width:15px; height:15px; border-radius:50%; background:{type_colors.get(t,"#777")}; border:1px solid #333; margin-left:5px;"></div>' for t in data["types"]])
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #f0d000 0%, #e0c000 50%, #b09000 100%);
        padding: 15px;
        border-radius: 12px;
        border: 6px solid #333;
        box-shadow: 0 20px 40px rgba(0,0,0,0.6);
        max-width: 340px;
        margin: 20px auto;
    ">
        <div style="background-color: #fffde7; border: 3px solid #444; padding: 10px; font-family: sans-serif;">
            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom: 2px solid #444; padding-bottom: 5px; margin-bottom: 8px;">
                <span style="font-weight:bold; font-size:1.2rem; color:#111;">{data['name'].upper()}</span>
                <span style="font-weight:bold; color:#d32f2f;">HP {data['weight']*10:.0f} {type_icons}</span>
            </div>
            <div style="background:#fff; border:3px solid #888; margin:5px 0; height:180px; display:flex; align-items:center; justify-content:center; overflow:hidden;">
                <img src="{data['sprite']}" style="width:100%; object-fit: contain;">
            </div>
            <div style="font-size:0.7rem; text-align:center; background:#ccc; margin:5px 0; padding:2px; font-style:italic; border:1px solid #666; color:#111;">
                {data['category']}. Altura: {data['height']}m, Peso: {data['weight']}kg
            </div>
            <div style="margin-top:10px; font-size:0.85rem; line-height:1.2; color:#111;">
                <b style="color:#d32f2f;">Dato:</b> {fun_fact}<br>
                <div style="margin-top:5px; padding:5px; background:rgba(0,0,0,0.05); border-radius:4px;">
                    <b style="color:#1976d2;">EVO:</b> {(' → '.join(data['evolutions']) if data['evolutions'] else "Único").upper()}
                </div>
            </div>
            <div style="display:flex; justify-content:space-between; font-size:0.6rem; margin-top:15px; padding-top:5px; border-top:1px solid #999; color:#444; font-weight:bold;">
                <span>Nº {data['id']}</span>
                <span>ID-GEN V2.0</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
