import streamlit as st
import pandas as pd
import time
import plotly.graph_objects as go
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

# --- 3. PARAMÈTRE DE TEMPS ---
# 1 sample = 3 minutes
TIME_STEP_MINUTES = 3

# --- 4. CSS ---
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

# --- 5. MISE EN PAGE ---
st.title("🏭 Monitor the Reactor")

col_left, col_right = st.columns([1, 4])

# === ZONE GAUCHE (CONTROLE) ===
with col_left:
    st.subheader("Contrôle")

    scenario_options = {f"Panne #{i}": i for i in range(1, 21)}

    if 'simulation_running' not in st.session_state:
        st.session_state.simulation_running = False

    selected_scenario_name = st.selectbox(
        "Sélectionnez le scénario",
        list(scenario_options.keys()),
        disabled=st.session_state.simulation_running
    )
    selected_fault_code = scenario_options[selected_scenario_name]

    col_btn1, col_btn2 = st.columns(2)

    with col_btn1:
        if st.button("▶️ DÉMARRER", type="primary", use_container_width=True):
            st.session_state.simulation_running = True

    with col_btn2:
        if st.button("⏹️ ANNULER", type="primary", use_container_width=True):
            st.session_state.simulation_running = False

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
    st.markdown("##### 📈 Diagnostic Panne (Vue Globale)")
    chart_main_spot = st.empty()
    st.divider()

    st.markdown("##### 📊 Capteurs du réacteur (Temps réel)")
    feat_c1, feat_c2, feat_c3 = st.columns(3)
    chart_feat1 = feat_c1.empty()
    chart_feat2 = feat_c2.empty()
    chart_feat3 = feat_c3.empty()


# ==========================
# 6. LOGIQUE D'EXÉCUTION
# ==========================

if st.session_state.simulation_running:

    # A. APPEL API
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

    if df_full.empty:
        st.error("Impossible de récupérer les données depuis l'API.")
        st.session_state.simulation_running = False
        st.stop()

    # B. FILTRAGE
    if 'faultNumber' in df_full.columns:
        df_full['faultNumber'] = df_full['faultNumber'].astype(int)
        simulation_data = df_full[df_full['faultNumber'] == selected_fault_code].reset_index(drop=True)
    else:
        st.warning("Colonne 'faultNumber' introuvable. Affichage brut.")
        simulation_data = df_full

    if simulation_data.empty:
        st.error(f"Aucune donnée trouvée pour le scénario {selected_scenario_name}.")
        st.session_state.simulation_running = False
        st.stop()

    st.toast(f"Démarrage : {len(simulation_data)} points chargés", icon="🚀")

    # C. INITIALISATION DES LISTES
    history_pression = []
    history_temp = []
    history_debit = []
    history_pred = []
    history_time = []

    # D. BOUCLE D'ANIMATION
    for index, row in simulation_data.iterrows():

        if not st.session_state.simulation_running:
            break

        val_press = row.get('xmeas_7', 0)
        val_temp = row.get('xmeas_9', 0)
        val_debit = row.get('xmeas_10', 0)
        val_sample = row.get('sample', index)

        # 1. Temps (Heures)
        current_time_hours = (val_sample * TIME_STEP_MINUTES) / 60

        # 2. Masquage avant 1h (Warm-up)
        raw_pred = row.get('faults_pred', 0)

        if current_time_hours < 1.0:
            val_pred = 0.0 # On force à 0 pendant la chauffe
        else:
            val_pred = raw_pred

        # Ajout historiques
        history_pression.append(val_press)
        history_temp.append(val_temp)
        history_debit.append(val_debit)
        history_pred.append(val_pred)
        history_time.append(current_time_hours)

        # --- VISUALISATION ---

        # 1. Pression
        fig1 = go.Figure(go.Scatter(x=history_time, y=history_pression, mode='lines', line=dict(color='cyan')))
        fig1.update_layout(
            height=200, margin=dict(t=30,b=10,l=10,r=10),
            title="Pression (xmeas_7)", xaxis_title="Temps (h)", template="plotly_dark"
        )
        chart_feat1.plotly_chart(fig1, use_container_width=True, key=f"f1_{index}")

        # 2. Température
        fig2 = go.Figure(go.Scatter(x=history_time, y=history_temp, mode='lines', line=dict(color='orange')))
        fig2.update_layout(
            height=200, margin=dict(t=30,b=10,l=10,r=10),
            title="Température (xmeas_9)", xaxis_title="Temps (h)", template="plotly_dark"
        )
        chart_feat2.plotly_chart(fig2, use_container_width=True, key=f"f2_{index}")

        # 3. Débit
        fig3 = go.Figure(go.Scatter(x=history_time, y=history_debit, mode='lines', line=dict(color='#00FF00')))
        fig3.update_layout(
            height=200, margin=dict(t=30,b=10,l=10,r=10),
            title="Débit (xmeas_10)", xaxis_title="Temps (h)", template="plotly_dark"
        )
        chart_feat3.plotly_chart(fig3, use_container_width=True, key=f"f3_{index}")

        # 4. Vue Globale (MODE DYNAMIQUE + AXE VISIBLE)
        fig_main = go.Figure()

        # Trace
        fig_main.add_trace(go.Scatter(
            x=history_time,
            y=history_pred,
            mode='lines',
            name='Diagnostic',
            line=dict(color='#FF4B4B', width=2)
        ))

        # Zone Grise (Couvre toute la hauteur automatiquement)
        fig_main.add_vrect(
            x0=0, x1=1,
            fillcolor="gray", opacity=0.3,
            line_width=0,
            annotation_text="STABILISATION",
            annotation_position="top left",
            annotation_font_color="white"
        )

        fig_main.update_layout(
            title="Évolution du Diagnostic (Type de Panne)",
            height=250,
            margin=dict(t=30,b=20,l=20,r=20),
            paper_bgcolor="rgba(0,0,0,0)",
            template="plotly_dark",

            # AXE X
            xaxis=dict(
                title="Temps écoulé (heures)",
                range=[0, max(1.1, current_time_hours + 0.1)]
            ),

            # AXE Y : Réactivé (Visible) et Dynamique
            yaxis=dict(
                title="Code Panne", # L'unité est ici
                visible=True,       # On réaffiche l'axe
                automargin=True     # S'assure que le titre ne soit pas coupé
                # Pas de 'range' fixe -> s'adapte aux données
            )
        )

        chart_main_spot.plotly_chart(fig_main, use_container_width=True, key=f"main_{index}")

        time.sleep(0.05)

    if st.session_state.simulation_running:
        st.success(f"Simulation terminée. Durée totale : {current_time_hours:.1f} heures.")
        st.session_state.simulation_running = False
