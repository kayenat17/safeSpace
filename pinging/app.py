from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
import json
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///relationships.db'
db = SQLAlchemy(app)

# Ensure the data directory exists
os.makedirs('data', exist_ok=True)

class Relationship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    relationship_type = db.Column(db.String(50), nullable=False)
    person_name = db.Column(db.String(100), nullable=False)
    answers = db.Column(db.JSON)

def analyze_relationship(relationship_type, responses):
    analysis = {
        'overall_score': 0,
        'strengths': [],
        'weaknesses': [],
        'recommendations': [],
        'insights': []
    }
    
    # Convert responses to numerical values where applicable
    numerical_responses = []
    text_responses = []
    
    for i, response in enumerate(responses):
        if response.isdigit():
            numerical_responses.append(int(response))
        else:
            text_responses.append(response)
    
    # Calculate overall score from numerical responses
    if numerical_responses:
        analysis['overall_score'] = sum(numerical_responses) / len(numerical_responses)
    
    # Generate insights based on relationship type and responses
    if relationship_type == 'family':
        if analysis['overall_score'] >= 4:
            analysis['strengths'].append("Strong emotional connection")
            analysis['strengths'].append("Good communication patterns")
        elif analysis['overall_score'] <= 2:
            analysis['weaknesses'].append("Limited emotional connection")
            analysis['weaknesses'].append("Communication challenges")
        
        # Analyze text responses for family relationships
        for response in text_responses:
            if 'challenge' in response.lower():
                analysis['weaknesses'].append("Identified challenges in the relationship")
            if 'improve' in response.lower():
                analysis['recommendations'].append("Areas for improvement identified")
    
    elif relationship_type == 'sibling':
        if analysis['overall_score'] >= 4:
            analysis['strengths'].append("Strong sibling bond")
            analysis['strengths'].append("Good conflict resolution")
        elif analysis['overall_score'] <= 2:
            analysis['weaknesses'].append("Distant sibling relationship")
            analysis['weaknesses'].append("Conflict resolution needs improvement")
        
        # Analyze text responses for sibling relationships
        for response in text_responses:
            if 'interest' in response.lower():
                analysis['strengths'].append("Shared interests identified")
            if 'improve' in response.lower():
                analysis['recommendations'].append("Specific improvement areas noted")
    
    elif relationship_type == 'partner':
        if analysis['overall_score'] >= 4:
            analysis['strengths'].append("Strong partnership")
            analysis['strengths'].append("Good emotional intimacy")
        elif analysis['overall_score'] <= 2:
            analysis['weaknesses'].append("Relationship challenges")
            analysis['weaknesses'].append("Limited emotional connection")
        
        # Analyze text responses for partner relationships
        for response in text_responses:
            if 'goal' in response.lower():
                analysis['insights'].append("Future goals discussed")
            if 'conflict' in response.lower():
                analysis['weaknesses'].append("Conflict management needs attention")
            if 'improve' in response.lower():
                analysis['recommendations'].append("Specific improvement areas identified")
    
    # Add general recommendations based on overall score
    if analysis['overall_score'] < 3:
        analysis['recommendations'].append("Consider increasing quality time together")
        analysis['recommendations'].append("Work on improving communication")
    elif analysis['overall_score'] >= 4:
        analysis['recommendations'].append("Maintain current positive patterns")
        analysis['recommendations'].append("Continue building on strengths")
    
    return analysis

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    relationships = Relationship.query.all()
    return render_template('dashboard.html', relationships=relationships)

@app.route('/questionnaire', methods=['GET', 'POST'])
def questionnaire():
    if request.method == 'POST':
        relationship_type = request.form.get('relationship_type')
        person_name = request.form.get('person_name')
        
        # Collect all answers
        answers = {}
        for key, value in request.form.items():
            if key.startswith('question_'):
                answers[key] = value
        
        # Analyze the relationship
        analysis_results = analyze_relationship(relationship_type, answers)
        
        # Store the relationship data
        relationship = Relationship(
            relationship_type=relationship_type,
            person_name=person_name,
            answers=json.dumps(answers)
        )
        db.session.add(relationship)
        db.session.commit()
        
        return render_template('results.html', 
                             person_name=person_name,
                             relationship_type=relationship_type,
                             analysis=analysis_results)
    
    return render_template('questionnaire.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    relationship_type = data.get('relationship_type')
    person_name = data.get('person_name')
    responses = data.get('responses', [])
    
    # Generate analysis
    analysis = analyze_relationship(relationship_type, responses)
    
    # Save the analysis
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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 