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
    st.error("Erreur : Vérifiez vos Secrets Streamlit (BACKEND_URL et GROQ_API_KEY).")
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

# --- GESTION DU RETOUR DE PAIEMENT ---
if "session_id" in st.query_params:
    st.success("✅ Paiement validé !")
    try:
        r = requests.get(f"{BACKEND_URL}/get-doc/{st.query_params['session_id']}", timeout=15)
        if r.status_code == 200:
            st.download_button("📥 TÉLÉCHARGER MON DOSSIER", create_pdf(r.json()['content']), "citizenos_dossier.pdf")
    except:
        st.info("Le serveur prépare votre fichier... Patientez 10 secondes et rafraîchissez.")

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
        system_msg = "Tu es Kareem de CitizenOS. Pose une question à la fois. Après 4 questions, résume et termine par : [FIN_DE_DOSSIER]"
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": system_msg}] + st.session_state.messages
        )
        txt = resp.choices[0].message.content
        
        # Détection du signal de fin (plus robuste)
        if "[FIN_DE_DOSSIER]" in txt or "FIN_DE_DOSSIER" in txt.upper():
            st.session_state.ready = True
            txt = txt.replace("[FIN_DE_DOSSIER]", "").replace("FIN_DE_DOSSIER", "")
            txt += "\n\n📌 **Dossier prêt. Cliquez ci-dessous pour finaliser.**"
        
        st.markdown(txt)
        st.session_state.messages.append({"role": "assistant", "content": txt})
        if st.session_state.ready: st.rerun()

# --- BOUTON DE PAIEMENT (Gère le réveil du serveur) ---
if st.session_state.ready:
    st.divider()
    if st.button("💳 PAYER ET GÉNÉRER LE PDF (10€)", use_container_width=True):
        with st.spinner("Réveil du serveur sécurisé (peut prendre 30s)..."):
            try:
                res = requests.post(
                    f"{BACKEND_URL}/create-checkout", 
                    json={"content": st.session_state.messages[-1]["content"]}, 
                    timeout=30 # Temps long pour laisser Render démarrer
                )
                if res.status_code == 200:
                    st.link_button("👉 PROCÉDER AU PAIEMENT", res.json()['url'], type="primary")
                else:
                    st.error("Erreur Stripe : Domaine non autorisé ou clé invalide.")
            except requests.exceptions.Timeout:
                st.error("Le serveur est encore en train de démarrer. Réessayez dans 10 secondes.")
            except Exception:
                st.error("Connexion impossible. Vérifiez l'URL de votre backend.")
