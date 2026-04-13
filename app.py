import streamlit as st
import requests
import io
import time
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from groq import Groq

# --- CONFIG ---
BACKEND_URL = st.secrets["BACKEND_URL"].strip("/") # On enlève les slashs de trop
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def create_pdf(text_content):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    text = c.beginText(50, 800)
    text.setFont("Helvetica", 10)
    # On découpe le texte pour qu'il ne dépasse pas du PDF
    lines = text_content.split('\n')
    for line in lines:
        text.textLine(line[:100]) 
    c.drawText(text)
    c.showPage()
    c.save()
    return buffer.getvalue()

st.set_page_config(page_title="CitizenOS", page_icon="⚖️")
st.title("CitizenOS ⚖️")

# --- RETOUR DE PAIEMENT ---
if "session_id" in st.query_params:
    st.success("✅ Paiement Test réussi !")
    sid = st.query_params["session_id"]
    try:
        r = requests.get(f"{BACKEND_URL}/get-doc/{sid}", timeout=10)
        if r.status_code == 200:
            pdf_bytes = create_pdf(r.json()['content'])
            st.download_button("📥 TÉLÉCHARGER MON PDF", pdf_bytes, "document.pdf", "application/pdf")
        else:
            st.error("Document en cours de préparation... rafraîchissez dans 5 secondes.")
    except:
        st.error("Le serveur Render met du temps à répondre. Réessayez.")
    st.divider()

# --- CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.ready = False

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Votre réponse..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # On donne une consigne ultra-stricte à l'IA
            resp = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "Tu es CitizenOS. Pose UNE question à la fois. NE DIS JAMAIS '[PROCHAINES_ÉTAPES]'. Quand tu as fini, écris exactement : [FIN_DE_DOSSIER]"},
                    *st.session_state.messages
                ]
            )
            txt = resp.choices[0].message.content
            
            if "[FIN_DE_DOSSIER]" in txt:
                st.session_state.ready = True
                txt = txt.replace("[FIN_DE_DOSSIER]", "📌 Votre dossier est complet.")
            
            st.markdown(txt)
            st.session_state.messages.append({"role": "assistant", "content": txt})
            if st.session_state.ready: st.rerun()
        except Exception as e:
            st.error(f"Erreur Groq : {e}")

# --- LE BOUTON DE PAIEMENT ---
if st.session_state.ready:
    st.info("🎯 Tout est prêt.")
    if st.button("💳 GÉNÉRER LE PDF (STRIPE TEST)"):
        with st.spinner("Connexion à Stripe..."):
            try:
                # On prend le résumé de l'IA (le dernier message)
                last_ai_text = st.session_state.messages[-1]["content"]
                payload = {"content": last_ai_text}
                res = requests.post(f"{BACKEND_URL}/create-checkout", json=payload, timeout=15)
                
                if res.status_code == 200:
                    stripe_url = res.json().get('url')
                    st.link_button("👉 CLIQUER ICI POUR PAYER (TEST)", stripe_url)
                else:
                    st.error(f"Erreur Backend : {res.status_code}")
            except Exception as e:
                st.error(f"Le serveur Render est endormi : {e}")
