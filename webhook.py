from flask import Flask, request, jsonify, send_from_directory
import stripe
import os
from dotenv import load_dotenv
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

load_dotenv()

app = Flask(__name__)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

DOC_FOLDER = "documents"
os.makedirs(DOC_FOLDER, exist_ok=True)


# =====================
# HOME
# =====================
@app.route("/")
def home():
    return "CitizenOS OK"


# =====================
# DETECT CASE
# =====================
def detect_case(text):
    t = text.lower()

    if "dalo" in t:
        return "DALO"
    if "caf" in t:
        return "CAF"
    if "préfecture" in t or "titre de séjour" in t:
        return "PREFECTURE"
    if "logement" in t:
        return "LOGEMENT"
    if "recours" in t:
        return "RECOURS"

    return "COURRIER"


# =====================
# LETTER ENGINE (AMÉLIORÉ)
# =====================
def build_letter(doc_type, situation):

    base = f"""
Objet : Demande de traitement de situation administrative

Madame, Monsieur,

Je soussigné(e), vous expose la situation suivante :

{situation}

"""

    if doc_type == "DALO":
        body = """
Au regard de ma situation actuelle, je sollicite la reconnaissance de mon droit au logement opposable (DALO).

Ma situation ne me permet pas d’accéder à un logement stable et décent.

Je demande l’examen prioritaire de mon dossier conformément aux dispositions en vigueur.
"""

    elif doc_type == "CAF":
        body = """
Je sollicite un réexamen complet de mon dossier auprès de la CAF.

Certaines incohérences ou retards impactent actuellement ma situation sociale et financière.

Je demande une vérification et une régularisation de mes droits.
"""

    elif doc_type == "PREFECTURE":
        body = """
Je sollicite l’examen de ma situation administrative auprès de la préfecture.

Je demande la réévaluation de mon dossier afin de clarifier ma situation et mes droits au séjour ou à la régularisation.
"""

    elif doc_type == "RECOURS":
        body = """
Je forme un recours administratif concernant la décision prise à mon encontre.

Je demande une révision complète de cette décision au regard des éléments de ma situation.
"""

    else:
        body = """
Je sollicite une prise en compte et une analyse de ma situation administrative.
"""

    end = """
Je vous prie d’agréer, Madame, Monsieur, l’expression de ma considération distinguée.
"""

    return base + body + end


# =====================
# PDF GENERATION
# =====================
def generate_pdf(email, doc_type, situation):

    filename = f"{doc_type}_{email.replace('@','_')}.pdf"
    path = os.path.join(DOC_FOLDER, filename)

    doc = SimpleDocTemplate(path)
    styles = getSampleStyleSheet()

    text = build_letter(doc_type, situation)

    content = [
        Paragraph(f"<b>{doc_type}</b>", styles["Title"]),
        Spacer(1, 12),
        Paragraph(text.replace("\n", "<br/>"), styles["Normal"])
    ]

    doc.build(content)
    return filename


# =====================
# DOWNLOAD
# =====================
@app.route("/download/<file>")
def download(file):
    return send_from_directory(DOC_FOLDER, file, as_attachment=True)


# =====================
# CHECKOUT
# =====================
@app.route("/create-checkout-session", methods=["POST"])
def checkout():

    data = request.json or {}
    situation = data.get("situation", "")[:500]

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="payment",
        line_items=[{
            "price_data": {
                "currency": "eur",
                "product_data": {
                    "name": "CitizenOS - Document administratif IA"
                },
                "unit_amount": 900
            },
            "quantity": 1
        }],
        success_url="http://localhost:8501/?success=true",
        cancel_url="http://localhost:8501/?cancel=true",
        metadata={"situation": situation}
    )

    return jsonify({"url": session.url})


# =====================
# WEBHOOK STRIPE
# =====================
@app.route("/webhook", methods=["POST"])
def webhook():

    payload = request.data
    sig = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig, endpoint_secret)
    except Exception:
        return "", 400

    if event["type"] == "checkout.session.completed":

        session = event["data"]["object"]

        email = session.get("customer_details", {}).get("email", "client@email.com")
        situation = session.get("metadata", {}).get("situation", "")

        doc_type = detect_case(situation)
        file = generate_pdf(email, doc_type, situation)

        print("✔ Document généré :", file)

    return "", 200


if __name__ == "__main__":
    app.run(port=5001)