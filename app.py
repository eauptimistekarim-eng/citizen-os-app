import streamlit as st
import requests
from groq import Groq

BACKEND_URL = st.secrets["BACKEND_URL"]
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

st.title("CitizenOS - Assistant Administratif IA")

# =====================
# SUCCESS PAGE FIX
# =====================
if st.query_params.get("success"):

    session_id = st.query_params.get("session_id")

    st.success("Paiement confirmé ✔")

    if session_id:
        st.markdown("### 📄 Votre document est prêt")

        file_url = f"{BACKEND_URL}/download/{session_id}"

        st.markdown(f"[📥 Télécharger votre document]({file_url})")

    st.stop()

# =====================
# CHAT SIMPLE
# =====================
if "messages" not in st.session_state:
    st.session_state.messages = []

user_input = st.chat_input("Décrivez votre situation...")

if user_input:
    st.session_state.messages.append(("user", user_input))

    reply = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "Assistant administratif"},
            {"role": "user", "content": user_input}
        ]
    ).choices[0].message.content

    st.session_state.messages.append(("assistant", reply))

    st.rerun()

# =====================
# PAYMENT BLOCK
# =====================
if len([m for m in st.session_state.messages if m[0] == "user"]) >= 3:

    st.divider()
    st.subheader("📄 Génération de document")

    if st.button("Générer (9€)"):

        res = requests.post(
            f"{BACKEND_URL}/create-checkout-session",
            json={
                "summary": st.session_state.messages[-1][1]
            }
        )

        data = res.json()

        if "url" in data:
            st.markdown(f"[Payer maintenant]({data['url']})")
