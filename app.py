import streamlit as st
import requests
from groq import Groq

# =====================
# CONFIG
# =====================
st.set_page_config(page_title="CitizenOS", page_icon="⚖️")

BACKEND_URL = st.secrets["BACKEND_URL"]

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# =====================
# TITRE + POSITIONNEMENT
# =====================
st.title("CitizenOS - Assistant Administratif IA")

st.markdown("""
### Analyse intelligente de situations administratives

Cet outil vous aide à structurer une situation (CAF, DALO, préfecture, recours…).

⚠️ Ce n’est pas un avocat, mais une aide à la compréhension et à la rédaction.
""")

# =====================
# SUCCESS PAGE
# =====================
if st.query_params.get("success"):

    st.success("✔ Paiement confirmé")

    st.subheader("📄 Votre document est prêt")

    session_id = st.query_params.get("email", "client")

    file_url = f"{BACKEND_URL}/download/COURRIER_{session_id}.pdf"

    st.info("Téléchargement en cours...")

    st.markdown(f"[📥 Télécharger le document]({file_url})")

    st.stop()

# =====================
# IA PROMPT
# =====================
SYSTEM_PROMPT = """
Tu es un assistant administratif expert.

Tu dois :
- poser une question à la fois
- reformuler la situation
- guider progressivement
- créer un besoin de document
- garder un style court, précis, type machine à écrire
"""

def chat(messages):
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": SYSTEM_PROMPT}] +
                 [{"role": r, "content": m} for r, m in messages],
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
for role, msg in st.session_state.messages:
    with st.chat_message(role):
        st.write(msg)

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
👉 Génération d’une lettre administrative personnalisée :

- CAF
- DALO
- Préfecture
- Recours officiel

⏱ instantané
💰 9€
""")

    if st.button("Générer mon document (9€)"):

        payload = {
            "situation": str(st.session_state.messages)[-400:]
        }

        res = requests.post(
            f"{BACKEND_URL}/create-checkout-session",
            json=payload
        )

        data = res.json()

        if "url" in data:
            st.markdown(f"[👉 Payer maintenant]({data['url']})")
        else:
            st.error(data)
