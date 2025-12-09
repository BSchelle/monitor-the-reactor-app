import streamlit as st
import requests
import time
import os

st.set_page_config(page_title="Test API", page_icon="🔧")

st.title("🔧 Console de Test API")

# --- CONFIGURATION ---
# Astuce : Pour ne pas modifier le code à chaque fois, on essaie de lire les secrets Streamlit,
# sinon on utilise une valeur par défaut.
# Pour l'instant, remplacez juste la string ci-dessous par votre URL Cloud Run.
DEFAULT_URL = "https://monitor-the-reactor-api-899473705146.europe-west1.run.app"

# Champ texte pour modifier l'URL à la volée si besoin (pratique pour tester local vs distant)
api_url = st.text_input("URL de l'API cible", value=DEFAULT_URL)

# On retire le slash final s'il est présent pour éviter les erreurs "//"
if api_url.endswith("/"):
    api_url = api_url[:-1]

st.divider()

# --- BLOC DE TEST 1 : ROUTE RACINE ---
st.subheader("1. Test de Connexion (Route `/`)")

col1, col2 = st.columns([1, 3])

with col1:
    if st.button("Pinger l'API", type="primary"):
        with col2:
            try:
                start_time = time.time()
                response = requests.get(f"{api_url}/")
                duration = time.time() - start_time

                if response.status_code == 200:
                    data = response.json()
                    st.success(f"✅ Succès ({duration:.2f}s)")
                    # Affiche le message "Bonjour depuis..."
                    st.info(f"Message reçu : **{data.get('message', 'Pas de message')}**")
                    with st.expander("JSON Brut"):
                        st.json(data)
                else:
                    st.error(f"❌ Erreur HTTP {response.status_code}")
                    st.text(response.text)
            except Exception as e:
                st.error(f"❌ Erreur technique : {e}")

st.divider()

# --- BLOC DE TEST 2 : ROUTE HEALTH ---
st.subheader("2. Test de Santé (Route `/health`)")

col_h1, col_h2 = st.columns([1, 3])

with col_h1:
    if st.button("Vérifier Santé"):
        with col_h2:
            try:
                response = requests.get(f"{api_url}/health")

                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "ok":
                        st.success("✅ Statut : OK")
                    else:
                        st.warning(f"⚠️ Réponse inattendue : {data}")
                else:
                    st.error(f"❌ Erreur HTTP {response.status_code}")
            except Exception as e:
                st.error(f"❌ Erreur technique : {e}")

# --- SECTION INFO ---
st.sidebar.markdown("---")
st.sidebar.info(
    """
    **Page de Debug**
    Cette page sert à vérifier que le frontend Streamlit
    arrive bien à discuter avec le backend Cloud Run.
    """
)
