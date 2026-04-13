import streamlit as st
import requests
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from groq import Groq

# --- CONFIGURATION ---
# Assurez-vous que ces noms correspondent EXACTEMENT à vos secrets Streamlit
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

st.set_page_config(page_title="CitizenOS", page_icon="⚖️")
st.title("CitizenOS ⚖️")

# --- INITIALISATION ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "ready_for_payment" not in st.session_state:
    st.session_state.ready_for_payment = False

# --- GESTION DU RETOUR DE PAIEMENT ---
params = st.query_params
if "session_id" in params:
    st.success("✅ Paiement confirmé ! Préparation de votre document...")
    try:
        r = requests.get(f"{BACKEND_URL}/get-doc/{params['session_id']}")
        if r.status_code == 200:
            pdf_bytes = create_pdf(r.json()['content'])
            st.download_button(
                label="📥 Télécharger mon document officiel (PDF)",
                data=pdf_bytes,
                file_name="document_citizenos.pdf",
                mime="application/pdf"
            )
        else:
            st.error("Erreur : Document introuvable. Veuillez réessayer.")
    except Exception as e:
        st.error(f"Erreur de connexion au backend : {e}")
    st.divider()

# --- AFFICHAGE DU CHAT ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- LOGIQUE CHAT IA (ENTONNOIR) ---
if prompt := st.chat_input("Répondez ici..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # Le prompt système force l'IA à poser des questions d'abord
        system_prompt = """Tu es l'assistant juridique de CitizenOS. 
        TON BUT : Aider l'utilisateur à constituer un dossier ou une lettre.
        MÉTHODE : Ne rédige pas le document final immédiatement. Pose des questions précises, une par une, pour comprendre le litige ou la demande (entonnoir).
        QUAND TU AS TOUT : Une fois que tu as assez d'infos, résume la situation et termine impérativement ton message par le code : [PRET_POUR_CERTIFICATION]"""
        
        history = [{"role": "system", "content": system_prompt}] + st.session_state.messages
        
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=history
        )
        ai_text = response.choices[0].message.content
        
        if "[PRET_POUR_CERTIFICATION]" in ai_text:
            st.session_state.ready_for_payment = True
            display_text = ai_text.replace("[PRET_POUR_CERTIFICATION]", "✅ Dossier complet.")
            st.markdown(display_text)
            st.session_state.messages.append({"role": "assistant", "content": display_text})
        else:
            st.markdown(ai_text)
            st.session_state.messages.append({"role": "assistant", "content": ai_text})

# --- BOUTON DE PAIEMENT ---
if st.session_state.ready_for_payment:
    st.info("🎯 Votre document est prêt à être généré.")
    if st.button("💳 Payer 10€ et générer le PDF"):
        # On envoie le contenu du dernier message de l'IA pour le PDF
        content_to_save = st.session_state.messages[-1]["content"]
        try:
            r = requests.post(f"{BACKEND_URL}/create-checkout", json={"content": content_to_save})
            if r.status_code == 200:
                st.link_button("🚀 Aller vers le paiement sécurisé", r.json()['url'])
            else:
                st.error("Erreur lors de la création de la session de paiement.")
        except:
            st.error("Backend injoignable.")
