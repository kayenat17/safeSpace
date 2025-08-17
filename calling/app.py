from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from flask_mail import Mail, Message
from twilio.rest import Client
import os
from dotenv import load_dotenv
import pytz
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-123')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///safety_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', 'kayenatfatmi17@gmail.com')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', 'usmbptopuvwxhjxj')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')

# Twilio configuration
app.config['TWILIO_ACCOUNT_SID'] = os.getenv('TWILIO_ACCOUNT_SID', 'your-account-sid-from-twilio')
app.config['TWILIO_AUTH_TOKEN'] = os.getenv('TWILIO_AUTH_TOKEN', 'your-auth-token-from-twilio')
app.config['TWILIO_PHONE_NUMBER'] = os.getenv('TWILIO_PHONE_NUMBER', 'your-twilio-phone-number')

# Validate configurations
if not all([app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD']]):
    logger.warning("Email configuration is incomplete. Please check your .env file.")

if not all([app.config['TWILIO_ACCOUNT_SID'], app.config['TWILIO_AUTH_TOKEN'], app.config['TWILIO_PHONE_NUMBER']]):
    logger.warning("Twilio configuration is incomplete. Please check your .env file.")

db = SQLAlchemy(app)
mail = Mail(app)
twilio_client = Client(app.config['TWILIO_ACCOUNT_SID'], app.config['TWILIO_AUTH_TOKEN']) if app.config['TWILIO_ACCOUNT_SID'] and app.config['TWILIO_AUTH_TOKEN'] else None
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    name = db.Column(db.String(100))
    last_check_in = db.Column(db.DateTime, default=datetime.utcnow)
    emergency_contacts = db.relationship('EmergencyContact', backref='user', lazy=True)

class EmergencyContact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class LocationHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

# Scheduler setup
scheduler = BackgroundScheduler(timezone=pytz.UTC)
scheduler.start()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def check_user_safety():
    with app.app_context():
        users = User.query.all()
        for user in users:
            if datetime.utcnow() - user.last_check_in > timedelta(hours=12):
                send_sos_notification(user)

def send_sos_notification(user, is_manual=False):
    try:
        if not user.emergency_contacts:
            logger.warning(f"No emergency contacts found for user {user.email}")
            return False

        logger.info(f"Starting SOS notification process for user {user.email}")
        logger.info(f"Email configuration status: MAIL_USERNAME={app.config['MAIL_USERNAME']}, MAIL_PASSWORD={'Set' if app.config['MAIL_PASSWORD'] else 'Not Set'}")
        logger.info(f"Twilio configuration status: ACCOUNT_SID={'Set' if app.config['TWILIO_ACCOUNT_SID'] else 'Not Set'}, AUTH_TOKEN={'Set' if app.config['TWILIO_AUTH_TOKEN'] else 'Not Set'}")

        # Fetch the latest location for the user
        latest_location = LocationHistory.query.filter_by(user_id=user.id)\
                                       .order_by(LocationHistory.timestamp.desc())\
                                       .first()

        location_info = "Location information not available." # Default message
        if latest_location:
            location_info = f"Last known location: Latitude {latest_location.latitude}, Longitude {latest_location.longitude} (at {latest_location.timestamp})"
            logger.info(f"Latest location found: {location_info}")
        else:
            logger.warning(f"No location history found for user {user.email}")

        for contact in user.emergency_contacts:
            logger.info(f"Processing contact: {contact.name} (Email: {contact.email}, Phone: {contact.phone})")
            
            # Send email notification
            try:
                msg = Message(
                    'SOS Alert - Safety Check-in Missed' if not is_manual else 'SOS Alert - Manual Emergency',
                    sender=app.config['MAIL_USERNAME'],
                    recipients=[contact.email]
                )
                msg.body = f'''
                This is an automated SOS message.
                {user.name} has {'manually triggered an emergency alert' if is_manual else 'missed their safety check-in'}.
                Last check-in: {user.last_check_in}
                {location_info}

                Please check on them immediately.
                '''
                mail.send(msg)
                logger.info(f"Successfully sent SOS notification email to {contact.email}")
            except Exception as e:
                logger.error(f"Failed to send email to {contact.email}. Error: {str(e)}")

            # Send phone call notification
            if contact.phone and twilio_client:
                try:
                    logger.info(f"Attempting to make call to {contact.phone}")
                    # Create a TwiML response for the call
                    twiml = f'''
                    <Response>
                        <Say>This is an automated emergency alert. {user.name} has {'manually triggered an emergency alert' if is_manual else 'missed their safety check-in'}. 
                        Their last check-in was at {user.last_check_in}. {location_info}. Please check on them immediately.</Say>
                        <Pause length="2"/>
                        <Say>This message will repeat once more.</Say>
                        <Pause length="2"/>
                        <Say>This is an automated emergency alert. {user.name} has {'manually triggered an emergency alert' if is_manual else 'missed their safety check-in'}. 
                        Their last check-in was at {user.last_check_in}. {location_info}. Please check on them immediately.</Say>
                    </Response>
                    '''
                    
                    # Make the call
                    call = twilio_client.calls.create(
                        to=contact.phone,
                        from_=app.config['TWILIO_PHONE_NUMBER'],
                        twiml=twiml
                    )
                    logger.info(f"Successfully initiated call to {contact.phone}. Call SID: {call.sid}")
                except Exception as e:
                    logger.error(f"Failed to make call to {contact.phone}. Error: {str(e)}")
            elif not contact.phone:
                logger.warning(f"No phone number provided for contact {contact.email}")
            elif not twilio_client:
                logger.warning("Twilio client not configured. Phone calls will not be made.")

        return True
    except Exception as e:
        logger.error(f"Error in send_sos_notification: {str(e)}")
        return False

# Schedule the safety check every 12 hours
scheduler.add_job(check_user_safety, 'interval', hours=12, timezone=pytz.UTC)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))
        
        user = User(
            email=email,
            password_hash=generate_password_hash(password),
            name=name
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            user.last_check_in = datetime.utcnow()
            db.session.commit()
            return redirect(url_for('dashboard'))
        
        flash('Invalid email or password')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/check-in', methods=['POST'])
@login_required
def check_in():
    current_user.last_check_in = datetime.utcnow()
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/send-sos', methods=['POST'])
@login_required
def send_sos():
    if not current_user.emergency_contacts:
        return jsonify({'status': 'error', 'message': 'No emergency contacts found'})
    
    if not all([app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD']]):
        return jsonify({'status': 'error', 'message': 'Email configuration is incomplete. Please contact support.'})
    
    success = send_sos_notification(current_user, is_manual=True)
    if success:
        return jsonify({'status': 'success', 'message': 'SOS alert sent to all emergency contacts'})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to send SOS alert. Please check your email configuration.'})

@app.route('/emergency-contacts', methods=['GET', 'POST'])
@login_required
def emergency_contacts():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        
        contact = EmergencyContact(
            name=name,
            email=email,
            phone=phone,
            user_id=current_user.id
        )
        db.session.add(contact)
        db.session.commit()
        
        flash('Emergency contact added successfully')
        return redirect(url_for('emergency_contacts'))
    
    contacts = EmergencyContact.query.filter_by(user_id=current_user.id).all()
    return render_template('emergency_contacts.html', contacts=contacts)

@app.route('/delete-contact/<int:contact_id>', methods=['POST'])
@login_required
def delete_contact(contact_id):
    contact = EmergencyContact.query.get_or_404(contact_id)
    if contact.user_id != current_user.id:
        flash('Unauthorized action')
        return redirect(url_for('emergency_contacts'))
    
    db.session.delete(contact)
    db.session.commit()
    flash('Contact deleted successfully')
    return redirect(url_for('emergency_contacts'))

@app.route('/save-location', methods=['POST'])
@login_required
def save_location():
    data = request.get_json()
    latitude = data.get('latitude')
    longitude = data.get('longitude')

    if latitude is None or longitude is None:
        return jsonify({'status': 'error', 'message': 'Invalid location data'}), 400

    try:
        location = LocationHistory(
            user_id=current_user.id,
            latitude=latitude,
            longitude=longitude
        )
        db.session.add(location)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Location saved successfully'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving location for user {current_user.id}: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to save location'}), 500

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/location-history', methods=['GET'])
@login_required
def get_location_history():
    try:
        # Fetch location history for the current user, ordered by timestamp (latest first)
        locations = LocationHistory.query.filter_by(user_id=current_user.id)
        locations = locations.order_by(LocationHistory.timestamp.desc())
        locations = locations.limit(20) # Limit to the last 20 locations
        locations = locations.all()

        # Format the location data for JSON response
        location_data = []
        for loc in locations:
            # Format timestamp for display
            # Using UTC timezone from pytz for consistent formatting
            utc_dt = pytz.UTC.localize(loc.timestamp)
            # You might want to convert this to the user's local timezone on the frontend
            formatted_timestamp = utc_dt.strftime('%m/%d/%Y, %I:%M:%S %p UTC')

            location_data.append({
                'latitude': loc.latitude,
                'longitude': loc.longitude,
                'timestamp': formatted_timestamp
            })

        return jsonify({'status': 'success', 'history': location_data})

    except Exception as e:
        logger.error(f"Error fetching location history for user {current_user.id}: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to fetch location history'}), 500

@app.route('/test-notifications')
@login_required
def test_notifications():
    try:
        # Test email configuration
        test_msg = Message(
            'Test Email from Safety App',
            sender=app.config['MAIL_USERNAME'],
            recipients=[current_user.email]
        )
        test_msg.body = 'This is a test email from your Safety App.'
        mail.send(test_msg)
        
        # Test Twilio configuration
        if twilio_client and current_user.emergency_contacts:
            for contact in current_user.emergency_contacts:
                if contact.phone:
                    twiml = '''
                    <Response>
                        <Say>This is a test call from your Safety App. If you hear this message, your phone call configuration is working correctly.</Say>
                    </Response>
                    '''
                    call = twilio_client.calls.create(
                        to=contact.phone,
                        from_=app.config['TWILIO_PHONE_NUMBER'],
                        twiml=twiml
                    )
                    logger.info(f"Test call initiated to {contact.phone}. Call SID: {call.sid}")
        
        return jsonify({
            'status': 'success',
            'message': 'Test notifications sent. Check your email and phone.'
        })
    except Exception as e:
        logger.error(f"Error in test notifications: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to send test notifications: {str(e)}'
        })

@app.route('/clear-location-history', methods=['POST'])
@login_required
def clear_location_history():
    try:
        # Delete all location history entries for the current user
        LocationHistory.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Location history cleared successfully'})
    except Exception as e:
        logger.error(f"Error clearing location history for user {current_user.id}: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to clear location history'}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 