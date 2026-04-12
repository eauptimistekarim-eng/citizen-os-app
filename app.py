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
### Assistant administratif intelligent

Analyse de situations : CAF, DALO, Préfecture, recours.

⚠️ Outil d’aide, pas un avocat.
""")

# =====================
# SUCCESS PAGE
# =====================
if st.query_params.get("success"):

    st.success("✔ Paiement confirmé")

    session_id = st.query_params.get("session_id")

    if session_id:
        st.markdown("### 📄 Votre document est prêt")

        file_url = f"{BACKEND_URL}/download/{session_id}"
        st.markdown(f"[📥 Télécharger votre lettre]({file_url})")

    st.stop()

# =====================
# IA PROMPT
# =====================
SYSTEM_PROMPT = """
Tu es un assistant administratif expert.

Tu fonctionnes comme un entretien :
- une question à la fois
- reformulation
- style machine à écrire
- progression lente
- création d’un besoin de document

Ne donne jamais la solution complète trop tôt.
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
# CHAT UI
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
# CONVERSION BLOCK (SAFE)
# =====================
if st.session_state.unlock:

    st.divider()
    st.subheader("📄 Analyse complète disponible")

    st.markdown("""
✔ Lettre administrative personnalisée  
✔ CAF / DALO / Préfecture / Recours  
✔ Document prêt à envoyer  
""")

    if st.button("Générer mon document (9€)"):

        res = requests.post(
            f"{BACKEND_URL}/create-checkout-session",
            json={
                "messages": st.session_state.messages[-6:],
                "summary": st.session_state.messages[-1][1] if st.session_state.messages else ""
            }
        )

        # 🔥 FIX CRASH JSON
        try:
            data = res.json()
        except Exception:
            st.error("Erreur backend (réponse invalide)")
            st.write(res.text)
            st.stop()

        # 🔥 CHECK STATUS
        if res.status_code != 200:
            st.error("Erreur serveur backend")
            st.write(data)
            st.stop()

        if "url" in data:
            st.markdown(f"[👉 Accéder au paiement]({data['url']})")
        else:
            st.error(data)
