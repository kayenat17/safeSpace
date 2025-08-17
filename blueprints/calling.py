from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from flask_mail import Mail, Message
from twilio.rest import Client
import pytz
import logging
from extensions import db  # Import the shared db instance

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

calling_bp = Blueprint('calling', __name__, template_folder='../calling/templates')

# Models (same as in calling/app.py)
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

# Utility functions

def send_sos_notification(user, is_manual=False):
    try:
        if not user.emergency_contacts:
            logger.warning(f"No emergency contacts found for user {user.email}")
            return False
        # Fetch the latest location for the user
        latest_location = LocationHistory.query.filter_by(user_id=user.id)\
                                   .order_by(LocationHistory.timestamp.desc())\
                                   .first()
        location_info = "Location information not available."
        if latest_location:
            location_info = f"Last known location: Latitude {latest_location.latitude}, Longitude {latest_location.longitude} (at {latest_location.timestamp})"
        for contact in user.emergency_contacts:
            # Send email notification
            try:
                msg = Message(
                    'SOS Alert - Safety Check-in Missed' if not is_manual else 'SOS Alert - Manual Emergency',
                    sender=current_app.config['MAIL_USERNAME'],
                    recipients=[contact.email]
                )
                msg.body = f'''
                This is an automated SOS message.
                {user.name} has {'manually triggered an emergency alert' if is_manual else 'missed their safety check-in'}.
                Last check-in: {user.last_check_in}
                {location_info}
                Please check on them immediately.
                '''
                mail = Mail(current_app)
                mail.send(msg)
            except Exception as e:
                logger.error(f"Failed to send email to {contact.email}. Error: {str(e)}")
            # Send phone call notification
            if contact.phone and current_app.config.get('TWILIO_ACCOUNT_SID') and current_app.config.get('TWILIO_AUTH_TOKEN'):
                try:
                    twilio_client = Client(current_app.config['TWILIO_ACCOUNT_SID'], current_app.config['TWILIO_AUTH_TOKEN'])
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
                    call = twilio_client.calls.create(
                        to=contact.phone,
                        from_=current_app.config['TWILIO_PHONE_NUMBER'],
                        twiml=twiml
                    )
                except Exception as e:
                    logger.error(f"Failed to make call to {contact.phone}. Error: {str(e)}")
        return True
    except Exception as e:
        logger.error(f"Error in send_sos_notification: {str(e)}")
        return False

# Routes
@calling_bp.route('/')
def index():
    return render_template('index.html')

@calling_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('calling.register'))
        user = User(
            email=email,
            password_hash=generate_password_hash(password),
            name=name
        )
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please login.')
        return redirect(url_for('calling.login'))
    return render_template('register.html')

@calling_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            user.last_check_in = datetime.utcnow()
            db.session.commit()
            return redirect(url_for('calling.dashboard'))
        flash('Invalid email or password')
    return render_template('login.html')

@calling_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@calling_bp.route('/check-in', methods=['POST'])
@login_required
def check_in():
    current_user.last_check_in = datetime.utcnow()
    db.session.commit()
    return jsonify({'status': 'success'})

@calling_bp.route('/send-sos', methods=['POST'])
@login_required
def send_sos():
    if not current_user.emergency_contacts:
        return jsonify({'status': 'error', 'message': 'No emergency contacts found'})
    if not all([current_app.config['MAIL_USERNAME'], current_app.config['MAIL_PASSWORD']]):
        return jsonify({'status': 'error', 'message': 'Email configuration is incomplete. Please contact support.'})
    success = send_sos_notification(current_user, is_manual=True)
    if success:
        return jsonify({'status': 'success', 'message': 'SOS alert sent to all emergency contacts'})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to send SOS alert. Please check your email configuration.'})

@calling_bp.route('/emergency-contacts', methods=['GET', 'POST'])
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
        return redirect(url_for('calling.emergency_contacts'))
    contacts = EmergencyContact.query.filter_by(user_id=current_user.id).all()
    return render_template('emergency_contacts.html', contacts=contacts)

@calling_bp.route('/delete-contact/<int:contact_id>', methods=['POST'])
@login_required
def delete_contact(contact_id):
    contact = EmergencyContact.query.get_or_404(contact_id)
    if contact.user_id != current_user.id:
        flash('Unauthorized action')
        return redirect(url_for('calling.emergency_contacts'))
    db.session.delete(contact)
    db.session.commit()
    flash('Contact deleted successfully')
    return redirect(url_for('calling.emergency_contacts'))

@calling_bp.route('/save-location', methods=['POST'])
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

@calling_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('calling.index'))

@calling_bp.route('/location-history', methods=['GET'])
@login_required
def get_location_history():
    try:
        locations = LocationHistory.query.filter_by(user_id=current_user.id)
        locations = locations.order_by(LocationHistory.timestamp.desc())
        locations = locations.limit(20)
        locations = locations.all()
        location_data = []
        for loc in locations:
            utc_dt = pytz.UTC.localize(loc.timestamp)
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

@calling_bp.route('/test-notifications')
@login_required
def test_notifications():
    try:
        test_msg = Message(
            'Test Email from Safety App',
            sender=current_app.config['MAIL_USERNAME'],
            recipients=[current_user.email]
        )
        test_msg.body = 'This is a test email from your Safety App.'
        mail = Mail(current_app)
        mail.send(test_msg)
        if current_app.config.get('TWILIO_ACCOUNT_SID') and current_app.config.get('TWILIO_AUTH_TOKEN') and current_user.emergency_contacts:
            twilio_client = Client(current_app.config['TWILIO_ACCOUNT_SID'], current_app.config['TWILIO_AUTH_TOKEN'])
            for contact in current_user.emergency_contacts:
                if contact.phone:
                    twiml = '''
                    <Response>
                        <Say>This is a test call from your Safety App. If you hear this message, your phone call configuration is working correctly.</Say>
                    </Response>
                    '''
                    call = twilio_client.calls.create(
                        to=contact.phone,
                        from_=current_app.config['TWILIO_PHONE_NUMBER'],
                        twiml=twiml
                    )
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

@calling_bp.route('/clear-location-history', methods=['POST'])
@login_required
def clear_location_history():
    try:
        LocationHistory.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Location history cleared successfully'})
    except Exception as e:
        logger.error(f"Error clearing location history for user {current_user.id}: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to clear location history'}), 500 