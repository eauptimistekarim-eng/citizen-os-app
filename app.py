import streamlit as st
import requests
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="CitizenOS", page_icon="⚖️")

# =====================
# TITLE
# =====================
st.title("CitizenOS - Analyse Administrative IA")

st.markdown("""
### Assistant d’analyse et de structuration administrative

Cet outil aide à comprendre une situation administrative complexe et à générer un document adapté.

Il ne remplace pas un professionnel du droit.
""")

# =====================
# SUCCESS PAGE
# =====================
if "success" in st.query_params:

    st.success("Paiement confirmé ✔")

    st.subheader("Votre document est prêt")

    backend_file = "http://127.0.0.1:5001/download/COURRIER_client_email.pdf"

    st.info("Téléchargement en cours...")

    st.markdown(f"""
    <meta http-equiv="refresh" content="2;url={backend_file}">
    """, unsafe_allow_html=True)

    st.markdown(f"[📥 Télécharger manuellement]({backend_file})")

    st.stop()


# =====================
# GROQ
# =====================
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


SYSTEM_PROMPT = """
Tu es un assistant administratif expert.

OBJECTIF :
- comprendre la situation progressivement
- poser une question à la fois
- reformuler
- guider vers une analyse claire
- préparer vers génération de document

STYLE :
- court
- professionnel
- structuré
- machine à écrire

NE DONNE PAS TOUT TROP VITE.
"""


def chat(messages):

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            *[{"role": r, "content": m} for r, m in messages]
        ],
        temperature=0.3
    )

    return completion.choices[0].message.content


# =====================
# STATE
# =====================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "unlock" not in st.session_state:
    st.session_state.unlock = False


# =====================
# CHAT DISPLAY
# =====================
for r, m in st.session_state.messages:
    with st.chat_message(r):
        st.write(m)


# =====================
# INPUT
# =====================
user_input = st.chat_input("Décrivez votre situation...")

if user_input:
    st.session_state.messages.append(("user", user_input))

    reply = chat(st.session_state.messages)

    st.session_state.messages.append(("assistant", reply))

    if len([m for m in st.session_state.messages if m[0] == "user"]) >= 4:
        st.session_state.unlock = True

    st.rerun()


# =====================
# CONVERSION BLOCK
# =====================
if st.session_state.unlock:

    st.divider()
    st.subheader("📄 Analyse complète disponible")

    st.markdown("""
Votre situation a été analysée.

Une lettre administrative personnalisée peut être générée immédiatement :
- prête à envoyer
- adaptée à votre cas
- format officiel
""")

    if st.button("Générer mon document (9€)"):

        res = requests.post(
            "http://127.0.0.1:5001/create-checkout-session",
            json={"situation": st.session_state.messages[-1][1]}
        )

        data = res.json()

        if "url" in data:
            st.markdown(f"[👉 Accéder au paiement]({data['url']})")
        else:
            st.error(data)