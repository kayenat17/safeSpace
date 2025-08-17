import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
from extensions import db, mail, login_manager
from blueprints.calling import calling_bp, User
from blueprints.pinging import pinging_bp, init_pinging_database
from blueprints.chat_analyser import chat_analyser_bp
import smtplib

# Import the chat analyser function
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'chat analyser/chat analyser')))
from analyze_chat import analyze_chat

def analyze_text_toxicity(text):
    """Analyze the toxicity of a given text using the chat analyser."""
    return analyze_chat(text)

load_dotenv()

# Ensure directories exist
os.makedirs('pinging/instance', exist_ok=True)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-123')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///safety_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('GOOGLE_2FA_SECRET')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')
app.config['TWILIO_ACCOUNT_SID'] = os.getenv('TWILIO_ACCOUNT_SID', 'your-account-sid-from-twilio')
app.config['TWILIO_AUTH_TOKEN'] = os.getenv('TWILIO_AUTH_TOKEN', 'your-auth-token-from-twilio')
app.config['TWILIO_PHONE_NUMBER'] = os.getenv('TWILIO_PHONE_NUMBER', 'your-twilio-phone-number')

db.init_app(app)
mail.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'calling.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Register blueprints
app.register_blueprint(calling_bp, url_prefix='/calling')
app.register_blueprint(pinging_bp, url_prefix='/pinging')
app.register_blueprint(chat_analyser_bp, url_prefix='/chat-analyser')
init_pinging_database()

@app.route('/')
def home():
    return render_template('unified_home.html')

@app.route('/analyze-chat', methods=['POST'])
def analyze_chat_api():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400
    text = data['text']
    score = analyze_text_toxicity(text)
    if score is None:
        return jsonify({'error': 'Failed to analyze text'}), 500
    return jsonify({'score': score, 'text': text})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5050) 
