import streamlit as st
import pandas as pd
import numpy as np
import time
import plotly.graph_objects as go
import plotly.express as px
import requests
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="Monitor the reactor", page_icon="🏭", layout="wide")

# --- GESTION DE L'URL API ---
def get_api_url():
    """
    Récupère l'URL de l'API selon l'environnement.
    Priorité : Secrets (Streamlit Cloud) > Env Var (Docker/Cloud Run) > Localhost
    """
    # Cas 1 : Streamlit Cloud (Secrets)
    if "API_URL" in st.secrets:
        return st.secrets["API_URL"]
    # Cas 2 : Docker / Cloud Run (Variables d'environnement)
    elif "API_URL" in os.environ:
        return os.environ["API_URL"]
    # Cas 3 : Localhost (Défaut)
    else:
        return "http://localhost:8000"

API_URL = get_api_url()

# --- CSS PERSONNALISÉ ---
st.markdown("""
    <style>
    /* Fond général sombre */
    .main { background-color: #0E1117; }

    /* BOITE DE RÉSULTAT (ZONE 1) */
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


# --- MENU ---
st.sidebar.title("Navigation")
st.sidebar.page_link("app.py", label="Accueil", icon="🏠")
# Si vous avez créé le fichier pages/2_🔧_Test_API.py, décommentez la ligne ci-dessous
# st.sidebar.page_link("pages/2_🔧_Test_API.py", label="Test API", icon="1️⃣")

# --- INTERFACE PRINCIPALE ---
st.title("🏭 Monitor the Reactor :")
st.markdown("Architecture : Récupération Data Cloud Run -> Visualisation Temps Réel")

# --- MISE EN PAGE : ZONE 1 (Gauche) et ZONE 2 (Droite) ---
col_left, col_right = st.columns([1, 4])

# ==========================
# ZONE 1 : CONTROLE
# ==========================
with col_left:
    st.subheader("Contrôle")

    start_clicked = st.button("▶️ DÉMARRER", type="primary", key="start_btn")
    stop_clicked = st.button("⏹️ ANNULER", type="secondary", key="stop_btn")

    # Rectangle pour les prédictions
    prediction_box = st.empty()

    # Affichage par défaut (Vide)
    prediction_box.markdown("""
        <div class="result-box">
            <div class="result-title">Détection du délai</div>
            <div class="result-value">--</div>
            <div class="result-title">Statut Procédé</div>
            <div class="result-value">Prêt</div>
        </div>
    """, unsafe_allow_html=True)


# ==========================
# ZONE 2 : VISUALISATION
# ==========================
with col_right:
    # --- FENÊTRE 1 : Graphique Principal (Top) ---
    st.markdown("##### 📈 Vue d'ensemble (Pression)")
    chart_main_spot = st.empty()

    st.divider()

    # --- FENÊTRE 2 : 3 GRAPHES FEATURES (Milieu) ---
    st.markdown("##### 📊 Capteurs (Données Réelles)")
    feat_c1, feat_c2, feat_c3 = st.columns(3)
    chart_feat1 = feat_c1.empty() # Pression
    chart_feat2 = feat_c2.empty() # Température
    chart_feat3 = feat_c3.empty() # Débit

    st.divider()

    # --- FENÊTRE 3 : ETAT VANNE (Bas) ---
    st.markdown("##### 🏭 État Vanne (Simulé sur seuil)")
    img_col1, img_col2 = st.columns([1, 5])
    valve_status_spot = img_col1.empty()


# ==========================
# 4. LOGIQUE RÉELLE (API)
# ==========================

if start_clicked:
    # 1. APPEL API POUR RÉCUPÉRER LES DONNÉES
    # ---------------------------------------
    with st.spinner("Connexion à l'API Cloud Run..."):
        try:
            # On appelle la route que nous avons créée ensemble
            response = requests.get(f"{API_URL}/get-process-data")

            if response.status_code == 200:
                json_data = response.json()

                # Gestion des erreurs renvoyées par l'API
                if isinstance(json_data, dict) and "error" in json_data:
                    st.error(f"L'API a renvoyé une erreur : {json_data['error']}")
                    st.stop()

                # Création du DataFrame
                df = pd.DataFrame(json_data)

                # Vérification des colonnes nécessaires
                required_cols = ['xmeas_7', 'xmeas_9', 'xmeas_10']
                if not all(col in df.columns for col in required_cols):
                    st.error(f"Colonnes manquantes. Reçu : {df.columns.tolist()}")
                    st.stop()

                st.toast(f"✅ {len(df)} points de données chargés !", icon="🚀")

            else:
                st.error(f"Erreur HTTP {response.status_code}")
                st.stop()

        except Exception as e:
            st.error(f"Impossible de joindre l'API : {e}")
            st.stop()

    # 2. INITIALISATION DES HISTORIQUES
    # ---------------------------------
    history_pression = []   # xmeas_7
    history_temp = []       # xmeas_9
    history_debit = []      # xmeas_10
    history_sample = []     # sample ou index

    # 3. BOUCLE D'ANIMATION (LECTURE DU DATAFRAME)
    # --------------------------------------------
    # On itère sur chaque ligne du DataFrame reçu
    for index, row in df.iterrows():

        # Extraction des valeurs réelles
        val_press = row['xmeas_7']
        val_temp = row['xmeas_9']
        val_debit = row['xmeas_10']
        val_sample = row.get('sample', index) # Utilise l'index si 'sample' n'existe pas

        # Mise à jour des listes
        history_pression.append(val_press)
        history_temp.append(val_temp)
        history_debit.append(val_debit)
        history_sample.append(val_sample)

        # ---------------------------------------
        # LOGIQUE DE DÉTECTION (Simulée pour l'instant)
        # Ici, vous pourrez plus tard appeler votre API de Prédiction
        # Pour l'exemple, on crée une alerte si la pression dépasse un seuil arbitraire
        current_fault = "Normal"
        if val_press > 2800: # Exemple de seuil arbitraire sur xmeas_7
            current_fault = "Surpression"
        elif val_press < 2650:
            current_fault = "Sous-pression"

        color_status = "#FAFAFA" if current_fault == "Normal" else "#FF4B4B"
        # ---------------------------------------

        # A. MISE À JOUR ZONE 1 (INFO BOX)
        prediction_box.markdown(f"""
            <div class="result-box">
                <div class="result-title">Échantillon</div>
                <div class="result-value">{val_sample}</div>
                <div class="result-title">État Déduit</div>
                <div class="result-value" style="color: {color_status};">{current_fault}</div>
            </div>
        """, unsafe_allow_html=True)

        # B. MISE À JOUR ZONE 2 (GRAPHIQUES)

        # Graphique 1 : Pression (xmeas_7)
        fig1 = go.Figure(go.Scatter(x=history_sample, y=history_pression, mode='lines', line=dict(color='cyan')))
        fig1.update_layout(height=200, margin=dict(l=10, r=10, t=30, b=10), title="Pression (xmeas_7)", template="plotly_dark")
        chart_feat1.plotly_chart(fig1, use_container_width=True, key=f"f1_{index}")

        # Graphique 2 : Température (xmeas_9)
        fig2 = go.Figure(go.Scatter(x=history_sample, y=history_temp, mode='lines', line=dict(color='orange')))
        fig2.update_layout(height=200, margin=dict(l=10, r=10, t=30, b=10), title="Température (xmeas_9)", template="plotly_dark")
        chart_feat2.plotly_chart(fig2, use_container_width=True, key=f"f2_{index}")

        # Graphique 3 : Débit (xmeas_10)
        fig3 = go.Figure(go.Scatter(x=history_sample, y=history_debit, mode='lines', line=dict(color='#00FF00')))
        fig3.update_layout(height=200, margin=dict(l=10, r=10, t=30, b=10), title="Débit (xmeas_10)", template="plotly_dark")
        chart_feat3.plotly_chart(fig3, use_container_width=True, key=f"f3_{index}")

        # Graphique Principal (Focus sur Pression aussi pour l'instant)
        fig_main = px.line(x=history_sample, y=history_pression)
        fig_main.update_layout(height=250, margin=dict(l=20, r=20, t=20, b=20), paper_bgcolor="rgba(0,0,0,0)", title="Vue Globale Pression")
        chart_main_spot.plotly_chart(fig_main, use_container_width=True, key=f"main_{index}")

        # C. MISE À JOUR INDICATEUR VANNE
        valve_color = "red" if current_fault != "Normal" else "green"
        valve_text = "ALERTE" if current_fault != "Normal" else "OK"

        valve_status_spot.markdown(f"""
            <div style="text-align: center; margin-top: 20px;">
                <div style="
                    width: 50px; height: 50px;
                    background-color: {valve_color};
                    border-radius: 50%;
                    border: 2px solid white;
                    margin: 0 auto;
                    box-shadow: 0 0 15px {valve_color};
                "></div>
                <p style="margin-top: 5px; font-weight: bold;">{valve_text}</p>
            </div>
        """, unsafe_allow_html=True)

        # Contrôle de vitesse de l'animation
        time.sleep(0.05)
