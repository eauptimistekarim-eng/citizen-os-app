import streamlit as st
import requests
import io
import time
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from groq import Groq

# --- CONFIGURATION ---
# On récupère les secrets configurés dans l'interface Streamlit Cloud
BACKEND_URL = st.secrets["BACKEND_URL"]
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
client = Groq(api_key=GROQ_API_KEY)

def create_pdf(text_content):
    """Génère un fichier PDF à partir du texte fourni."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    text = c.beginText(50, 800)
    text.setFont("Helvetica", 12)
    for line in text_content.split('\n'):
        text.textLine(line)
    c.drawText(text)
    c.showPage()
    c.save()
    return buffer.getvalue()

def typewriter_effect(text, delay=0.02):
    """Affiche un texte avec un effet machine à écrire."""
    placeholder = st.empty()
    full_text = ""
    for char in text:
        full_text += char
        placeholder.markdown(full_text + "▌")
        time.sleep(delay)
    placeholder.markdown(full_text)

# --- MISE EN PAGE ---
st.set_page_config(page_title="CitizenOS", page_icon="⚖️")
st.title("CitizenOS ⚖️")

# Présentation en mode machine à écrire
intro_text = "Votre assistant juridique intelligent pour la rédaction de documents officiels et la résolution de litiges."
typewriter_effect(intro_text)
st.divider()

# --- INITIALISATION ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "ready_for_payment" not in st.session_state:
    st.session_state.ready_for_payment = False

# --- GESTION DU RETOUR DE PAIEMENT STRIPE ---
# Si un session_id est présent dans l'URL, le paiement a réussi
params = st.query_params
if "session_id" in params:
    st.success("✅ Paiement validé ! Votre document est prêt.")
    with st.spinner("Récupération du contenu final..."):
        try:
            r = requests.get(f"{BACKEND_URL}/get-doc/{params['session_id']}")
            if r.status_code == 200:
                pdf_data = create_pdf(r.json()['content'])
                st.download_button(
                    label="📥 Télécharger mon document PDF",
                    data=pdf_data,
                    file_name="document_citizenos.pdf",
                    mime="application/pdf"
                )
            else:
                st.error("Document introuvable sur le serveur.")
        except Exception as e:
            st.error(f"Erreur de connexion : {e}")
    st.divider()

# --- AFFICHAGE DE L'HISTORIQUE ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- CHATBOT (LOGIQUE D'ENTONNOIR) ---
if prompt := st.chat_input("Décrivez votre situation ici..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # Prompt système pour forcer l'IA à poser des questions
            system_instruction = """Tu es l'expert CitizenOS. 
            Étape 1 : Pose des questions courtes et pertinentes une par une (entonnoir).
            Étape 2 : Ne rédige pas le document final avant d'avoir tous les détails.
            Étape 3 : Quand tu as tout, termine impérativement par : [DOSSIER_COMPLET] suivi du résumé."""
            
            messages_history = [{"role": "system", "content": system_instruction}] + st.session_state.messages
            
            response = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=messages_history
            )
            ai_response = response.choices[0].message.content
            
            if "[DOSSIER_COMPLET]" in ai_response:
                st.session_state.ready_for_payment = True
                ai_response = ai_response.replace("[DOSSIER_COMPLET]", "✅ Informations recueillies.")
            
            st.markdown(ai_response)
            st.session_state.messages.append({"role": "assistant", "content": ai_response})
            
        except Exception as e:
            st.error(f"Erreur Groq (Quota ou Clé) : {e}")

# --- BOUTON DE PAIEMENT DYNAMIQUE ---
if st.session_state.ready_for_payment:
    st.warning("🎯 L'IA a toutes les informations nécessaires.")
    if st.button("💳 Payer 10€ pour générer le PDF officiel"):
        # On envoie le dernier résumé de l'IA pour la mise en PDF
        last_content = st.session_state.messages[-1]["content"]
        try:
            res = requests.post(f"{BACKEND_URL}/create-checkout", json={"content": last_content})
            if res.status_code == 200:
                st.link_button("🚀 Accéder au paiement sécurisé Stripe", res.json()['url'])
        except:
            st.error("Lien avec le serveur Render impossible.")
