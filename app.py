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
TIME_STEP_MINUTES = 3
INJECTION_TIME_MIN = 60
PERSISTENCE_LIMIT = 2

# Métadonnées (inchangé)
FAULT_METADATA = {
    1: {"desc": "Modification Ratio A/C", "f1": 0.99, "accuracy": 0.99, "difficulty": "Facile", "comment": "Détection immédiate."},
    2: {"desc": "Composition B", "f1": 0.98, "accuracy": 0.98, "difficulty": "Facile", "comment": "Signature claire."},
    3: {"desc": "Température D (Step)", "f1": 0.55, "accuracy": 0.60, "difficulty": "Difficile", "comment": "Confusion fréquente."},
    4: {"desc": "Température Réacteur", "f1": 0.95, "accuracy": 0.96, "difficulty": "Facile", "comment": "Impact thermique fort."},
    5: {"desc": "Température Entrée C", "f1": 0.40, "accuracy": 0.45, "difficulty": "Très Difficile", "comment": "Peu d'impact visible."},
    6: {"desc": "Perte Alimentation A", "f1": 0.99, "accuracy": 1.00, "difficulty": "Facile", "comment": "Arrêt total."},
    7: {"desc": "Pression Collecteur", "f1": 0.97, "accuracy": 0.98, "difficulty": "Moyen", "comment": "Bonne détection."},
}

def get_fault_info(code):
    return FAULT_METADATA.get(code, {"desc": "Scénario Standard", "f1": 0.85, "accuracy": 0.88, "difficulty": "Moyen", "comment": "Performance standard."})

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
    div[data-testid="stMetricValue"] { font-size: 26px; color: #FAFAFA; }
    </style>
""", unsafe_allow_html=True)

# --- 5. FONCTION DE DESSIN DU RÉACTEUR (NOUVEAU) ---
def create_reactor_synoptic(current_p, current_t, current_f, base_p, base_t, base_f):
    """
    Crée un schéma Plotly du réacteur avec 3 LEDs qui changent de couleur
    si la valeur dévie de plus de 2% de la valeur de base.
    """

    # Seuil de tolérance (ex: 2% de déviation = anomalie capteur)
    THRESHOLD = 0.02

    # Logique couleur (Vert = OK, Rouge = Alerte)
    def get_color(curr, base):
        if base == 0: return "#00CC96"
        dev = abs(curr - base) / base
        return "#FF4B4B" if dev > THRESHOLD else "#00CC96"

    # Calcul des couleurs pour chaque capteur
    # Si base est None (début simulation), on reste vert
    c_p = get_color(current_p, base_p) if base_p else "#00CC96"
    c_t = get_color(current_t, base_t) if base_t else "#00CC96"
    c_f = get_color(current_f, base_f) if base_f else "#00CC96"

    fig = go.Figure()

    # 1. Le Réacteur (Rectangle arrondi)
    fig.add_shape(type="rect", x0=3, y0=2, x1=7, y1=8, line=dict(color="white", width=2), fillcolor="rgba(255,255,255,0.1)")

    # 2. Les Tuyaux (Lignes)
    fig.add_shape(type="line", x0=1, y0=7, x1=3, y1=7, line=dict(color="white", width=2), name="Inlet") # Entrée
    fig.add_annotation(x=1, y=7, text="Alimentation", showarrow=False, yshift=10, font=dict(color="#aaa", size=10))

    fig.add_shape(type="line", x0=7, y0=3, x1=9, y1=3, line=dict(color="white", width=2), name="Outlet") # Sortie
    fig.add_annotation(x=9, y=3, text="Produit", showarrow=False, yshift=10, font=dict(color="#aaa", size=10))

    # 3. Les LEDs (Scatter points)
    # Positions: Pression (Haut), Temp (Milieu), Débit (Sortie)

    # LED Pression
    fig.add_trace(go.Scatter(
        x=[5], y=[8], mode='markers+text',
        marker=dict(size=25, color=c_p, line=dict(width=2, color='white')),
        text=["<b>P</b>"], textposition="middle center", textfont=dict(color='white'),
        hoverinfo='text', hovertext=f"Pression: {current_p:.1f}"
    ))
    # LED Température
    fig.add_trace(go.Scatter(
        x=[5], y=[5], mode='markers+text',
        marker=dict(size=25, color=c_t, line=dict(width=2, color='white')),
        text=["<b>T</b>"], textposition="middle center", textfont=dict(color='white'),
        hoverinfo='text', hovertext=f"Température: {current_t:.1f}"
    ))
    # LED Débit
    fig.add_trace(go.Scatter(
        x=[8], y=[3], mode='markers+text',
        marker=dict(size=25, color=c_f, line=dict(width=2, color='white')),
        text=["<b>D</b>"], textposition="middle center", textfont=dict(color='white'),
        hoverinfo='text', hovertext=f"Débit: {current_f:.1f}"
    ))

    # Mise en page propre (sans axes)
    fig.update_layout(
        title="Schéma Synoptique (Temps Réel)",
        title_font_size=14,
        width=300, height=250,
        margin=dict(l=10, r=10, t=40, b=10),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(range=[0, 10], showgrid=False, zeroline=False, visible=False),
        yaxis=dict(range=[0, 10], showgrid=False, zeroline=False, visible=False),
        showlegend=False
    )
    return fig

# --- 6. INITIALISATION STATE ---
if 'simulation_running' not in st.session_state: st.session_state.simulation_running = False
if 'final_report' not in st.session_state: st.session_state.final_report = None
if 'final_figs' not in st.session_state: st.session_state.final_figs = None

# Valeurs de base (Moyennes) pour comparer
if 'base_values' not in st.session_state: st.session_state.base_values = {'p': None, 't': None, 'f': None}

# --- 7. MISE EN PAGE ---
st.title("🏭 Monitor the Reactor")

col_left, col_right = st.columns([1, 4])

# === ZONE GAUCHE (CONTROLE) ===
with col_left:
    st.subheader("Contrôle")
    scenario_options = {f"Panne #{i}": i for i in range(1, 21)}
    selected_scenario_name = st.selectbox("Sélectionnez le scénario", list(scenario_options.keys()), disabled=st.session_state.simulation_running)
    selected_fault_code = scenario_options[selected_scenario_name]

    meta = get_fault_info(selected_fault_code)

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("▶️ DÉMARRER", type="primary", use_container_width=True):
            st.session_state.simulation_running = True
            st.session_state.final_report = None
            st.session_state.final_figs = None
            st.session_state.base_values = {'p': None, 't': None, 'f': None} # Reset bases
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

    diff_color = "#28a745" if meta['difficulty'] == "Facile" else "#dc3545" if "Difficile" in meta['difficulty'] else "#ffc107"
    st.markdown(f"""<div style="margin-top:10px; text-align:center;"><span style="background-color:{diff_color}; color:white; padding:4px 10px; border-radius:15px; font-size:0.8em;">Complexité : {meta['difficulty']}</span></div>""", unsafe_allow_html=True)

    st.divider()

    # --- ZONE SYNOPTIQUE (VISUALISATION LIVE) ---
    st.markdown("##### ⚙️ État Réacteur")
    synoptic_spot = st.empty() # Placeholder pour le schéma


# === ZONE DROITE (VISUALISATION) ===
with col_right:
    # Métadonnées
    meta = get_fault_info(selected_fault_code)
    with st.container():
        st.markdown("##### 📋 Profil de performance (Offline)")
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("Description", meta['desc'])
        kpi2.metric("F1-Score", f"{meta['f1']:.2f}")
        kpi3.metric("Précision", f"{meta['accuracy']:.2f}")
        kpi4.info(f"{meta['comment']}")

    st.divider()

    st.markdown("##### 📈 Diagnostic Panne (Vue Globale)")
    chart_main_spot = st.empty()
    st.markdown("##### 📊 Capteurs du réacteur (Temps réel)")
    feat_c1, feat_c2, feat_c3 = st.columns(3)
    chart_feat1 = feat_c1.empty()
    chart_feat2 = feat_c2.empty()
    chart_feat3 = feat_c3.empty()

    # Affichage statique fin de simulation
    if not st.session_state.simulation_running and st.session_state.final_figs:
        chart_main_spot.plotly_chart(st.session_state.final_figs['main'], use_container_width=True)
        chart_feat1.plotly_chart(st.session_state.final_figs['f1'], use_container_width=True)
        chart_feat2.plotly_chart(st.session_state.final_figs['f2'], use_container_width=True)
        chart_feat3.plotly_chart(st.session_state.final_figs['f3'], use_container_width=True)

        # On réaffiche aussi le synoptique figé
        synoptic_spot.plotly_chart(st.session_state.final_figs['synoptic'], use_container_width=True)

    # Rapport Final
    if st.session_state.final_report:
        st.divider()
        st.markdown("### 📝 Rapport de Simulation")
        rep = st.session_state.final_report
        m1, m2, m3 = st.columns(3)
        m1.metric("Scénario", rep['scenario'])
        m2.metric("⏱️ Détection", f"{rep['detection_delay']:.1f} min" if rep['detection_delay'] else "N/A")
        m3.metric("🎯 Diagnostic", f"{rep['diagnosis_delay']:.1f} min" if rep['diagnosis_delay'] else "N/A")


# ==========================
# 8. LOGIQUE D'EXÉCUTION
# ==========================
if st.session_state.simulation_running:

    @st.cache_data(ttl=600)
    def fetch_data_from_api(url):
        try:
            response = requests.get(f"{url}/get-process-data")
            return pd.DataFrame(response.json()) if response.status_code == 200 else pd.DataFrame()
        except Exception: return pd.DataFrame()

    with st.spinner("Chargement..."): df_full = fetch_data_from_api(API_URL)
    if df_full.empty: st.error("Erreur API."); st.session_state.simulation_running = False; st.stop()
    if 'faultNumber' in df_full.columns:
        df_full['faultNumber'] = df_full['faultNumber'].astype(int)
        simulation_data = df_full[df_full['faultNumber'] == selected_fault_code].reset_index(drop=True)
    else: simulation_data = df_full
    if simulation_data.empty: st.error("Aucune donnée."); st.session_state.simulation_running = False; st.stop()

    history_pression, history_temp, history_debit, history_pred, history_time = [], [], [], [], []

    # Pour calculer la moyenne des 10 premiers points (calibration des capteurs)
    init_p, init_t, init_f = [], [], []

    for index, row in simulation_data.iterrows():
        if not st.session_state.simulation_running: break

        val_press = row.get('xmeas_7', 0); val_temp = row.get('xmeas_9', 0); val_debit = row.get('xmeas_10', 0)
        val_sample = row.get('sample', index)
        val_detector = float(row.get('detector', 0)); val_diagnosis = float(row.get('faults_pred', 0))

        current_time_hours = (val_sample * TIME_STEP_MINUTES) / 60
        current_time_minutes = val_sample * TIME_STEP_MINUTES
        display_pred = 0.0 if current_time_hours < 1.0 else val_diagnosis

        # --- CALIBRATION DU RÉACTEUR (5 premiers points) ---
        # On détermine les valeurs "Normales" au tout début
        if index < 5:
            init_p.append(val_press)
            init_t.append(val_temp)
            init_f.append(val_debit)
        elif index == 5:
            st.session_state.base_values['p'] = sum(init_p)/len(init_p)
            st.session_state.base_values['t'] = sum(init_t)/len(init_t)
            st.session_state.base_values['f'] = sum(init_f)/len(init_f)

        # --- LOGIQUE HYBRIDE ---
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

        history_pression.append(val_press); history_temp.append(val_temp); history_debit.append(val_debit)
        history_pred.append(display_pred); history_time.append(current_time_hours)

        # --- UPDATE GRAPHS ---
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
        fig_main.update_layout(title="Type de Panne", height=250, margin=dict(t=30,b=20,l=20,r=20), paper_bgcolor="rgba(0,0,0,0)", template="plotly_dark", xaxis=dict(title="Heures", range=[0, max(1.1, current_time_hours + 0.1)]), yaxis=dict(title="Code Panne", visible=True, automargin=True))
        chart_main_spot.plotly_chart(fig_main, use_container_width=True, key=f"main_{index}")

        # --- UPDATE SYNOPTIQUE (NOUVEAU) ---
        # On passe les valeurs actuelles et les valeurs de base
        # Note : On force l'affichage Vert pendant la première heure (current_time_hours < 1.0)
        # pour éviter que ça clignote pendant la chauffe.
        if current_time_hours < 1.0:
            fig_syn = create_reactor_synoptic(val_press, val_temp, val_debit, None, None, None)
        else:
            fig_syn = create_reactor_synoptic(val_press, val_temp, val_debit,
                                              st.session_state.base_values['p'],
                                              st.session_state.base_values['t'],
                                              st.session_state.base_values['f'])

        synoptic_spot.plotly_chart(fig_syn, use_container_width=True, key=f"syn_{index}")

        time.sleep(0.05)

    if st.session_state.simulation_running:
        d_det, d_diag, det_time_h, diag_time_h = None, None, None, None
        if st.session_state.anomaly_detected:
            d_det = max(0, st.session_state.anomaly_time_min - INJECTION_TIME_MIN)
            det_time_h = st.session_state.anomaly_time_min / 60
        if st.session_state.diagnosis_confirmed:
            d_diag = max(0, st.session_state.diagnosis_time_min - INJECTION_TIME_MIN)
            diag_time_h = st.session_state.diagnosis_time_min / 60

        st.session_state.final_report = {"scenario": selected_scenario_name, "detection_delay": d_det, "diagnosis_delay": d_diag}

        def add_markers_to_fig(fig_to_mark):
            if det_time_h: fig_to_mark.add_vline(x=det_time_h, line_width=2, line_dash="dash", line_color="orange", annotation_text="Détection", annotation_position="top right")
            if diag_time_h:
                pos = "bottom right" if (det_time_h and abs(diag_time_h - det_time_h) < 0.1) else "top right"
                fig_to_mark.add_vline(x=diag_time_h, line_width=2, line_dash="solid", line_color="red", annotation_text="Diagnostic", annotation_position=pos)
            return fig_to_mark

        st.session_state.final_figs = {'main': add_markers_to_fig(fig_main), 'f1': fig1, 'f2': fig2, 'f3': fig3, 'synoptic': fig_syn}
        st.session_state.simulation_running = False
        st.rerun()
