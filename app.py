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
# TITLE
# =====================
st.title("CitizenOS - Assistant Administratif IA")

st.markdown("""
### Assistant intelligent de structuration administrative

Cet outil analyse votre situation (CAF, DALO, préfecture, recours) et vous aide à comprendre vos options.

⚠️ Ceci n’est pas un avocat, mais un outil d’aide à la rédaction et à la compréhension.
""")

# =====================
# SUCCESS PAGE
# =====================
if st.query_params.get("success"):

    st.success("✔ Paiement confirmé")

    session_id = st.query_params.get("session_id")

    if session_id:
        file_url = f"{BACKEND_URL}/download/COURRIER_{session_id}.pdf"
        st.markdown(f"### 📄 Votre document est prêt")
        st.markdown(f"[📥 Télécharger votre lettre]({file_url})")
    else:
        st.warning("Document en cours de génération... rafraîchissez dans quelques secondes")

    st.stop()

# =====================
# IA PROMPT
# =====================
SYSTEM_PROMPT = """
Tu es un assistant administratif expert.

Objectif :
- poser une question à la fois
- reformuler clairement
- guider progressivement
- créer un besoin de document administratif

Style :
- machine à écrire
- court
- précis
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
# CHAT
# =====================
for role, msg in st.session_state.messages:
    with st.chat_message(role):
        st.write(msg)

user_input = st.chat_input("Décrivez votre situation...")

if user_input:
    st.session_state.messages.append(("user", user_input))

    reply = chat(st.session_state.messages)

    st.session_state.messages.append(("assistant", reply))

    if len([m for m in st.session_state.messages if m[0] == "user"]) >= 4:
        st.session_state.unlock = True

    st.rerun()

# =====================
# CONVERSION
# =====================
if st.session_state.unlock:

    st.divider()
    st.subheader("📄 Génération de document")

    st.markdown("""
✔ Lettre administrative personnalisée  
✔ CAF / DALO / Préfecture / Recours  
✔ Format prêt à envoyer  
""")

    if st.button("Générer mon document (9€)"):

        payload = {
            "messages": str(st.session_state.messages)[-500:]
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
