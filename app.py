import streamlit as st
import requests
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from groq import Groq

# Config
BACKEND_URL = st.secrets["BACKEND_URL"]
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def create_pdf(text_content):
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

st.title("CitizenOS ⚖️")

# --- INITIALISATION ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "ready_for_payment" not in st.session_state:
    st.session_state.ready_for_payment = False

# --- GESTION DU RETOUR STRIPE ---
params = st.query_params
if "session_id" in params:
    st.success("✅ Paiement validé !")
    with st.spinner("Récupération du document final..."):
        r = requests.get(f"{BACKEND_URL}/get-doc/{params['session_id']}")
        if r.status_code == 200:
            pdf_bytes = create_pdf(r.json()['content'])
            st.download_button("📥 Télécharger mon PDF Officiel", pdf_bytes, "document.pdf", "application/pdf")
    st.divider()

# --- AFFICHAGE DU CHAT ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- LOGIQUE CHAT IA ---
if prompt := st.chat_input("Répondez ici..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        # Prompt Système pour forcer l'entonnoir
        system_prompt = """Tu es un expert juridique CitizenOS. Ta mission est d'aider l'utilisateur à rédiger un document.
        CONSIGNE : Ne rédige pas le document tout de suite. Pose des questions précises une par une (méthode de l'entonnoir) pour obtenir tous les détails nécessaires.
        Dès que tu as assez d'infos, termine obligatoirement ton message par le mot-clé : [DOCUMENT_PRET] suivi du résumé complet du document."""
        
        full_history = [{"role": "system", "content": system_prompt}] + st.session_state.messages
        
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=full_history
        )
        ai_text = response.choices[0].message.content
        
        # Vérification si le document est prêt
        if "[DOCUMENT_PRET]" in ai_text:
            st.session_state.ready_for_payment = True
            clean_text = ai_text.replace("[DOCUMENT_PRET]", "")
            st.markdown(clean_text)
            st.session_state.messages.append({"role": "assistant", "content": clean_text})
        else:
            st.markdown(ai_text)
            st.session_state.messages.append({"role": "assistant", "content": ai_text})

# --- BOUTON DE PAIEMENT DYNAMIQUE ---
if st.session_state.ready_for_payment:
    st.warning("🎯 Toutes les informations sont réunies. Vous pouvez maintenant générer votre document officiel.")
    if st.button("💳 Payer 10€ et télécharger le PDF"):
        # On envoie le dernier résumé de l'IA au backend
        last_ai_msg = st.session_state.messages[-1]["content"]
        try:
            r = requests.post(f"{BACKEND_URL}/create-checkout", json={"content": last_ai_msg})
            if r.status_code == 200:
                st.link_button("🚀 Accéder au paiement sécurisé", r.json()['url'])
        except:
            st.error("Lien avec le serveur Stripe impossible.")
