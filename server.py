from flask import Flask, request, jsonify
import os
import wave
import numpy as np
import base64
from telegram import Bot
from dotenv import load_dotenv
import uuid
import tempfile

# Load environment variables
load_dotenv()

app = Flask(__name__)
bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))

# Constants
SAMPLE_RATE = 44100
CHANNELS = 1

@app.route('/')
def home():
    return jsonify({"status": "ok", "message": "Voice Recorder Backend is running"})

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        if not data:
            return jsonify({'status': 'error', 'message': 'No data received'}), 400
        
        if data['type'] == 'recording':
            # Save the recording
            audio_data = base64.b64decode(data['audio'])
            filename = f"recording_{uuid.uuid4().hex}.wav"
            filepath = os.path.join('recordings', filename)
            
            with open(filepath, 'wb') as f:
                f.write(audio_data)
                
            # Process the recording (e.g., transcribe)
            # Add your transcription logic here
            
            return jsonify({'status': 'success'})
            
        elif data['type'] == 'combine_recordings':
            # Combine multiple recordings
            recordings = data['recordings']
            segments = []
            
            for rec in recordings:
                audio_data = base64.b64decode(rec['audio'])
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp:
                    temp.write(audio_data)
                    temp_path = temp.name
                
                with wave.open(temp_path, 'rb') as wf:
                    data = wf.readframes(wf.getnframes())
                    arr = np.frombuffer(data, dtype=np.int16)
                    segments.append(arr)
                
                os.unlink(temp_path)
            
            if segments:
                combined = np.concatenate(segments)
                combined_filename = f"combined_{uuid.uuid4().hex}.wav"
                combined_path = os.path.join('recordings', combined_filename)
                
                with wave.open(combined_path, 'wb') as wf:
                    wf.setnchannels(CHANNELS)
                    wf.setsampwidth(2)
                    wf.setframerate(SAMPLE_RATE)
                    wf.writeframes(combined.tobytes())
                
                # Read the combined file and convert to base64
                with open(combined_path, 'rb') as f:
                    combined_base64 = base64.b64encode(f.read()).decode('utf-8')
                
                return jsonify({
                    'type': 'combined_audio',
                    'audio': combined_base64
                })
        
        return jsonify({'status': 'error', 'message': 'Invalid request type'}), 400
    
    except Exception as e:
        app.logger.error(f"Error processing request: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    # Create recordings directory if it doesn't exist
    os.makedirs('recordings', exist_ok=True)
    
    # Run the Flask app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 