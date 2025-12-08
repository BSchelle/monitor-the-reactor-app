import streamlit as st
import time # Nécessaire pour simuler le temps de chargement
#import matplotlib.pyplot as plt
#import matplotlib.image as mpimg

# --- CSS PERSONNALISÉ ---
st.markdown("""
    <style>
    .main { background-color: #0E1117; }    # Dark Mode
    #.stMetric { background-color: #262730; padding: 10px; border-radius: 5px; } Chiffres en rouge
    </style>
    """, unsafe_allow_html=True)

# --- MENU ---
st.sidebar.title("Navigation")
st.sidebar.page_link("app.py", label="Accueil", icon="🏠")
st.sidebar.page_link("pages/page_1.py", label="Secours", icon="1️⃣")

# --- INTERFACE PRINCIPALE ---
st.title("🏭 Monitor the reactor")
st.markdown("Architecture : Détection d'anomalie + Diagnostic")

st.button("Démarrer", type="primary")




# --- 3. CHARGEMENT DES RESSOURCES (Call API) ---


# --- 4. SIDEBAR ---
#st.sidebar.image("https://cdn.brandfetch.io/iduL2MR6Zu/w/820/h/216/theme/dark/logo.png?c=1bxid64Mup7aczewSAYMX&t=1764620774839", width=100)
#st.sidebar.title("🎛️ Contrôle")
#st.sidebar.markdown("---")


#st.sidebar.markdown("---")
#start_btn = st.sidebar.button("▶️ LANCER", type="primary")
#stop_btn = st.sidebar.button("⏹️ ARRÊTER")



# --- 6. BOUCLE DE SIMULATION ---


# --- D. VISUALISATION ---
