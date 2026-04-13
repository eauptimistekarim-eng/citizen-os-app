import streamlit as st
import requests
import stripe
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

# Configuration
BACKEND_URL = st.secrets["BACKEND_URL"]
STRIPE_PUBLIC_KEY = st.secrets["STRIPE_PUBLIC_KEY"]

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

st.set_page_config(page_title="CitizenOS", page_icon="⚖️")
st.title("CitizenOS ⚖️")

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- GESTION DU RETOUR DE PAIEMENT ---
params = st.query_params
if "session_id" in params:
    st.success("✅ Paiement confirmé ! Préparation de votre document...")
    session_id = params["session_id"]
    
    try:
        # On demande le contenu au backend
        res = requests.get(f"{BACKEND_URL}/get-doc/{session_id}")
        if res.status_code == 200:
            doc_data = res.json()
            pdf_bytes = create_pdf(doc_data['content'])
            
            st.download_button(
                label="📥 Télécharger mon document PDF",
                data=pdf_bytes,
                file_name="document_citizenos.pdf",
                mime="application/pdf",
                type="primary"
            )
        else:
            st.warning("⏳ Le document est en cours de finalisation... Veuillez rafraîchir dans 5 secondes.")
    except:
        st.error("Erreur de liaison avec le serveur.")
    st.divider()

# --- INTERFACE CHATBOT ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Posez vos questions ici..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Logique IA (Simulée pour l'exemple, connectez votre Groq ici)
    full_response = f"Analyse terminée pour votre demande : {prompt}\n\nDocument prêt pour certification."
    
    with st.chat_message("assistant"):
        st.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        
        # Le bouton n'apparaît qu'après un certain nombre de messages ou une condition
        if len(st.session_state.messages) >= 2:
            if st.button("💳 Générer et Télécharger le document (10€)"):
                try:
                    r = requests.post(f"{BACKEND_URL}/create-checkout", json={"content": full_response})
                    if r.status_code == 200:
                        st.link_button("Procéder au paiement", r.json()['url'])
                except:
                    st.error("Impossible de joindre le service de paiement.")
