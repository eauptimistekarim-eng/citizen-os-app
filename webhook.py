from flask import Flask, request, jsonify, send_file
import stripe
import os
import io
from reportlab.pdfgen import canvas

app = Flask(__name__)

# =====================
# CONFIG
# =====================
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

FRONTEND_URL = "https://citizen-os-app.streamlit.app"

# =====================
# HOME
# =====================
@app.route("/")
def home():
    return "CitizenOS backend OK"

# =====================
# CHECKOUT
# =====================
@app.route("/create-checkout-session", methods=["POST"])
def create_checkout():

    data = request.json or {}
    situation = data.get("messages", "")[:500]

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "eur",
                "product_data": {
                    "name": "CitizenOS - Lettre administrative IA"
                },
                "unit_amount": 900
            },
            "quantity": 1
        }],
        mode="payment",

        success_url=f"{FRONTEND_URL}?success=true&session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{FRONTEND_URL}?cancel=true",

        metadata={
            "situation": situation
        }
    )

    return jsonify({"url": session.url})

# =====================
# PDF EN MÉMOIRE (IMPORTANT)
# =====================
def generate_pdf_buffer(situation):

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer)

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, 800, "LETTRE ADMINISTRATIVE")

    pdf.setFont("Helvetica", 11)

    text = pdf.beginText(50, 750)
    text.textLines("Situation :")
    text.textLines(situation[:1200])

    text.textLines("\n\nAnalyse :")
    text.textLines("Votre dossier nécessite une structuration administrative et une action adaptée.")

    text.textLines("\n\nLettre :")
    text.textLines(
        "Madame, Monsieur,\n\n"
        "Je vous contacte concernant ma situation administrative.\n"
        "Je sollicite une révision de mon dossier dans les meilleurs délais.\n\n"
        "Cordialement."
    )

    pdf.drawText(text)
    pdf.save()

    buffer.seek(0)
    return buffer

# =====================
# DOWNLOAD PDF
# =====================
@app.route("/download/<session_id>")
def download(session_id):

    session = stripe.checkout.Session.retrieve(session_id)
    situation = session["metadata"].get("situation", "")

    pdf_buffer = generate_pdf_buffer(situation)

    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name="citizenos_lettre.pdf",
        mimetype="application/pdf"
    )

# =====================
# RUN
# =====================
if __name__ == "__main__":
    app.run(port=5001)
