import streamlit as st
import requests
import io
import time
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from groq import Groq

# --- 1. CONFIGURATION & SECRETS ---
# Assure-toi que ces clés sont bien dans tes secrets Streamlit
try:
    BACKEND_URL = st.secrets["BACKEND_URL"].strip("/")
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    st.error("Erreur de configuration : Vérifiez vos Secrets Streamlit.")
    st.stop()

# --- 2. FONCTIONS UTILES ---
def create_pdf(text_content):
    """Génère un PDF simple à partir du texte de l'IA."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    text = c.beginText(50, 800)
    text.setFont("Helvetica", 10)
    # Découpage du texte pour éviter qu'il ne dépasse du PDF
    lines = text_content.split('\n')
    for line in lines:
        text.textLine(line[:100]) 
    c.drawText(text)
    c.showPage()
    c.save()
    return buffer.getvalue()

def typewriter_effect(text):
    """Effet d'écriture pour l'introduction."""
    placeholder = st.empty()
    full_text = ""
    for char in text:
        full_text += char
        placeholder.markdown(full_text + "▌")
        time.sleep(0.02)
    placeholder.markdown(full_text)

# --- 3. INTERFACE UTILISATEUR ---
st.set_page_config(page_title="CitizenOS", page_icon="⚖️", layout="centered")
st.title("CitizenOS ⚖️")

if "intro_done" not in st.session_state:
    typewriter_effect("Je suis Kareem, votre expert CitizenOS. Décrivez-moi votre situation pour constituer votre dossier juridique.")
    st.session_state.intro_done = True
else:
    st.markdown("*Kareem est à votre écoute pour vos recours et dossiers officiels.*")

st.divider()

# --- 4. GESTION DU RETOUR DE PAIEMENT ---
if "session_id" in st.query_params:
    st.success("✅ Paiement validé avec succès !")
    sid = st.query_params["session_id"]
    with st.status("Récupération de votre dossier...", expanded=True) as status:
        try:
            r = requests.get(f"{BACKEND_URL}/get-doc/{sid}", timeout=10)
            if r.status_code == 200:
                content = r.json().get('content', "Dossier CitizenOS")
                pdf_bytes = create_pdf(content)
                st.download_button(
                    label="📥 TÉLÉCHARGER MON DOSSIER (PDF)",
                    data=pdf_bytes,
                    file_name="dossier_citizenos.pdf",
                    mime="application/pdf"
                )
                status.update(label="Dossier prêt !", state="complete")
            else:
                st.warning("Le document est encore en cours de traitement... Rafraîchissez la page.")
        except:
            st.error("Connexion au serveur interrompue. Veuillez patienter.")
    st.divider()

# --- 5. LOGIQUE DU CHAT (KAREEM) ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "ready_for_pay" not in st.session_state:
    st.session_state.ready_for_pay = False

# Affichage de l'historique
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Entrée utilisateur
if prompt := st.chat_input("Ex: Problème de logement, amende SNCF..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # Système de questions en entonnoir (Freeman Method)
            system_prompt = """Tu es Kareem, l'IA experte de CitizenOS. 
            Ton but est de collecter les informations pour un dossier juridique officiel.
            1. Pose UNE SEULE question précise à la fois.
            2. Ne fais pas de politesses inutiles, sois factuel et professionnel.
            3. Tu dois poser environ 4 à 5 questions pour bien comprendre le litige.
            4. Quand tu as toutes les informations, fais un résumé structuré et termine EXACTEMENT par le code : [FIN_DE_DOSSIER]"""

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": system_prompt}] + st.session_state.messages
            )
            
            full_response = response.choices[0].message.content
            
            if "[FIN_DE_DOSSIER]" in full_response:
                st.session_state.ready_for_pay = True
                full_response = full_response.replace("[FIN_DE_DOSSIER]", "")
                st.markdown(full_response)
                st.info("🎯 **Analyse terminée. Votre dossier est prêt à être généré.**")
            else:
                st.markdown(full_response)
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
            # Forcer le rafraîchissement pour afficher le bouton de paiement
            if st.session_state.ready_for_pay:
                st.rerun()

        except Exception as e:
            st.error(f"Erreur technique : {e}")

# --- 6. BOUTON DE PAIEMENT STRIPE ---
if st.session_state.ready_for_pay:
    st.divider()
    st.subheader("Finaliser mon document")
    if st.button("💳 PAYER ET GÉNÉRER LE PDF (10€)", use_container_width=True):
        with st.spinner("Connexion sécurisée à Stripe..."):
            try:
                # On envoie le dernier résumé de Kareem au backend Render
                last_ai_message = st.session_state.messages[-1]["content"]
                
                res = requests.post(
                    f"{BACKEND_URL}/create-checkout",
                    json={"content": last_ai_message},
                    timeout=15
                )
                
                if res.status_code == 200:
                    checkout_url = res.json().get('url')
                    st.link_button("👉 CLIQUER ICI POUR RÉGLER", checkout_url, type="primary")
                else:
                    st.error("Erreur Backend : Vérifiez que l'URL Streamlit est autorisée dans votre Dashboard Stripe.")
            except Exception as e:
                st.error("Le serveur Render est en veille (Sleep mode). Veuillez patienter 30 secondes et cliquer à nouveau.")
