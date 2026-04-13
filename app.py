import streamlit as st
import requests
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

# Variables de config
BACKEND_URL = st.secrets["BACKEND_URL"]

def create_pdf(text_content):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    text = c.beginText(50, 800)
    text.setFont("Helvetica", 12)
    # Découpage simple pour le PDF
    for line in text_content.split('\n'):
        text.textLine(line)
    c.drawText(text)
    c.showPage()
    c.save()
    return buffer.getvalue()

st.set_page_config(page_title="CitizenOS", page_icon="⚖️")
st.title("CitizenOS ⚖️")

# 1. Vérification du retour de paiement
params = st.query_params
if "session_id" in params:
    session_id = params["session_id"]
    st.success("✅ Paiement validé !")
    with st.spinner("Génération du PDF..."):
        r = requests.get(f"{BACKEND_URL}/get-doc/{session_id}")
        if r.status_code == 200:
            pdf_data = create_pdf(r.json()['content'])
            st.download_button("📥 Télécharger mon document PDF", pdf_data, "document_citizenos.pdf", "application/pdf")
    st.divider()

# 2. Chatbot
if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("Posez vos questions ici..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    # Réponse simulée (Connectez votre Groq ici)
    ai_res = f"Analyse terminée pour : {prompt}\n\nDocument prêt pour certification."
    with st.chat_message("assistant"):
        st.markdown(ai_res)
        st.session_state.messages.append({"role": "assistant", "content": ai_res})
        
        # Le bouton de paiement apparaît sous le dernier message
        if st.button("💳 Acheter le document PDF (10€)"):
            res = requests.post(f"{BACKEND_URL}/create-checkout", json={"content": ai_res})
            if res.status_code == 200:
                st.link_button("🚀 Accéder au paiement sécurisé", res.json()['url'])
