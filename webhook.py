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
# CREATE CHECKOUT SESSION
# =====================
@app.route("/create-checkout-session", methods=["POST"])
def create_checkout():

    data = request.json or {}
    messages = data.get("messages", [])
    summary = data.get("summary", "")

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
            "summary": summary[:500]
        }
    )

    return jsonify({"url": session.url})

# =====================
# PDF GENERATION (IN MEMORY)
# =====================
def generate_pdf_buffer(text):

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer)

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, 800, "LETTRE ADMINISTRATIVE - CITIZENOS")

    pdf.setFont("Helvetica", 11)

    text_obj = pdf.beginText(50, 750)
    text_obj.textLines("Situation :")
    text_obj.textLines(text[:1200])

    text_obj.textLines("\nAnalyse :")
    text_obj.textLines("Votre situation nécessite une structuration administrative.")

    text_obj.textLines("\nLettre :")
    text_obj.textLines(
        "Madame, Monsieur,\n\n"
        "Je vous adresse ce courrier concernant ma situation administrative.\n"
        "Je sollicite une réévaluation de mon dossier.\n\n"
        "Cordialement."
    )

    pdf.drawText(text_obj)
    pdf.save()

    buffer.seek(0)
    return buffer

# =====================
# DOWNLOAD
# =====================
@app.route("/download/<session_id>")
def download(session_id):

    session = stripe.checkout.Session.retrieve(session_id)
    summary = session["metadata"].get("summary", "")

    pdf_buffer = generate_pdf_buffer(summary)

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
    app.run(host="0.0.0.0", port=5001)
