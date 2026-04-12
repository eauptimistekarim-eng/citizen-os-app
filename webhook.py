from flask import Flask, request, jsonify, send_file
import stripe
import os
import uuid
from reportlab.pdfgen import canvas

app = Flask(__name__)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

FRONTEND_URL = "https://citizen-os-app.streamlit.app"

# =====================
# STORAGE MEMORY SIMPLE
# =====================
PDF_STORAGE = {}

# =====================
# HOME
# =====================
@app.route("/")
def home():
    return jsonify({"status": "ok"})

# =====================
# CREATE CHECKOUT
# =====================
@app.route("/create-checkout-session", methods=["POST"])
def create_checkout():

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

# =====================
# WEBHOOK STRIPE (IMPORTANT)
# =====================
@app.route("/webhook", methods=["POST"])
def webhook():

    payload = request.data
    event = stripe.Event.construct_from(
        stripe.json.loads(payload), stripe.api_key
    )

    if event["type"] == "checkout.session.completed":

        session = event["data"]["object"]

        session_id = session["id"]
        summary = session.get("metadata", {}).get("summary", "")

        file_id = str(uuid.uuid4())
        file_path = f"/tmp/{file_id}.pdf"

        pdf = canvas.Canvas(file_path)
        pdf.drawString(50, 800, "CITIZENOS - LETTRE ADMINISTRATIVE")
        pdf.drawString(50, 750, summary[:1000])
        pdf.save()

        PDF_STORAGE[session_id] = file_path

    return "", 200

# =====================
# DOWNLOAD STABLE
# =====================
@app.route("/download/<session_id>")
def download(session_id):

    file_path = PDF_STORAGE.get(session_id)

    if not file_path:
        return jsonify({
            "error": "file_not_ready",
            "message": "Document pas encore généré"
        }), 404

    return send_file(
        file_path,
        as_attachment=True,
        download_name="citizenos_lettre.pdf",
        mimetype="application/pdf"
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
