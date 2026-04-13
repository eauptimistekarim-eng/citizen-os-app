import streamlit as st
import requests
import io
import time
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from groq import Groq

# --- CONFIGURATION ---
BACKEND_URL = st.secrets["BACKEND_URL"].strip("/")
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

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

def typewriter(text):
    placeholder = st.empty()
    full_text = ""
    for char in text:
        full_text += char
        placeholder.markdown(full_text + "▌")
        time.sleep(0.02)
    placeholder.markdown(full_text)

# --- INTERFACE ---
st.set_page_config(page_title="CitizenOS", page_icon="⚖️")
st.title("CitizenOS ⚖️")

if "init" not in st.session_state:
    typewriter("Kareem, votre assistant expert pour vos recours et dossiers administratifs.")
    st.session_state.init = True

# --- LOGIQUE DE PAIEMENT ---
if "session_id" in st.query_params:
    st.success("✅ Paiement validé !")
    try:
        r = requests.get(f"{BACKEND_URL}/get-doc/{st.query_params['session_id']}")
        if r.status_code == 200:
            st.download_button("📥 TÉLÉCHARGER LE PDF", create_pdf(r.json()['content']), "dossier.pdf")
    except:
        st.error("Serveur en cours de réveil... réessayez dans 5 secondes.")

# --- CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.ready = False

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Décrivez votre problème (SNCF, Logement, Litige...)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        # LE CERVEAU DE KAREEM
        system_msg = """Tu es Kareem de CitizenOS. 
        Ton but : extraire les infos pour un dossier juridique.
        1. Pose UNE SEULE question précise à la fois.
        2. Sois direct, pas de politesses inutiles.
        3. Après 4-5 questions, résume et termine par : [FIN_DE_DOSSIER]"""
        
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": system_msg}] + st.session_state.messages
        )
        txt = resp.choices[0].message.content
        if "[FIN_DE_DOSSIER]" in txt:
            st.session_state.ready = True
            txt = txt.replace("[FIN_DE_DOSSIER]", "📌 Dossier prêt.")
        
        st.markdown(txt)
        st.session_state.messages.append({"role": "assistant", "content": txt})
        if st.session_state.ready: st.rerun()

# --- BOUTON DE PAIEMENT ---
if st.session_state.ready:
    if st.button("💳 GÉNÉRER MON DOSSIER OFFICIEL (10€)"):
        res = requests.post(f"{BACKEND_URL}/create-checkout", json={"content": st.session_state.messages[-1]["content"]})
        if res.status_code == 200:
            st.link_button("👉 ALLER VERS LE PAIEMENT", res.json()['url'])
        else:
            st.error("Erreur Backend. Vérifiez vos domaines autorisés dans Stripe.")
