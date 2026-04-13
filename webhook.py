from flask import Flask, request, jsonify
import stripe
import os

app = Flask(__name__)

# Configuration
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET")

# Stockage temporaire (Attention: Render reset ce dict au restart)
# Solution sans DB : On utilise la durée de vie du processus pour le transit
temp_storage = {}

@app.route('/create-checkout-session', methods=['POST'])
def create_session():
    try:
        data = request.json
        content = data.get("content", "")
        
        # On limite pour la sécurité mais on garde le gros du texte ici
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'product_data': {'name': 'Document CitizenOS'},
                    'unit_amount': 1000,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=os.environ.get("STREAMLIT_URL") + "?status=success&session_id={CHECKOUT_SESSION_ID}",
            cancel_url=os.environ.get("STREAMLIT_URL"),
            # On ne stocke que les 100 premiers caractères en metadata par sécurité
            metadata={"summary": content[:100]} 
        )
        
        # Stockage du contenu lié au session_id
        temp_storage[checkout_session.id] = content
        return jsonify({"url": checkout_session.url})
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route('/get_content/<session_id>', methods=['GET'])
def get_content(session_id):
    # L'app Streamlit vient chercher le texte ici
    content = temp_storage.get(session_id)
    if content:
        return jsonify({"content": content})
    
    # Fallback : Si Render a reboot, on tente de récupérer le summary Stripe
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        return jsonify({"content": session.metadata.get("summary", "Contenu expiré.")})
    except:
        return jsonify(error="Not found"), 404

@app.route('/webhook', methods=['POST'])
def webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
    except:
        return jsonify(success=False), 400

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        print(f"Paiement réussi pour session {session.id}")
        
    return jsonify(success=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
