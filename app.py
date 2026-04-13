import streamlit as st
import requests
import stripe
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

# Config
BACKEND_URL = st.secrets["BACKEND_URL"]
STRIPE_PUBLIC_KEY = st.secrets["STRIPE_PUBLIC_KEY"]

def generate_pdf(content):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    text_obj = c.beginText(50, 800)
    text_obj.setFont("Helvetica", 12)
    
    # Simple line wrapping
    for line in content.split('\n'):
        text_obj.textLine(line)
        
    c.drawText(text_obj)
    c.showPage()
    c.save()
    return buffer.getvalue()

st.set_page_config(page_title="CitizenOS", page_icon="📄")
st.title("CitizenOS 📄")

# Initialisation
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_doc" not in st.session_state:
    st.session_state.last_doc = ""

# Gestion du retour de paiement
params = st.query_params
if "status" in params and params["status"] == "success":
    st.success("✅ Paiement validé !")
    
    # On récupère le contenu via le backend pour éviter les limites metadata
    session_id = params.get("session_id")
    if session_id:
        with st.spinner("Préparation de votre document..."):
            try:
                resp = requests.get(f"{BACKEND_URL}/get_content/{session_id}")
                if resp.status_code == 200:
                    data = resp.json()
                    pdf_bytes = generate_pdf(data['content'])
                    
                    st.download_button(
                        label="📥 Télécharger mon PDF",
                        data=pdf_bytes,
                        file_name="citizenos_document.pdf",
                        mime="application/pdf",
                        type="primary"
                    )
                else:
                    st.error("Document introuvable ou session expirée.")
            except:
                st.error("Erreur de connexion au serveur.")
    st.divider()

# Chatbot Interface
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Décrivez votre document..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # Ici, intégrez votre appel Groq réel. Exemple simulé :
        response = f"Voici l'analyse pour votre demande : {prompt}\n\nCe document est prêt à être certifié et téléchargé après paiement."
        st.markdown(response)
        st.session_state.last_doc = response
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        if st.button("💳 Générer le PDF (10€)"):
            payload = {"content": st.session_state.last_doc}
            try:
                res = requests.post(f"{BACKEND_URL}/create-checkout-session", json=payload)
                if res.status_code == 200:
                    url = res.json().get("url")
                    st.link_button("Aller vers le paiement sécurisé", url)
                else:
                    st.error("Erreur lors de la création de la session.")
            except:
                st.error("Serveur indisponible.")
