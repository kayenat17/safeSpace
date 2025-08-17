# Relationship Analyzer

A web application that helps users analyze and understand their relationships with family members, siblings, and partners through interactive questionnaires.

## Features

- User authentication system
- Interactive relationship questionnaires
- Different question sets for family, sibling, and partner relationships
- Beautiful and responsive UI with a soft color palette
- Dynamic form generation based on relationship type
- Secure data storage with SQLite database

## Tech Stack

- Backend: Python (Flask)
- Frontend: HTML, CSS, JavaScript
- Database: SQLite
- Authentication: Flask-Login

## Setup Instructions

1. Clone the repository:
```bash
git clone <repository-url>
cd relationship-analyzer
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Initialize the database:
```bash
python app.py
```

5. Run the application:
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Usage

1. Register a new account or login with existing credentials
2. Navigate to the dashboard
3. Start a new relationship analysis by selecting the relationship type
4. Fill out the questionnaire with detailed responses
5. View your analysis history in the dashboard

## Project Structure

```
relationship-analyzer/
├── app.py              # Main application file
├── requirements.txt    # Python dependencies
├── templates/          # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   └── questionnaire.html
└── README.md
```

## Contributing

Feel free to submit issues and enhancement requests! 