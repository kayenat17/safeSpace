from flask import Blueprint, render_template, request, redirect, url_for, jsonify
import sqlite3
import os
import json
from datetime import datetime

pinging_bp = Blueprint('pinging', __name__, 
                      template_folder='../pinging/templates',
                      static_folder='../pinging/static',
                      static_url_path='/pinging/static')

# Ensure the data directory exists
os.makedirs('data', exist_ok=True)

# Database file path
DB_PATH = 'pinging/relationships.db'

def get_db_connection():
    """Get a connection to the pinging database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_pinging_database():
    """Initialize the pinging database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS relationship (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            relationship_type TEXT NOT NULL,
            person_name TEXT NOT NULL,
            answers TEXT
        )
    ''')
    conn.commit()
    conn.close()

def analyze_relationship(relationship_type, responses):
    analysis = {
        'overall_score': 0,
        'strengths': [],
        'weaknesses': [],
        'recommendations': [],
        'insights': []
    }
    numerical_responses = []
    text_responses = []
    
    # Handle both list and dictionary responses
    if isinstance(responses, dict):
        # Convert dictionary values to list
        response_values = list(responses.values())
    else:
        # Already a list
        response_values = responses
    
    for i, response in enumerate(response_values):
        if isinstance(response, str) and response.isdigit():
            numerical_responses.append(int(response))
        else:
            text_responses.append(response)
    if numerical_responses:
        analysis['overall_score'] = sum(numerical_responses) / len(numerical_responses)
    if relationship_type == 'family':
        if analysis['overall_score'] >= 4:
            analysis['strengths'].append("Strong emotional connection")
            analysis['strengths'].append("Good communication patterns")
        elif analysis['overall_score'] <= 2:
            analysis['weaknesses'].append("Limited emotional connection")
            analysis['weaknesses'].append("Communication challenges")
        for response in text_responses:
            if 'challenge' in str(response).lower():
                analysis['weaknesses'].append("Identified challenges in the relationship")
            if 'improve' in str(response).lower():
                analysis['recommendations'].append("Areas for improvement identified")
    elif relationship_type == 'sibling':
        if analysis['overall_score'] >= 4:
            analysis['strengths'].append("Strong sibling bond")
            analysis['strengths'].append("Good conflict resolution")
        elif analysis['overall_score'] <= 2:
            analysis['weaknesses'].append("Distant sibling relationship")
            analysis['weaknesses'].append("Conflict resolution needs improvement")
        for response in text_responses:
            if 'interest' in str(response).lower():
                analysis['strengths'].append("Shared interests identified")
            if 'improve' in str(response).lower():
                analysis['recommendations'].append("Specific improvement areas noted")
    elif relationship_type == 'partner':
        if analysis['overall_score'] >= 4:
            analysis['strengths'].append("Strong partnership")
            analysis['strengths'].append("Good emotional intimacy")
        elif analysis['overall_score'] <= 2:
            analysis['weaknesses'].append("Relationship challenges")
            analysis['weaknesses'].append("Limited emotional connection")
        for response in text_responses:
            if 'goal' in str(response).lower():
                analysis['insights'].append("Future goals discussed")
            if 'conflict' in str(response).lower():
                analysis['weaknesses'].append("Conflict management needs attention")
            if 'improve' in str(response).lower():
                analysis['recommendations'].append("Specific improvement areas identified")
    if analysis['overall_score'] < 3:
        analysis['recommendations'].append("Consider increasing quality time together")
        analysis['recommendations'].append("Work on improving communication")
    elif analysis['overall_score'] >= 4:
        analysis['recommendations'].append("Maintain current positive patterns")
        analysis['recommendations'].append("Continue building on strengths")
    return analysis

@pinging_bp.route('/')
def index():
    return render_template('pinging_index.html')

@pinging_bp.route('/dashboard')
def dashboard():
    conn = get_db_connection()
    relationships = conn.execute('SELECT * FROM relationship').fetchall()
    conn.close()
    return render_template('pinging_dashboard.html', relationships=relationships)

@pinging_bp.route('/questionnaire', methods=['GET', 'POST'])
def questionnaire():
    if request.method == 'POST':
        try:
            relationship_type = request.form.get('relationship_type')
            person_name = request.form.get('person_name')
            
            if not relationship_type or not person_name:
                return render_template('pinging_questionnaire.html', error="Please fill in all required fields")
            
            answers = {}
            for key, value in request.form.items():
                if key.startswith('question_'):
                    answers[key] = value
            
            analysis_results = analyze_relationship(relationship_type, answers)
            
            # Save to database
            conn = get_db_connection()
            conn.execute('INSERT INTO relationship (relationship_type, person_name, answers) VALUES (?, ?, ?)',
                        (relationship_type, person_name, json.dumps(answers)))
            conn.commit()
            conn.close()
            
            return render_template('pinging_results.html', 
                                 person_name=person_name,
                                 relationship_type=relationship_type,
                                 analysis=analysis_results)
        except Exception as e:
            print(f"Error in questionnaire route: {str(e)}")
            return render_template('pinging_questionnaire.html', error="An error occurred. Please try again.")
    
    return render_template('pinging_questionnaire.html')

@pinging_bp.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data received'}), 400
        
        relationship_type = data.get('relationship_type')
        person_name = data.get('person_name')
        responses = data.get('responses', [])
        
        if not relationship_type or not person_name:
            return jsonify({'error': 'Missing required fields'}), 400
        
        analysis = analyze_relationship(relationship_type, responses)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'data/analysis_{timestamp}.json'
        analysis_data = {
            'timestamp': timestamp,
            'relationship_type': relationship_type,
            'person_name': person_name,
            'responses': responses,
            'analysis': analysis
        }
        with open(filename, 'w') as f:
            json.dump(analysis_data, f, indent=2)
        return jsonify(analysis)
    except Exception as e:
        print(f"Error in analyze route: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500 