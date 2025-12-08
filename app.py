import streamlit as st
import pandas as pd
import numpy as np
import joblib
import time
import plotly.graph_objects as go
import plotly.express as px
import tensorflow as tf  # Indispensable pour l'Autoencoder

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Monitor the reactor",
    page_icon="🏭",
    layout="wide"
)

# --- 2. CSS PERSONNALISÉ ---
st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    .stMetric { background-color: #262730; padding: 10px; border-radius: 5px; }
    div.block-container { padding-top: 2rem; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CHARGEMENT DES RESSOURCES (Call API) ---



# --- 4. SIDEBAR ---
st.sidebar.image("https://cdn.brandfetch.io/iduL2MR6Zu/w/820/h/216/theme/dark/logo.png?c=1bxid64Mup7aczewSAYMX&t=1764620774839", width=100)
st.sidebar.title("🎛️ Contrôle")
st.sidebar.markdown("---")


st.sidebar.markdown("---")
start_btn = st.sidebar.button("▶️ LANCER", type="primary")
stop_btn = st.sidebar.button("⏹️ ARRÊTER")

# --- 5. INTERFACE PRINCIPALE ---
st.title("🏭 Monitor the reactor")
st.markdown("Architecture : Détection d'anomalie + Diagnostic")


# --- 6. BOUCLE DE SIMULATION ---


        # --- D. VISUALISATION ---

time.sleep()
