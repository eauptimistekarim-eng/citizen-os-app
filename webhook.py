from flask import Flask, request, jsonify
from flask_cors import CORS
import stripe
import os

app = Flask(__name__)
CORS(app)

# Configuration
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
STREAMLIT_URL = os.environ.get("STREAMLIT_URL")

# Mémoire temporaire pour le document
storage = {}

@app.route('/create-checkout', methods=['POST'])
def create_checkout():
    try:
        data = request.json
        content = data.get('content', '')
        
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'product_data': {'name': 'Document Officiel CitizenOS'},
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
        return jsonify(error=str(e)), 500

@app.route('/get-doc/<session_id>', methods=['GET'])
def get_doc(session_id):
    content = storage.get(session_id)
    if content:
        return jsonify({'content': content})
    return jsonify(error="file_not_ready"), 404

if __name__ == '__main__':
    # Correction pour l'erreur de Port sur Render
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
