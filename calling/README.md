# Safety Check-in App

A web application that helps users stay safe by requiring regular check-ins. If a user doesn't respond to check-in requests, emergency contacts are notified.

## Features

- User registration and authentication
- Regular safety check-ins (every 12 hours)
- Emergency contact management
- Automatic SOS notifications
- Modern, user-friendly interface

## Setup Instructions

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a .env file with the following variables:
```
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-specific-password
```

4. Initialize the database:
```bash
flask db init
flask db migrate
flask db upgrade
```

5. Run the application:
```bash
flask run
```

## Security Features

- Regular check-ins every 12 hours
- Automatic SOS notifications to emergency contacts
- Secure password hashing
- Email verification
- Session management

## Tech Stack

- Backend: Python (Flask)
- Database: SQLite (can be changed to PostgreSQL for production)
- Frontend: HTML, CSS, JavaScript
- Email: Flask-Mail
- Task Scheduling: APScheduler 