import streamlit as st
import pandas as pd
import time
import plotly.graph_objects as go
import plotly.express as px
import requests
import os

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Monitor the reactor", page_icon="🏭", layout="wide")

# --- 2. FONCTION POUR L'URL API ---
def get_api_url():
    if "API_URL" in st.secrets:
        return st.secrets["API_URL"]
    elif "API_URL" in os.environ:
        return os.environ["API_URL"]
    else:
        return "http://localhost:8000"

API_URL = get_api_url()

# --- 3. CSS (NETTOYÉ) ---
# On garde uniquement le style pour la boîte de résultat, plus de hack pour les boutons.
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
    .result-value { font-size: 1.2em; font-weight: bold; color: #FAFAFA; margin-bottom: 0px; }
    </style>
""", unsafe_allow_html=True)

# --- 4. MISE EN PAGE ---
st.title("🏭 Monitor the Reactor")

col_left, col_right = st.columns([1, 4])

# === ZONE GAUCHE (CONTROLE) ===
with col_left:
    st.subheader("Contrôle")

    # Génération automatique des 20 scénarios
    scenario_options = {f"Panne #{i}": i for i in range(1, 21)}

    # Initialisation de l'état
    if 'simulation_running' not in st.session_state:
        st.session_state.simulation_running = False

    # Menu déroulant (désactivé pendant la simulation)
    selected_scenario_name = st.selectbox(
        "Sélectionnez le scénario",
        list(scenario_options.keys()),
        disabled=st.session_state.simulation_running
    )
    selected_fault_code = scenario_options[selected_scenario_name]

    # --- BOUTONS DE CONTROLE ---
    col_btn1, col_btn2 = st.columns(2)

    with col_btn1:
        # Bouton DÉMARRER (Vert par défaut selon votre thème)
        if st.button("▶️ DÉMARRER", type="primary", use_container_width=True):
            st.session_state.simulation_running = True

    with col_btn2:
        # Bouton ANNULER (Vert aussi, même taille, simple et stable)
        if st.button("⏹️ ANNULER", type="primary", use_container_width=True):
            st.session_state.simulation_running = False

    # Boîte d'info Statut
    status_text = "En cours" if st.session_state.simulation_running else "Prêt"
    prediction_box = st.empty()
    prediction_box.markdown(f"""
        <div class="result-box">
            <div class="result-title">Scénario Cible</div>
            <div class="result-value">{selected_fault_code}</div>
            <div class="result-title">Statut</div>
            <div class="result-value">{status_text}</div>
        </div>
    """, unsafe_allow_html=True)


# === ZONE DROITE (VISUALISATION) ===
with col_right:
    st.markdown("##### 📈 Prédiction des pannes")
    chart_main_spot = st.empty()
    st.divider()

    st.markdown("##### 📊 Capteurs du réacteur")
    feat_c1, feat_c2, feat_c3 = st.columns(3)
    chart_feat1 = feat_c1.empty()
    chart_feat2 = feat_c2.empty()
    chart_feat3 = feat_c3.empty()


# ==========================
# 5. LOGIQUE D'EXÉCUTION
# ==========================

if st.session_state.simulation_running:

    # A. APPEL API AVEC CACHE
    @st.cache_data(ttl=600)
    def fetch_data_from_api(url):
        try:
            response = requests.get(f"{url}/get-process-data")
            if response.status_code == 200:
                return pd.DataFrame(response.json())
            else:
                return pd.DataFrame()
        except Exception:
            return pd.DataFrame()

    with st.spinner("Chargement des données API..."):
        df_full = fetch_data_from_api(API_URL)

    # Gestion erreur API
    if df_full.empty:
        st.error("Impossible de récupérer les données depuis l'API.")
        st.session_state.simulation_running = False
        st.stop()

    # B. FILTRAGE DES DONNÉES (Le cœur de votre demande)
    if 'faultNumber' in df_full.columns:
        # Conversion en int pour être sûr de la correspondance
        df_full['faultNumber'] = df_full['faultNumber'].astype(int)
        # On ne garde que les ~500 lignes de la panne choisie
        simulation_data = df_full[df_full['faultNumber'] == selected_fault_code].reset_index(drop=True)
    else:
        st.warning("Colonne 'faultNumber' introuvable. Affichage brut.")
        simulation_data = df_full

    # Gestion erreur Scénario vide
    if simulation_data.empty:
        st.error(f"Aucune donnée trouvée pour la {selected_scenario_name} (Code {selected_fault_code}).")
        st.session_state.simulation_running = False
        st.stop()

    st.toast(f"Démarrage : {len(simulation_data)} points chargés", icon="🚀")

    # C. INITIALISATION DES LISTES POUR L'ANIMATION
    history_pression = []
    history_temp = []
    history_debit = []
    history_pred = []
    history_sample = []

    # D. BOUCLE D'ANIMATION
    for index, row in simulation_data.iterrows():

        # Interruption immédiate via bouton ANNULER
        if not st.session_state.simulation_running:
            break

        # Lecture des valeurs
        val_press = row.get('xmeas_7', 0)
        val_temp = row.get('xmeas_9', 0)
        val_debit = row.get('xmeas_10', 0)
        val_pred = row.get('faults_pred', 0)
        val_sample = row.get('sample', index)

        # Ajout aux historiques
        history_pression.append(val_press)
        history_temp.append(val_temp)
        history_debit.append(val_debit)
        history_pred.append(val_pred)
        history_sample.append(val_sample)

        # 1. Mise à jour Pression
        fig1 = go.Figure(go.Scatter(x=history_sample, y=history_pression, mode='lines', line=dict(color='cyan')))
        fig1.update_layout(height=200, margin=dict(t=30,b=10,l=10,r=10), title="Pression (xmeas_7)", template="plotly_dark")
        chart_feat1.plotly_chart(fig1, use_container_width=True, key=f"f1_{index}")

        # 2. Mise à jour Température
        fig2 = go.Figure(go.Scatter(x=history_sample, y=history_temp, mode='lines', line=dict(color='orange')))
        fig2.update_layout(height=200, margin=dict(t=30,b=10,l=10,r=10), title="Température (xmeas_9)", template="plotly_dark")
        chart_feat2.plotly_chart(fig2, use_container_width=True, key=f"f2_{index}")

        # 3. Mise à jour Débit
        fig3 = go.Figure(go.Scatter(x=history_sample, y=history_debit, mode='lines', line=dict(color='#00FF00')))
        fig3.update_layout(height=200, margin=dict(t=30,b=10,l=10,r=10), title="Débit (xmeas_10)", template="plotly_dark")
        chart_feat3.plotly_chart(fig3, use_container_width=True, key=f"f3_{index}")

        # 4. Mise à jour Vue Globale
        fig_main = px.line(x=history_sample, y=history_pred, title="Vue Globale Prédiction")
        fig_main.update_layout(height=250, margin=dict(t=30,b=20,l=20,r=20), paper_bgcolor="rgba(0,0,0,0)")
        chart_main_spot.plotly_chart(fig_main, use_container_width=True, key=f"main_{index}")

        # Vitesse d'animation
        time.sleep(0.05)

    # Message de fin
    if st.session_state.simulation_running:
        st.success("Fin de la simulation.")
        st.session_state.simulation_running = False
