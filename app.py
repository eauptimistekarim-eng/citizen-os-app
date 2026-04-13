import streamlit as st
import requests
import io
import time
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from groq import Groq

# --- CONFIGURATION ---
BACKEND_URL = st.secrets["BACKEND_URL"]
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
client = Groq(api_key=GROQ_API_KEY)

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

def typewriter_effect(text, delay=0.02):
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

if "intro_done" not in st.session_state:
    typewriter_effect("Votre assistant juridique intelligent pour la rédaction de documents officiels.")
    st.session_state.intro_done = True
else:
    st.markdown("Votre assistant juridique intelligent pour la rédaction de documents officiels.")

st.divider()

# --- INITIALISATION ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "ready_for_payment" not in st.session_state:
    st.session_state.ready_for_payment = False

# --- RETOUR DE PAIEMENT ---
params = st.query_params
if "session_id" in params:
    st.success("✅ Paiement test validé !")
    try:
        r = requests.get(f"{BACKEND_URL}/get-doc/{params['session_id']}")
        if r.status_code == 200:
            pdf_data = create_pdf(r.json()['content'])
            st.download_button("📥 Télécharger mon PDF", pdf_data, "document.pdf", "application/pdf")
    except Exception as e:
        st.error(f"Erreur : {e}")

# --- AFFICHAGE CHAT ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- CHATBOT ---
if prompt := st.chat_input("Décrivez votre situation..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # MISE À JOUR DU MODÈLE ICI
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile", 
                messages=[
                    {"role": "system", "content": "Pose une question à la fois (entonnoir). Termine par [DOSSIER_COMPLET] quand tu as tout."},
                    *st.session_state.messages
                ]
            )
            ai_response = response.choices[0].message.content
            
            if "[DOSSIER_COMPLET]" in ai_response:
                st.session_state.ready_for_payment = True
                ai_response = ai_response.replace("[DOSSIER_COMPLET]", "")
            
            st.markdown(ai_response)
            st.session_state.messages.append({"role": "assistant", "content": ai_response})
            if st.session_state.ready_for_payment: st.rerun()
        except Exception as e:
            st.error(f"Erreur : {e}")

# --- BOUTON PAIEMENT ---
if st.session_state.ready_for_payment:
    if st.button("💳 Générer le PDF (Mode Test)"):
        last_content = st.session_state.messages[-1]["content"]
        res = requests.post(f"{BACKEND_URL}/create-checkout", json={"content": last_content})
        if res.status_code == 200:
            st.link_button("Aller vers Stripe Test", res.json()['url'])
