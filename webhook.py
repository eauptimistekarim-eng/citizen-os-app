from flask import Flask, request, jsonify
from flask_cors import CORS
import stripe
import os

app = Flask(__name__)
CORS(app)

# Récupération sécurisée des clés sur Render
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
STREAMLIT_URL = os.environ.get("STREAMLIT_URL")

storage = {}

@app.route('/create-checkout', methods=['POST'])
def create_checkout():
    try:
        data = request.json
        content = data.get('content', 'Document CitizenOS')
        
        # Création de session Stripe
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'product_data': {'name': 'Certification CitizenOS'},
                    'unit_amount': 1000,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f"{STREAMLIT_URL}?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=STREAMLIT_URL,
        )
        storage[session.id] = content
        return jsonify({'url': session.url})
    except Exception as e:
        # Renvoie l'erreur réelle pour débugger au lieu d'un 500 vide
        return jsonify(error=str(e)), 400 

@app.route('/get-doc/<session_id>', methods=['GET'])
def get_doc(session_id):
    content = storage.get(session_id)
    if content:
        return jsonify({'content': content})
    return jsonify(error="Non trouvé"), 404

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
