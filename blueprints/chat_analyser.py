from flask import Blueprint, render_template, request, jsonify
import os
import sys
from PIL import Image
import pytesseract
import io

# Ensure the chat analyser module is importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../chat analyser/chat analyser')))
from analyze_chat import analyze_chat

chat_analyser_bp = Blueprint(
    'chat_analyser',
    __name__,
    template_folder='../chat analyser/chat analyser/templates',
    static_folder=None
)

@chat_analyser_bp.route('/', methods=['GET'])
def home():
    return render_template('chat_analyser_index.html')

@chat_analyser_bp.route('/analyze', methods=['POST'])
def analyze():
    text = request.json.get('text', '')
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    score = analyze_chat(text)
    if score is None:
        return jsonify({'error': 'Failed to analyze text'}), 500
    return jsonify({'score': score, 'text': text})

@chat_analyser_bp.route('/ocr-analyze', methods=['POST'])
def ocr_analyze():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
    image_file = request.files['image']
    try:
        image = Image.open(image_file.stream)
        extracted_text = pytesseract.image_to_string(image)
        score = analyze_chat(extracted_text)
        return jsonify({'score': score, 'text': extracted_text})
    except Exception as e:
        return jsonify({'error': f'Failed to process image: {str(e)}'}), 500 