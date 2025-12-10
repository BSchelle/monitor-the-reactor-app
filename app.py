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

# --- 3. PARAMÈTRES SCIENTIFIQUES ---
TIME_STEP_MINUTES = 3    # 1 point = 3 minutes
INJECTION_TIME_MIN = 60  # La panne survient à 60 min
PERSISTENCE_LIMIT = 2    # Nombre de confirmations pour valider le DIAGNOSTIC

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
    .result-title { font-size: 0.8em; color: #aaaaaa; margin-bottom: 2px; text-transform: uppercase; letter-spacing: 1px;}
    .result-value { font-size: 1.4em; font-weight: bold; color: #FAFAFA; margin-bottom: 12px; }

    div[data-testid="stMetricValue"] {
        font-size: 28px;
        color: #FAFAFA;
    }
    </style>
""", unsafe_allow_html=True)

# --- 5. INITIALISATION DU SESSION STATE ---
if 'simulation_running' not in st.session_state: st.session_state.simulation_running = False
if 'final_report' not in st.session_state: st.session_state.final_report = None
if 'final_figs' not in st.session_state: st.session_state.final_figs = None

# --- 6. MISE EN PAGE ---
st.title("🏭 Monitor the Reactor")

col_left, col_right = st.columns([1, 4])

# === ZONE GAUCHE (CONTROLE) ===
with col_left:
    st.subheader("Contrôle")
    scenario_options = {f"Panne #{i}": i for i in range(1, 21)}
    selected_scenario_name = st.selectbox("Sélectionnez le scénario", list(scenario_options.keys()), disabled=st.session_state.simulation_running)
    selected_fault_code = scenario_options[selected_scenario_name]

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("▶️ DÉMARRER", type="primary", use_container_width=True):
            st.session_state.simulation_running = True
            st.session_state.final_report = None
            st.session_state.final_figs = None
            st.session_state.anomaly_detected = False
            st.session_state.anomaly_time_min = None
            st.session_state.diagnosis_confirmed = False
            st.session_state.diagnosis_time_min = None
            st.session_state.diag_consecutive_count = 0

    with col_btn2:
        if st.button("⏹️ ANNULER", type="primary", use_container_width=True):
            st.session_state.simulation_running = False
            st.session_state.final_report = None
            st.session_state.final_figs = None

    status_txt = "En cours..." if st.session_state.simulation_running else "Prêt"
    st.markdown(f"""<div class="result-box"><div class="result-title">Statut</div><div class="result-value">{status_txt}</div></div>""", unsafe_allow_html=True)


# === ZONE DROITE (VISUALISATION) ===
with col_right:
    # 1. Zone Graphiques
    st.markdown("##### 📈 Diagnostic Panne (Vue Globale)")
    chart_main_spot = st.empty()
    st.divider()

    st.markdown("##### 📊 Capteurs du réacteur (Temps réel)")
    feat_c1, feat_c2, feat_c3 = st.columns(3)
    chart_feat1 = feat_c1.empty()
    chart_feat2 = feat_c2.empty()
    chart_feat3 = feat_c3.empty()

    # LOGIQUE D'AFFICHAGE DES GRAPHES STOCKÉS (FIN DE SIMULATION)
    if not st.session_state.simulation_running and st.session_state.final_figs:
        chart_main_spot.plotly_chart(st.session_state.final_figs['main'], use_container_width=True)
        chart_feat1.plotly_chart(st.session_state.final_figs['f1'], use_container_width=True)
        chart_feat2.plotly_chart(st.session_state.final_figs['f2'], use_container_width=True)
        chart_feat3.plotly_chart(st.session_state.final_figs['f3'], use_container_width=True)

    # 2. Zone Rapport Final
    if st.session_state.final_report:
        st.divider()
        st.markdown("### 📝 Rapport de Simulation")
        rep = st.session_state.final_report
        m1, m2, m3 = st.columns(3)
        m1.metric("Scénario Joué", rep['scenario'])
        det_val = f"{rep['detection_delay']:.1f} min" if rep['detection_delay'] is not None else "Non Détecté"
        m2.metric("⏱️ Délai Détection", det_val, help="Temps après injection (1h). Marqueur Orange.")
        diag_val = f"{rep['diagnosis_delay']:.1f} min" if rep['diagnosis_delay'] is not None else "Non Identifié"
        m3.metric("🎯 Délai Diagnostic", diag_val, help="Temps après injection (1h). Marqueur Rouge.")
        if rep['diagnosis_delay'] is not None: st.success("✅ Succès : Panne identifiée et localisée.")
        else: st.warning("⚠️ Échec : Identification incomplète dans le temps imparti.")


# ==========================
# 7. LOGIQUE D'EXÉCUTION
# ==========================
if st.session_state.simulation_running:

    @st.cache_data(ttl=600)
    def fetch_data_from_api(url):
        try:
            response = requests.get(f"{url}/get-process-data")
            return pd.DataFrame(response.json()) if response.status_code == 200 else pd.DataFrame()
        except Exception: return pd.DataFrame()

    with st.spinner("Chargement des données..."): df_full = fetch_data_from_api(API_URL)
    if df_full.empty: st.error("Erreur API."); st.session_state.simulation_running = False; st.stop()
    if 'faultNumber' in df_full.columns:
        df_full['faultNumber'] = df_full['faultNumber'].astype(int)
        simulation_data = df_full[df_full['faultNumber'] == selected_fault_code].reset_index(drop=True)
    else: simulation_data = df_full
    if simulation_data.empty: st.error("Aucune donnée."); st.session_state.simulation_running = False; st.stop()

    # Initialisation listes
    history_pression, history_temp, history_debit, history_pred, history_time = [], [], [], [], []

    # BOUCLE D'ANIMATION
    for index, row in simulation_data.iterrows():
        if not st.session_state.simulation_running: break

        # Lecture
        val_press = row.get('xmeas_7', 0); val_temp = row.get('xmeas_9', 0); val_debit = row.get('xmeas_10', 0)
        val_sample = row.get('sample', index)
        val_detector = float(row.get('detector', 0)); val_diagnosis = float(row.get('faults_pred', 0))

        current_time_hours = (val_sample * TIME_STEP_MINUTES) / 60
        current_time_minutes = val_sample * TIME_STEP_MINUTES
        display_pred = 0.0 if current_time_hours < 1.0 else val_diagnosis

        # Algorithme Hybride
        if current_time_minutes > INJECTION_TIME_MIN:
            if not st.session_state.anomaly_detected and val_detector > 0.5:
                st.session_state.anomaly_detected = True
                st.session_state.anomaly_time_min = current_time_minutes
            if not st.session_state.diagnosis_confirmed:
                if round(val_diagnosis) == selected_fault_code: st.session_state.diag_consecutive_count += 1
                else: st.session_state.diag_consecutive_count = 0
                if st.session_state.diag_consecutive_count >= PERSISTENCE_LIMIT:
                    st.session_state.diagnosis_confirmed = True
                    st.session_state.diagnosis_time_min = current_time_minutes

        # Graphiques
        history_pression.append(val_press); history_temp.append(val_temp); history_debit.append(val_debit)
        history_pred.append(display_pred); history_time.append(current_time_hours)

        fig1 = go.Figure(go.Scatter(x=history_time, y=history_pression, mode='lines', line=dict(color='cyan')))
        fig1.update_layout(height=180, margin=dict(t=30,b=10,l=10,r=10), title="Pression", xaxis_title="Heures", template="plotly_dark")
        chart_feat1.plotly_chart(fig1, use_container_width=True, key=f"f1_{index}")

        fig2 = go.Figure(go.Scatter(x=history_time, y=history_temp, mode='lines', line=dict(color='orange')))
        fig2.update_layout(height=180, margin=dict(t=30,b=10,l=10,r=10), title="Température", xaxis_title="Heures", template="plotly_dark")
        chart_feat2.plotly_chart(fig2, use_container_width=True, key=f"f2_{index}")

        fig3 = go.Figure(go.Scatter(x=history_time, y=history_debit, mode='lines', line=dict(color='#00FF00')))
        fig3.update_layout(height=180, margin=dict(t=30,b=10,l=10,r=10), title="Débit", xaxis_title="Heures", template="plotly_dark")
        chart_feat3.plotly_chart(fig3, use_container_width=True, key=f"f3_{index}")

        fig_main = go.Figure()
        fig_main.add_trace(go.Scatter(x=history_time, y=history_pred, mode='lines', name='Diag', line=dict(color='#FF4B4B', width=2)))
        fig_main.add_vrect(x0=0, x1=1, fillcolor="gray", opacity=0.3, line_width=0, annotation_text="STABILISATION", annotation_position="top left", annotation_font_color="white")
        fig_main.update_layout(title="Type de Panne Identifiée", height=250, margin=dict(t=30,b=20,l=20,r=20), paper_bgcolor="rgba(0,0,0,0)", template="plotly_dark", xaxis=dict(title="Heures", range=[0, max(1.1, current_time_hours + 0.1)]), yaxis=dict(title="Code Panne", visible=True, automargin=True))
        chart_main_spot.plotly_chart(fig_main, use_container_width=True, key=f"main_{index}")

        time.sleep(0.05)

    # --- FIN DE SIMULATION ---
    if st.session_state.simulation_running:

        # 1. Calcul Rapport
        d_det, d_diag = None, None
        det_time_h, diag_time_h = None, None

        if st.session_state.anomaly_detected:
            d_det = max(0, st.session_state.anomaly_time_min - INJECTION_TIME_MIN)
            det_time_h = st.session_state.anomaly_time_min / 60

        if st.session_state.diagnosis_confirmed:
            d_diag = max(0, st.session_state.diagnosis_time_min - INJECTION_TIME_MIN)
            diag_time_h = st.session_state.diagnosis_time_min / 60

        st.session_state.final_report = {"scenario": selected_scenario_name, "detection_delay": d_det, "diagnosis_delay": d_diag}

        # 2. MARQUEURS UNIQUEMENT SUR VUE GLOBALE
        def add_markers_to_fig(fig_to_mark):
            if det_time_h:
                fig_to_mark.add_vline(x=det_time_h, line_width=2, line_dash="dash", line_color="orange", annotation_text="Détection", annotation_position="top right")
            if diag_time_h:
                pos = "bottom right" if (det_time_h and abs(diag_time_h - det_time_h) < 0.1) else "top right"
                fig_to_mark.add_vline(x=diag_time_h, line_width=2, line_dash="solid", line_color="red", annotation_text="Diagnostic", annotation_position=pos)
            return fig_to_mark

        st.session_state.final_figs = {
            'main': add_markers_to_fig(fig_main), # OUI pour le principal
            'f1': fig1, # NON pour les capteurs
            'f2': fig2,
            'f3': fig3
        }

        st.session_state.simulation_running = False
        st.rerun()
