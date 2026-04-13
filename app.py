import streamlit as st
import requests
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

# Configuration
BACKEND_URL = st.secrets["BACKEND_URL"]
STRIPE_PUBLIC_KEY = st.secrets["STRIPE_PUBLIC_KEY"]

def generate_pdf(content):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    text_obj = c.beginText(50, 800)
    text_obj.setFont("Helvetica", 11)
    
    # Gestion simple des retours à la ligne
    lines = content.split('\n')
    for line in lines:
        if text_obj.getY() < 50: # Nouvelle page si bas de page
            c.drawText(text_obj)
            c.showPage()
            text_obj = c.beginText(50, 800)
            text_obj.setFont("Helvetica", 11)
        text_obj.textLine(line)
        
    c.drawText(text_obj)
    c.showPage()
    c.save()
    return buffer.getvalue()

st.set_page_config(page_title="CitizenOS", layout="centered")
st.title("📄 CitizenOS")

# --- LOGIQUE DE RÉCUPÉRATION APRÈS PAIEMENT ---
query_params = st.query_params
if "status" in query_params and query_params["status"] == "success":
    session_id = query_params.get("session_id")
    st.balloons()
    st.success("Félicitations ! Votre paiement a été confirmé.")
    
    with st.spinner("Récupération de votre document sécurisé..."):
        try:
            response = requests.get(f"{BACKEND_URL}/get_content/{session_id}")
            if response.status_code == 200:
                doc_text = response.json().get("content")
                pdf_file = generate_pdf(doc_text)
                
                st.download_button(
                    label="📥 Télécharger mon document (PDF)",
                    data=pdf_file,
                    file_name="citizenos_document.pdf",
                    mime="application/pdf",
                    type="primary"
                )
                st.info("Ce lien est temporaire. Veuillez télécharger votre fichier maintenant.")
            else:
                st.error("Délai expiré ou document introuvable. Contactez le support.")
        except Exception:
            st.error("Le serveur est momentanément indisponible.")
    st.divider()

# --- INTERFACE CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ex: Rédige une lettre de contestation..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        # Ici l'appel Groq (simulé pour la structure)
        ai_content = f"DOCUMENT GÉNÉRÉ POUR : {prompt}\n\nCeci est le corps de votre document officiel.\nCitizenOS certifie la génération de ce texte.\n\n[Fin du document]"
        st.markdown(ai_content)
        st.session_state.messages.append({"role": "assistant", "content": ai_content})
        
        # Bouton déclencheur vers le Backend
        if st.button("Obtenir le PDF officiel (10€)"):
            try:
                res = requests.post(f"{BACKEND_URL}/create-checkout-session", json={"content": ai_content})
                if res.status_code == 200:
                    st.link_button("🚀 Passer au paiement", res.json()["url"])
                else:
                    st.error("Erreur technique côté serveur.")
            except:
                st.error("Connexion au backend impossible.")
