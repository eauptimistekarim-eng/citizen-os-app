import streamlit as st
import requests
from groq import Groq

# =====================
# CONFIG
# =====================
st.set_page_config(page_title="CitizenOS", page_icon="⚖️")

BACKEND_URL = st.secrets["BACKEND_URL"]
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

st.title("CitizenOS - Assistant Administratif IA")

st.markdown("""
### Assistant administratif intelligent
CAF • DALO • Préfecture • Recours

⚠️ Outil d’aide à la compréhension, pas un avocat.
""")

# =====================
# SUCCESS PAGE
# =====================
if st.query_params.get("success"):

    session_id = st.query_params.get("session_id")

    st.success("✔ Paiement confirmé")

    if session_id:
        st.markdown("### 📄 Votre document est prêt")

        file_url = f"{BACKEND_URL}/download/{session_id}"
        st.markdown(f"[📥 Télécharger votre lettre]({file_url})")

    st.stop()

# =====================
# STATE
# =====================
if "messages" not in st.session_state:
    st.session_state.messages = []

# =====================
# CHAT DISPLAY
# =====================
for role, msg in st.session_state.messages:
    with st.chat_message(role):
        st.write(msg)

# =====================
# IA FUNCTION
# =====================
def ask_ai(messages):
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "Assistant administratif expert. Pose une question à la fois."},
            *[{"role": r, "content": m} for r, m in messages]
        ],
        temperature=0.3
    )
    return completion.choices[0].message.content

# =====================
# INPUT
# =====================
user_input = st.chat_input("Décrivez votre situation...")

if user_input:

    st.session_state.messages.append(("user", user_input))

    reply = ask_ai(st.session_state.messages)

    st.session_state.messages.append(("assistant", reply))

    st.rerun()

# =====================
# CONVERSION BLOCK
# =====================
if len([m for m in st.session_state.messages if m[0] == "user"]) >= 3:

    st.divider()
    st.subheader("📄 Génération de document")

    st.markdown("""
✔ Lettre administrative personnalisée  
✔ CAF / DALO / Préfecture / Recours  
✔ Document prêt à envoyer  
""")

    if st.button("Générer mon document (9€)"):

        res = requests.post(
            f"{BACKEND_URL}/create-checkout-session",
            json={
                "summary": st.session_state.messages[-1][1]
            }
        )

        try:
            data = res.json()
        except:
            st.error("Erreur backend")
            st.write(res.text)
            st.stop()

        if "url" in data:
            st.markdown(f"[👉 Payer maintenant]({data['url']})")
        else:
            st.error(data)
