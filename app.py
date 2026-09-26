from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from anthropic import Anthropic
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)
client = Anthropic()

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/compress', methods=['POST'])
def compress():
    data = request.json
    prompt = data.get('prompt', '')
    
    if not prompt:
        return jsonify({'error': 'No prompt provided'}), 400
    
    try:
        response = client.messages.create(
            model="claude-3-5-haiku-20250514",
            max_tokens=400,
            messages=[{
                "role": "user",
                "content": f"Remove all verbose/filler words. Keep technical requirements only.\n\n{prompt}"
            }]
        )
        compressed = response.content[0].text.strip()
        ratio = 1 - (len(compressed) / len(prompt)) if len(compressed) < len(prompt) else 0
        
        return jsonify({
            'original': prompt,
            'compressed': compressed,
            'compression': round(ratio * 100, 1),
            'original_length': len(prompt),
            'compressed_length': len(compressed)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
