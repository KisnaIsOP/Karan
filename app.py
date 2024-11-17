from flask import Flask, render_template, request, jsonify, session
import google.generativeai as genai
from dotenv import load_dotenv
import os
import json
from datetime import datetime
import uuid

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-key-for-debug')

# Configure AI model
api_key = os.getenv('GOOGLE_API_KEY')
if not api_key:
    raise ValueError("No API key found. Please set GOOGLE_API_KEY environment variable.")

try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')
except Exception as e:
    print(f"Error configuring AI model: {str(e)}")
    raise

def get_system_prompt():
    return """You are Karan, a friendly and helpful AI assistant created by Kisna. Your responses should be:
    1. Helpful and informative
    2. Friendly and conversational
    3. Concise but complete
    4. Written in a natural, engaging style
    Remember to acknowledge that you were created by Kisna when relevant."""

@app.route('/')
def home():
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    return render_template('chat.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'No message provided'}), 400

        message = data['message'].strip()
        if not message:
            return jsonify({'error': 'Empty message'}), 400

        # Prepare conversation context
        context = get_system_prompt()
        prompt = f"{context}\n\nUser: {message}\nAssistant:"

        # Generate response
        response = model.generate_content(prompt)
        
        if not response or not response.text:
            return jsonify({'error': 'No response generated'}), 500

        return jsonify({
            'response': response.text,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=2000, host='0.0.0.0')
