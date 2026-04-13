import streamlit as st
import requests
import io
import time
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from groq import Groq

# --- CONFIGURATION ---
try:
    BACKEND_URL = st.secrets["BACKEND_URL"].strip("/")
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception:
    st.error("Erreur de configuration. Vérifiez vos secrets Streamlit.")
    st.stop()

def create_pdf(text_content):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    text = c.beginText(50, 800)
    text.setFont("Helvetica", 10)
    for line in text_content.split('\n'):
        text.textLine(line[:100])
    c.drawText(text)
    c.showPage()
    c.save()
    return buffer.getvalue()

st.set_page_config(page_title="CitizenOS", page_icon="⚖️")
st.title("CitizenOS ⚖️")

# --- RETOUR PAIEMENT ---
if "session_id" in st.query_params:
    st.success("✅ Paiement validé !")
    try:
        r = requests.get(f"{BACKEND_URL}/get-doc/{st.query_params['session_id']}", timeout=10)
        if r.status_code == 200:
            st.download_button("📥 TÉLÉCHARGER MON DOSSIER", create_pdf(r.json()['content']), "citizenos_dossier.pdf")
    except:
        st.error("Serveur en cours de réveil... Réessayez dans 10 secondes.")

# --- CHAT KAREEM ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.ready = False

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Décrivez votre situation..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        system_msg = """Tu es Kareem de CitizenOS. Pose UNE question précise à la fois. 
        Sois factuel. Après 4-5 questions, résume et termine par : [FIN_DE_DOSSIER]"""
        
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": system_msg}] + st.session_state.messages
        )
        txt = resp.choices[0].message.content
        
        # Détection flexible de la fin du dossier
        if any(tag in txt.upper() for tag in ["FIN_DE_DOSSIER", "FINS_DE_DOSSIER", "DOSSIER PRÊT"]):
            st.session_state.ready = True
            txt = txt.replace("[FIN_DE_DOSSIER]", "").replace("[FINS_DE_DOSSIER]", "")
            txt += "\n\n📌 **Dossier complété. Cliquez sur le bouton ci-dessous pour le générer.**"
        
        st.markdown(txt)
        st.session_state.messages.append({"role": "assistant", "content": txt})
        if st.session_state.ready: st.rerun()

# --- BOUTON STRIPE ---
if st.session_state.ready:
    st.divider()
    if st.button("💳 PAYER ET GÉNÉRER LE PDF (10€)", use_container_width=True):
        try:
            # Envoi du résumé au backend Render
            res = requests.post(f"{BACKEND_URL}/create-checkout", 
                                json={"content": st.session_state.messages[-1]["content"]}, 
                                timeout=15)
            if res.status_code == 200:
                st.link_button("👉 CLIQUEZ ICI POUR RÉGLER", res.json()['url'], type="primary")
            else:
                st.error("Le domaine 'citizen-os-app.streamlit.app' n'est pas encore validé dans Stripe.")
        except:
            st.error("Le backend Render est en veille. Veuillez patienter 30 secondes.")
