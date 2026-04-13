import streamlit as st
import requests
import io
import time
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from groq import Groq

# --- 1. CONFIGURATION & SECRETS ---
try:
    # URL de votre backend Render (ex: https://citizen-os-backend.onrender.com)
    BACKEND_URL = st.secrets["BACKEND_URL"].strip("/") 
    # Votre nouvelle clé API Groq
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    st.error("Erreur de configuration : Vérifiez vos Secrets Streamlit.")
    st.stop()

# --- 2. FONCTIONS UTILES ---
def create_pdf(text_content):
    """Génère un PDF à partir du résumé final de l'IA."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    text = c.beginText(50, 800)
    text.setFont("Helvetica", 10)
    # Découpage du texte pour éviter les débordements
    lines = text_content.split('\n')
    for line in lines:
        text.textLine(line[:100]) 
    c.drawText(text)
    c.showPage()
    c.save()
    return buffer.getvalue()

def typewriter_effect(text):
    """Affiche le texte avec un effet d'écriture progressive."""
    placeholder = st.empty()
    full_text = ""
    for char in text:
        full_text += char
        placeholder.markdown(full_text + "▌")
        time.sleep(0.02)
    placeholder.markdown(full_text)

# --- 3. INTERFACE UTILISATEUR ---
st.set_page_config(page_title="CitizenOS", page_icon="⚖️")
st.title("CitizenOS ⚖️")

if "intro_done" not in st.session_state:
    typewriter_effect("Je suis Kareem, votre expert CitizenOS. Je vais vous aider à constituer votre dossier juridique.")
    st.session_state.intro_done = True

st.divider()

# --- 4. GESTION DU RETOUR DE PAIEMENT ---
# Vérifie si l'URL contient un session_id après le paiement Stripe
if "session_id" in st.query_params:
    st.success("✅ Paiement validé !")
    sid = st.query_params["session_id"]
    try:
        # Récupération du contenu du document auprès du backend
        r = requests.get(f"{BACKEND_URL}/get-doc/{sid}", timeout=10)
        if r.status_code == 200:
            content = r.json().get('content', "Votre dossier CitizenOS")
            st.download_button(
                label="📥 TÉLÉCHARGER MON DOSSIER (PDF)",
                data=create_pdf(content),
                file_name="dossier_citizenos.pdf",
                mime="application/pdf"
            )
        else:
            st.warning("Dossier en cours de préparation... rafraîchissez la page dans quelques instants.")
    except:
        st.error("Le serveur est momentanément indisponible.")
    st.divider()

# --- 5. LOGIQUE DU CHAT (KAREEM) ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "ready_for_pay" not in st.session_state:
    st.session_state.ready_for_pay = False

# Affichage des messages précédents
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Entrée utilisateur
if prompt := st.chat_input("Décrivez votre problème (SNCF, logement, amende...)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # Consignes strictes pour Kareem (Méthode Freeman)
            system_prompt = """Tu es Kareem, l'IA experte de CitizenOS.
            1. Pose UNE SEULE question précise à la fois pour construire le dossier.
            2. Sois direct et professionnel.
            3. Après 4 à 5 questions, résume la situation et termine EXACTEMENT par : [FIN_DE_DOSSIER]"""

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile", # Modèle à jour
                messages=[{"role": "system", "content": system_prompt}] + st.session_state.messages
            )
            
            full_response = response.choices[0].message.content
            
            if "[FIN_DE_DOSSIER]" in full_response:
                st.session_state.ready_for_pay = True
                full_response = full_response.replace("[FIN_DE_DOSSIER]", "📌 Votre dossier est prêt.")
            
            st.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
            if st.session_state.ready_for_pay:
                st.rerun() # Pour faire apparaître le bouton de paiement immédiatement

        except Exception as e:
            st.error(f"Erreur de communication avec l'IA : {e}")

# --- 6. BOUTON DE PAIEMENT ---
if st.session_state.ready_for_pay:
    st.divider()
    st.subheader("Finaliser mon document")
    if st.button("💳 PAYER ET GÉNÉRER LE PDF (10€)", use_container_width=True):
        with st.spinner("Connexion à Stripe..."):
            try:
                # Envoi du contenu final au backend pour Stripe
                last_summary = st.session_state.messages[-1]["content"]
                res = requests.post(
                    f"{BACKEND_URL}/create-checkout",
                    json={"content": last_summary},
                    timeout=15
                )
                
                if res.status_code == 200:
                    stripe_url = res.json().get('url')
                    st.link_button("👉 CLIQUER ICI POUR PAYER", stripe_url, type="primary")
                else:
                    # Message d'erreur si le domaine n'est pas autorisé dans Stripe
                    st.error("Erreur Backend : Vérifiez que l'URL Streamlit est autorisée dans Stripe.")
            except Exception as e:
                st.error("Le serveur Render met trop de temps à répondre. Réessayez dans 20 secondes.")
