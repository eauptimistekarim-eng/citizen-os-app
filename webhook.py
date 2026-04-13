from flask import Flask, request, jsonify
from flask_cors import CORS
import stripe
import os

app = Flask(__name__)
CORS(app)

# Config
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
STREAMLIT_URL = os.environ.get("STREAMLIT_URL") # Ex: https://votreapp.streamlit.app

# Cache mémoire (Stateless : vidé à chaque reboot Render)
# C'est suffisant pour le laps de temps d'un paiement (2-3 min)
storage_cache = {}

@app.route('/create-checkout-session', methods=['POST'])
def create_session():
    try:
        data = request.json
        full_content = data.get("content", "")
        
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'product_data': {'name': 'Génération Document CitizenOS'},
                    'unit_amount': 1000,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f"{STREAMLIT_URL}?status=success&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=STREAMLIT_URL,
            metadata={"check": "valid"} 
        )
        
        # On stocke le texte avec l'ID de session comme clé
        storage_cache[session.id] = full_content
        return jsonify({"url": session.url})
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route('/get_content/<session_id>', methods=['GET'])
def get_content(session_id):
    # L'app Streamlit récupère le texte ici après le succès
    content = storage_cache.get(session_id)
    if content:
        # Nettoyage optionnel du cache après récupération pour libérer la RAM
        # doc = storage_cache.pop(session_id) 
        return jsonify({"content": content})
    return jsonify(error="Document non trouvé ou expiré"), 404

@app.route('/webhook', methods=['POST'])
def webhook():
    # Gardé pour la conformité Stripe, mais la logique principale est au-dessus
    return jsonify(success=True), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
