import streamlit as st
import pandas as pd
import numpy as np
import time
import plotly.graph_objects as go
import plotly.express as px

# --- CONFIGURATION ---
st.set_page_config(page_title="Monitor the reactor", page_icon="🏭", layout="wide")

# --- CSS PERSONNALISÉ ---
#st.markdown("""
#    <style>
#    .main { background-color: #0E1117; }    # Dark Mode
#    #.stMetric { background-color: #262730; padding: 10px; border-radius: 5px; } Chiffres en rouge
#    div.block-container { padding-top: 2rem; }
#    </style>
#    """, unsafe_allow_html=True)

# --- 2. CSS PERSONNALISÉ ---
st.markdown("""
    <style>
    /* Fond général sombre */
    .main { background-color: #0E1117; }

    /* BOUTON START (VERT) */
    div.stButton > button.start-btn {
        background-color: #28a745; color: white; border: none; width: 100%;
    }
    div.stButton > button.start-btn:hover { background-color: #218838; color: white; }

    /* BOUTON ANNULER (ROUGE) */
    div.stButton > button.stop-btn {
        background-color: #dc3545; color: white; border: none; width: 100%;
    }
    div.stButton > button.stop-btn:hover { background-color: #c82333; color: white; }

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

    /* Indicateur Vanne */
    .valve-indicator {
        display: inline-block; width: 20px; height: 20px; border-radius: 50%; margin-right: 10px;
    }
    </style>
    """, unsafe_allow_html=True)


# --- MENU ---
st.sidebar.title("Navigation")
st.sidebar.page_link("app.py", label="Accueil", icon="🏠")
st.sidebar.page_link("pages/page_1.py", label="Test API", icon="1️⃣")

# --- INTERFACE PRINCIPALE ---
st.title("🏭 Monitor the Reactor :")
#st.title("Tennessee Eastman Process")
st.markdown("Architecture : Détection d'anomalie + Diagnostic")

# --- MISE EN PAGE : ZONE 1 (Gauche) et ZONE 2 (Droite) ---
# Le ratio [1, 4] signifie que la colonne de droite est 4 fois plus large
col_left, col_right = st.columns([1, 4])

# ==========================
# ZONE 1 : CONTROLE
# ==========================
with col_left:
    st.subheader("Contrôle")

    # Bouton Démarrer (On utilise une clé unique pour gérer l'état si besoin)
    start_clicked = st.button("▶️ DÉMARRER", type="primary", key="start_btn")

    # Bouton Annuler
    stop_clicked = st.button("⏹️ ANNULER", type="secondary", key="stop_btn")

    # Rectangle pour les prédictions (Placeholder vide au début)
    prediction_box = st.empty()

    # Affichage par défaut du rectangle (Vide)
    prediction_box.markdown("""
        <div class="result-box">
            <div class="result-title">Détection du délai</div>
            <div class="result-value">--</div>
            <div class="result-title">Type de Panne</div>
            <div class="result-value">--</div>
        </div>
    """, unsafe_allow_html=True)


# ==========================
# ZONE 2 : VISUALISATION
# ==========================
with col_right:
    # --- FENÊTRE 1 : COURBE FAULTS (Top) ---
    st.markdown("##### 📈 Probabilité de Panne (Fault Probability)")
    chart_fault_spot = st.empty() # Placeholder pour le graph

    st.divider() # Ligne de séparation

    # --- FENÊTRE 2 : 3 GRAPHES FEATURES (Milieu) ---
    st.markdown("##### 📊 Features Pertinentes")
    # On prépare 3 colonnes pour les 3 petits graphes
    feat_c1, feat_c2, feat_c3 = st.columns(3)
    # Placeholders pour chaque petit graph
    chart_feat1 = feat_c1.empty()
    chart_feat2 = feat_c2.empty()
    chart_feat3 = feat_c3.empty()

    st.divider()

    # --- FENÊTRE 3 : IMAGE PROCESS & VANNE (Bas) ---
    st.markdown("##### 🏭 Schéma du Procédé & État Vanne")

    # On divise pour avoir l'indicateur à côté ou au-dessus de l'image
    img_col1, img_col2 = st.columns([1, 5])

    # Placeholder pour le statut de la vanne (Carré gris/rouge)
    valve_status_spot = img_col1.empty()

    # Affichage de l'image statique du Tennessee Eastman
    # Remplace l'URL par ton image locale si tu préfères
    #img_col2.image("https://ars.els-cdn.com/content/image/3-s2.0-B9780444538703500296-f29-01-9780444538703.jpg",
    #               caption="Tennessee Eastman Process Flowsheet", use_container_width=True)


# ==========================
# 4. LOGIQUE DE SIMULATION
# ==========================

if start_clicked:
    # Variables pour stocker l'historique (pour les courbes)
    history_fault = []
    history_feat1 = []
    history_feat2 = []
    history_feat3 = []

    # BOUCLE DE SIMULATION (ex: 50 itérations)
    for i in range(50):
        # A. SIMULATION DES DONNÉES (Remplace par tes .predict)
        # -----------------------------------------------------
        current_delay = np.random.randint(10, 200) # Faux délai
        current_fault = "Normal" if i < 30 else "Panne Vanne A" # Simule une panne après 30 steps
        prob_fault = 0.1 if i < 30 else 0.9 + np.random.normal(0, 0.05)

        # Fake features
        f1 = np.sin(i/5) + np.random.normal(0, 0.1)
        f2 = np.cos(i/5) + np.random.normal(0, 0.1)
        f3 = np.random.rand()

        # Mise à jour historiques
        history_fault.append(prob_fault)
        history_feat1.append(f1)
        history_feat2.append(f2)
        history_feat3.append(f3)

        # B. MISE À JOUR ZONE 1 (RECTANGLE INFOS)
        # ---------------------------------------
        color_status = "#FAFAFA" if current_fault == "Normal" else "#FF4B4B" # Rouge si panne
        prediction_box.markdown(f"""
            <div class="result-box">
                <div class="result-title">Détection du délai</div>
                <div class="result-value">{current_delay} ms</div>
                <div class="result-title">État du système</div>
                <div class="result-value" style="color: {color_status};">{current_fault}</div>
            </div>
        """, unsafe_allow_html=True)

        # C. MISE À JOUR ZONE 2 (GRAPHIQUES)
        # ----------------------------------

        # 1. Grand Graphique (Faults)
        fig_main = px.line(y=history_fault, x=range(len(history_fault)), labels={'x': 'Samples', 'y': 'Probabilité Panne'})
        fig_main.update_layout(height=250, margin=dict(l=20, r=20, t=20, b=20), paper_bgcolor="rgba(0,0,0,0)")
        chart_fault_spot.plotly_chart(fig_main, use_container_width=True, key=f"main_{i}")

        # 2. Les 3 petits graphiques (Features)
        # Astuce : On crée des figures simples pour la démo
        fig1 = go.Figure(go.Scatter(y=history_feat1, mode='lines', line=dict(color='cyan')))
        fig1.update_layout(height=250, margin=dict(l=10, r=10, t=22, b=10), title="Pression", template="plotly_dark")
        chart_feat1.plotly_chart(fig1, use_container_width=True, key=f"f1_{i}")

        fig2 = go.Figure(go.Scatter(y=history_feat2, mode='lines', line=dict(color='orange')))
        fig2.update_layout(height=250, margin=dict(l=10, r=10, t=22, b=10), title="Température", template="plotly_dark")
        chart_feat2.plotly_chart(fig2, use_container_width=True, key=f"f2_{i}")

        fig3 = go.Figure(go.Bar(y=[history_feat3[-1]], marker_color='lightgreen')) # Bar chart pour varier
        fig3.update_layout(height=250, margin=dict(l=10, r=10, t=22, b=10), title="Débit", template="plotly_dark")
        chart_feat3.plotly_chart(fig3, use_container_width=True, key=f"f3_{i}")

        # D. MISE À JOUR IMAGE (Carré Rouge/Gris)
        # ---------------------------------------
        # Si panne détectée, carré ROUGE, sinon GRIS
        valve_color = "red" if current_fault != "Normal" else "grey"
        valve_text = "DÉFAILLANCE" if current_fault != "Normal" else "OK"

        # On affiche un carré de couleur stylisé via Markdown
        valve_status_spot.markdown(f"""
            <div style="text-align: center; margin-top: 50px;">
                <div style="
                    width: 60px;
                    height: 60px;
                    background-color: {valve_color};
                    border-radius: 5px;
                    border: 2px solid white;
                    margin: 0 auto;
                    box-shadow: 0 0 10px {valve_color};
                "></div>
                <p style="margin-top: 10px; font-weight: bold;">VANNE X<br>{valve_text}</p>
            </div>
        """, unsafe_allow_html=True)

        # Pause pour visualiser l'animation
        time.sleep(0.1)
