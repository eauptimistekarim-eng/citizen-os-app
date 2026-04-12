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
st.title("CitizenOS - Analyse Administrative IA")

st.markdown("""
### Assistant d’analyse et de structuration administrative

Cet outil vous aide à comprendre une situation administrative complexe  
et à générer un document adapté (CAF, DALO, préfecture, recours).

⚠️ Il ne remplace pas un avocat, mais vous guide avec une logique professionnelle.
""")

# =====================
# SUCCESS PAGE
# =====================
query_params = st.query_params

if "success" in query_params:

    st.success("✅ Paiement confirmé")

    st.subheader("📄 Votre document est prêt")

    email = query_params.get("email", "client")

    file_url = f"{BACKEND_URL}/download/COURRIER_{email}.pdf"

    st.info("Téléchargement automatique en cours...")

    st.markdown(f"""
        <meta http-equiv="refresh" content="2;url={file_url}">
    """, unsafe_allow_html=True)

    st.markdown(f"[📥 Télécharger manuellement]({file_url})")

    st.stop()

# =====================
# IA PROMPT
# =====================
SYSTEM_PROMPT = """
Tu es un expert administratif français.

OBJECTIF :
- comprendre une situation administrative
- poser UNE question à la fois
- reformuler régulièrement
- structurer progressivement le problème
- détecter le niveau d'urgence
- préparer une stratégie

STYLE :
- phrases courtes
- ton professionnel
- clair
- effet "machine à écrire"

IMPORTANT :
- ne donne pas la solution complète
- crée un besoin de document
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
# SESSION STATE
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

    # 🔥 Déblocage conversion après 4 messages user
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

👉 Vous pouvez maintenant obtenir :

- une **lettre administrative personnalisée**
- prête à envoyer immédiatement
- rédigée dans un format professionnel
- adaptée à votre cas précis (CAF, DALO, préfecture…)

⏱️ Temps : immédiat  
💰 Prix : 9€
""")

    if st.button("Générer mon document (9€)"):

        situation = str(st.session_state.messages)[-400:]  # 🔥 limite Stripe

        response = requests.post(
            f"{BACKEND_URL}/create-checkout-session",
            json={"situation": situation}
        )

        data = response.json()

        if "url" in data:
            st.markdown(f"[👉 Accéder au paiement]({data['url']})")
        else:
            st.error(data)
