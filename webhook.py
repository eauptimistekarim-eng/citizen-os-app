from flask import Flask, request, jsonify, send_from_directory
import stripe
import os

from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)

# =====================
# CONFIG
# =====================
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

# 👉 TON URL STREAMLIT (corrigée)
FRONTEND_URL = "https://citizen-os-app.streamlit.app"

# =====================
# HOME
# =====================
@app.route("/")
def home():
    return "CitizenOS backend OK"

# =====================
# CREATE CHECKOUT
# =====================
@app.route("/create-checkout-session", methods=["POST"])
def create_checkout():
    try:
        data = request.json or {}
        situation = data.get("situation", "")[:400]  # limite Stripe

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "eur",
                    "product_data": {
                        "name": "Consultation administrative personnalisée"
                    },
                    "unit_amount": 900
                },
                "quantity": 1
            }],
            mode="payment",

            # ✅ REDIRECTION CORRIGÉE
            success_url=f"{FRONTEND_URL}?success=true&email={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{FRONTEND_URL}?cancel=true",

            metadata={"situation": situation}
        )

        return jsonify({"url": session.url})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =====================
# PDF GENERATION
# =====================
def generate_pdf(filename, situation):

    doc = SimpleDocTemplate(filename)
    styles = getSampleStyleSheet()

    content = [
        Paragraph("CONSULTATION ADMINISTRATIVE PERSONNALISÉE", styles["Title"]),
        Paragraph(" ", styles["Normal"]),

        Paragraph("1. Situation analysée", styles["Heading2"]),
        Paragraph(situation, styles["Normal"]),

        Paragraph(" ", styles["Normal"]),
        Paragraph("2. Analyse", styles["Heading2"]),
        Paragraph(
            "Votre situation révèle un blocage administratif nécessitant une action structurée.",
            styles["Normal"]
        ),

        Paragraph(" ", styles["Normal"]),
        Paragraph("3. Recommandation", styles["Heading2"]),
        Paragraph(
            "Il est recommandé d'envoyer un courrier formel afin d'engager une réponse officielle.",
            styles["Normal"]
        ),

        Paragraph(" ", styles["Normal"]),
        Paragraph("4. Lettre générée", styles["Heading2"]),
        Paragraph(
            "Madame, Monsieur,<br/><br/>"
            "Je me permets de vous contacter concernant ma situation administrative actuelle.<br/><br/>"
            "Malgré mes démarches, aucune solution satisfaisante n’a été apportée à ce jour.<br/><br/>"
            "Je vous demande donc un traitement prioritaire de mon dossier.<br/><br/>"
            "Je vous remercie par avance pour votre attention.<br/><br/>"
            "Cordialement.",
            styles["Normal"]
        ),
    ]

    doc.build(content)


# =====================
# WEBHOOK STRIPE
# =====================
@app.route("/webhook", methods=["POST"])
def webhook():

    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except Exception:
        return "", 400

    # 🔥 PAIEMENT VALIDÉ
    if event["type"] == "checkout.session.completed":

        session = event["data"]["object"]

        situation = session["metadata"].get("situation", "")
        session_id = session["id"]

        filename = f"COURRIER_{session_id}.pdf"

        generate_pdf(filename, situation)

        print("💰 Paiement confirmé + PDF généré :", filename)

    return "", 200


# =====================
# DOWNLOAD
# =====================
@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(".", filename, as_attachment=True)


# =====================
# RUN
# =====================
if __name__ == "__main__":
    app.run(port=5001)
