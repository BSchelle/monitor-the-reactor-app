import streamlit as st
import pandas as pd
import numpy as np
import time
import plotly.graph_objects as go
import plotly.express as px
import requests
import os

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Monitor the reactor", page_icon="🏭", layout="wide")

# --- 2. GESTION URL API ---
def get_api_url():
    if "API_URL" in st.secrets:
        return st.secrets["API_URL"]
    elif "API_URL" in os.environ:
        return os.environ["API_URL"]
    else:
        return "http://localhost:8000"

API_URL = get_api_url()

# --- 3. CSS ---
st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    .result-box {
        background-color: #262730;
        border: 1px solid #4B4B4B;
        border-radius: 5px;
        padding: 15px;
        margin-top: 20px;
        color: white;
        text-align: center;
    }
    .result-title { font-size: 0.9em; color: #aaaaaa; margin-bottom: 5px; }
    .result-value { font-size: 1.2em; font-weight: bold; color: #FAFAFA; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. LAYOUT ---
st.title("🏭 Monitor the Reactor")
st.markdown(f"Status API : `{API_URL}`")

col_left, col_right = st.columns([1, 4])

# === ZONE GAUCHE (CONTROLE) ===
with col_left:
    st.subheader("Contrôle")
    start_clicked = st.button("▶️ DÉMARRER", type="primary")
    stop_clicked = st.button("⏹️ ANNULER", type="secondary")

    # Placeholder pour les infos textuelles
    prediction_box = st.empty()
    prediction_box.markdown("""
        <div class="result-box">
            <div class="result-title">Détection</div>
            <div class="result-value">--</div>
            <div class="result-title">Statut</div>
            <div class="result-value">Prêt</div>
        </div>
    """, unsafe_allow_html=True)

# === ZONE DROITE (VISUALISATION) ===
with col_right:
    # Fenêtre 1 : Vue Globale
    st.markdown("##### 📈 Vue d'ensemble (Pression)")
    chart_main_spot = st.empty()

    st.divider()

    # --- FENÊTRE 2 : C'est ici que les graphes sont préparés ---
    st.markdown("##### 📊 Capteurs (Données Réelles API)")
    feat_c1, feat_c2, feat_c3 = st.columns(3)

    # On crée 3 emplacements vides qui seront remplis par la boucle plus bas
    chart_feat1 = feat_c1.empty() # Futur Graphe Pression
    chart_feat2 = feat_c2.empty() # Futur Graphe Température
    chart_feat3 = feat_c3.empty() # Futur Graphe Débit

    st.divider()

    # Fenêtre 3 : État Vanne
    st.markdown("##### 🏭 État Vanne")
    img_col1, img_col2 = st.columns([1, 5])
    valve_status_spot = img_col1.empty()

# ==========================
# 5. LOGIQUE D'EXÉCUTION (Remplacement de la simulation)
# ==========================

# ... dans app.py, juste avant requests.get
#full_url = f"{API_URL}/get-process-data"
#print(f"🧐 TENTATIVE DE CONNEXION SUR : {full_url}")  # Regardez votre terminal !

#response = requests.get(full_url)


if start_clicked:
    # A. APPEL API (Au lieu de générer des fake data)
    with st.spinner("Chargement des données depuis Cloud Run..."):
        try:
            response = requests.get(f"{API_URL}/get-process-data")
            if response.status_code == 200:
                json_data = response.json()
                # Gestion erreur API
                if isinstance(json_data, dict) and "error" in json_data:
                    st.error(json_data['error'])
                    st.stop()

                df = pd.DataFrame(json_data)
                st.toast(f"✅ Données reçues : {len(df)} lignes", icon="🚀")
            else:
                st.error(f"Erreur HTTP {response.status_code}")
                st.stop()
        except Exception as e:
            st.error(f"Erreur de connexion : {e}")
            st.stop()

    # B. INITIALISATION LISTES
    history_pression = []
    history_temp = []
    history_debit = []
    history_sample = []

    # C. BOUCLE D'ANIMATION
    # On parcourt le DataFrame reçu de l'API ligne par ligne
    for index, row in df.iterrows():

        # Lecture des vraies colonnes du CSV
        val_press = row['xmeas_7']
        val_temp = row['xmeas_9']
        val_debit = row['xmeas_10']
        val_sample = row.get('sample', index)

        # Ajout aux historiques pour le tracé
        history_pression.append(val_press)
        history_temp.append(val_temp)
        history_debit.append(val_debit)
        history_sample.append(val_sample)

        # Logique simple de seuil (Simulation d'alerte)
        current_fault = "Normal"
        if val_press > 2800: current_fault = "Surpression"
        elif val_press < 2650: current_fault = "Sous-pression"

        color_status = "#FAFAFA" if current_fault == "Normal" else "#FF4B4B"

        # Mise à jour Info Box
        prediction_box.markdown(f"""
            <div class="result-box">
                <div class="result-title">Échantillon</div>
                <div class="result-value">{val_sample}</div>
                <div class="result-title">État</div>
                <div class="result-value" style="color: {color_status};">{current_fault}</div>
            </div>
        """, unsafe_allow_html=True)

        # --- MISE A JOUR FENÊTRE 2 (LES 3 GRAPHES) ---

        # Graphe 1 : Pression
        fig1 = go.Figure(go.Scatter(x=history_sample, y=history_pression, mode='lines', line=dict(color='cyan')))
        fig1.update_layout(height=200, margin=dict(t=30,b=10,l=10,r=10), title="Pression (xmeas_7)", template="plotly_dark")
        chart_feat1.plotly_chart(fig1, use_container_width=True, key=f"f1_{index}")

        # Graphe 2 : Température
        fig2 = go.Figure(go.Scatter(x=history_sample, y=history_temp, mode='lines', line=dict(color='orange')))
        fig2.update_layout(height=200, margin=dict(t=30,b=10,l=10,r=10), title="Température (xmeas_9)", template="plotly_dark")
        chart_feat2.plotly_chart(fig2, use_container_width=True, key=f"f2_{index}")

        # Graphe 3 : Débit
        fig3 = go.Figure(go.Scatter(x=history_sample, y=history_debit, mode='lines', line=dict(color='#00FF00')))
        fig3.update_layout(height=200, margin=dict(t=30,b=10,l=10,r=10), title="Débit (xmeas_10)", template="plotly_dark")
        chart_feat3.plotly_chart(fig3, use_container_width=True, key=f"f3_{index}")

        # Graphe Vue Globale
        fig_main = px.line(x=history_sample, y=history_pression, title="Vue Globale Pression")
        fig_main.update_layout(height=250, margin=dict(t=30,b=20,l=20,r=20), paper_bgcolor="rgba(0,0,0,0)")
        chart_main_spot.plotly_chart(fig_main, use_container_width=True, key=f"main_{index}")

        # Vanne
        valve_color = "red" if current_fault != "Normal" else "green"
        valve_status_spot.markdown(f"""
            <div style="text-align: center; margin-top: 20px;">
                <div style="width: 50px; height: 50px; background-color: {valve_color}; border-radius: 50%; border: 2px solid white; margin: 0 auto; box-shadow: 0 0 15px {valve_color};"></div>
            </div>
        """, unsafe_allow_html=True)

        time.sleep(0.05)
