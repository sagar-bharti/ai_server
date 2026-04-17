import os
import tempfile
import whisper
from flask import Flask, request, jsonify

app = Flask(__name__)

# Server start hote hi model load karo (ek baar)
print("Loading Whisper model...")
model = whisper.load_model("tiny")
print("Model loaded! Server ready.")

EMERGENCY_KEYWORDS = [
    # English
    "help", "help me", "save me", "emergency",
    # Hindi roman
    "bachao", "madad", "bachao mujhe", "madad karo",
    "help karo", "bachaa lo", "koi hai", "please help",
    # Hindi devanagari (whisper kabhi kabhi yeh return karta hai)
    "बचाओ", "मदद", "मदद करो", "बचाओ मुझे"
]

def detect_keywords(text):
    if not text:
        return False, []
    text_lower = text.lower().strip()
    found = [kw for kw in EMERGENCY_KEYWORDS if kw in text_lower]
    return len(found) > 0, found

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "ok",
        "model": "whisper-tiny"
    })

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        if 'audio' not in request.files:
            return jsonify({"emergency": False, "error": "no_audio_file"}), 400

        audio_file = request.files['audio']
        audio_bytes = audio_file.read()

        if len(audio_bytes) == 0:
            return jsonify({"emergency": False, "error": "empty_audio"}), 400

        print(f"Audio received: {len(audio_bytes)} bytes")

        # Temp file mein save karo
        with tempfile.NamedTemporaryFile(suffix=".m4a", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            # Whisper se transcribe karo
            result = model.transcribe(
                tmp_path,
                language=None,   # auto-detect Hindi + English
                fp16=False,      # Render CPU pe fp16 nahi chalega
                temperature=0.0  # deterministic
            )
            transcript = result.get("text", "").strip()
            detected_lang = result.get("language", "unknown")

            print(f"Transcript: '{transcript}' | Language: {detected_lang}")

            is_emergency, keywords_found = detect_keywords(transcript)

            return jsonify({
                "emergency": is_emergency,
                "transcript": transcript,
                "language": detected_lang,
                "keywords_found": keywords_found
            })

        finally:
            os.unlink(tmp_path)

    except Exception as e:
        print(f"Error in /analyze: {e}")
        return jsonify({"emergency": False, "error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)