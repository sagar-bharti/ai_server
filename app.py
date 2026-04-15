from flask import Flask, request, jsonify
import speech_recognition as sr
import os
import tempfile

app = Flask(__name__)

# Emergency keywords - Hindi + English
DANGER_KEYWORDS = [
    'help', 'bachao', 'madad', 'emergency', 
    'danger', 'chhodo', 'chodo', 'bachaa', 
    'save me', 'help me', 'koi hai', 'please help'
]

def detect_keywords(text):
    text_lower = text.lower()
    detected = []
    for word in DANGER_KEYWORDS:
        if word in text_lower:
            detected.append(word)
    return detected

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'message': 'AI Server running!'})

@app.route('/analyze', methods=['POST'])
def analyze_audio():
    try:
        # Audio file lo request se
        if 'audio' not in request.files:
            return jsonify({'error': 'Audio file nahi mila'}), 400

        audio_file = request.files['audio']
        
        # Temp file me save karo
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp:
            audio_file.save(tmp.name)
            tmp_path = tmp.name

        # Speech Recognition
        recognizer = sr.Recognizer()
        
        with sr.AudioFile(tmp_path) as source:
            recognizer.adjust_for_ambient_noise(source)
            audio_data = recognizer.record(source)

        # Cleanup temp file
        os.unlink(tmp_path)

        # Text me convert karo
        try:
            # Hindi + English dono try karo
            text = recognizer.recognize_google(
                audio_data, 
                language='hi-IN'  # Hindi primary
            )
        except sr.UnknownValueError:
            try:
                text = recognizer.recognize_google(
                    audio_data,
                    language='en-US'  # English fallback
                )
            except sr.UnknownValueError:
                return jsonify({
                    'success': True,
                    'text': '',
                    'emergency': False,
                    'message': 'Kuch samaj nahi aaya'
                })

        # Keywords detect karo
        keywords_found = detect_keywords(text)
        is_emergency = len(keywords_found) > 0

        print(f"Detected text: {text}")
        print(f"Emergency: {is_emergency}, Keywords: {keywords_found}")

        return jsonify({
            'success': True,
            'text': text,
            'emergency': is_emergency,
            'keywords_found': keywords_found,
            'message': f'Suna: {text}'
        })

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)