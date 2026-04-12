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

FRONTEND_URL = "https://citizen-os-app.streamlit.app"

# =====================
# HOME
# =====================
@app.route("/")
def home():
    return jsonify({"status": "CitizenOS backend OK"})

# =====================
# CREATE CHECKOUT
# =====================
@app.route("/create-checkout-session", methods=["POST"])
def create_checkout():

    try:
        data = request.json or {}
        summary = data.get("summary", "")

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",

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

            success_url=f"{FRONTEND_URL}?success=true&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{FRONTEND_URL}?cancel=true",

            metadata={
                "summary": summary[:500]
            }
        )

        return jsonify({"url": session.url})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =====================
# PDF GENERATOR (NO STORAGE)
# =====================
def generate_pdf(text):

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer)

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, 800, "CITIZENOS - LETTRE ADMINISTRATIVE")

    pdf.setFont("Helvetica", 11)

    y = 760
    pdf.drawString(50, y, "SITUATION :")
    y -= 20

    for line in str(text)[:1200].split("\n"):
        pdf.drawString(50, y, line[:90])
        y -= 15
        if y < 50:
            break

    y -= 20
    pdf.drawString(50, y, "LETTRE :")
    y -= 20
    pdf.drawString(50, y, "Madame, Monsieur,")
    y -= 20
    pdf.drawString(50, y, "Je sollicite le traitement de ma situation administrative.")
    y -= 20
    pdf.drawString(50, y, "Veuillez agréer, mes salutations distinguées.")

    pdf.save()
    buffer.seek(0)

    return buffer

# =====================
# DOWNLOAD (FIX DEFINITIF)
# =====================
@app.route("/download/<session_id>")
def download(session_id):

    try:
        session = stripe.checkout.Session.retrieve(session_id)
        summary = session.get("metadata", {}).get("summary", "")

        pdf = generate_pdf(summary)

        return send_file(
            pdf,
            as_attachment=True,
            download_name="citizenos_lettre.pdf",
            mimetype="application/pdf"
        )

    except Exception as e:
        return jsonify({
            "error": "download_failed",
            "message": str(e)
        }), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
