from flask import Flask, render_template, request, jsonify
from analyze_chat import analyze_chat

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    text = request.json.get('text', '')
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    score = analyze_chat(text)
    if score is None:
        return jsonify({'error': 'Failed to analyze text'}), 500
    
    return jsonify({
        'score': score,
        'text': text
    })

if __name__ == '__main__':
    app.run(debug=True) 