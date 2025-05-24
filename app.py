from flask import Flask, request, jsonify, send_file
import os
import wave
import numpy as np
import assemblyai as aai
from dotenv import load_dotenv
import uuid
import io
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration
SAMPLE_RATE = 44100
CHANNELS = 1
RECORDINGS_DIR = "recordings"
COMBINED_DIR = "combined"

# Ensure directories exist
os.makedirs(RECORDINGS_DIR, exist_ok=True)
os.makedirs(COMBINED_DIR, exist_ok=True)

# Initialize AssemblyAI
aai.settings.api_key = os.getenv('ASSEMBLY_API_KEY')

@app.route('/api/recordings', methods=['POST'])
def save_recording():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    audio_file = request.files['audio']
    tag = request.form.get('tag', '💖 Personal')
    
    # Generate unique filename
    filename = f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.wav"
    filepath = os.path.join(RECORDINGS_DIR, filename)
    
    # Save the audio file
    audio_file.save(filepath)
    
    # Transcribe the audio
    try:
        transcriber = aai.Transcriber()
        result = transcriber.transcribe(filepath)
        transcription = getattr(result, 'text', '') or 'No transcription'
    except Exception as e:
        transcription = f'Transcription error: {str(e)}'
    
    return jsonify({
        'success': True,
        'filename': filename,
        'transcription': transcription
    })

@app.route('/api/combine', methods=['POST'])
def combine_recordings():
    data = request.json
    recording_ids = data.get('recordingIds', [])
    
    if not recording_ids:
        return jsonify({'error': 'No recordings selected'}), 400
    
    segments = []
    for recording_id in recording_ids:
        filepath = os.path.join(RECORDINGS_DIR, f"recording_{recording_id}.wav")
        if not os.path.exists(filepath):
            continue
            
        try:
            with wave.open(filepath, 'rb') as wf:
                data = wf.readframes(wf.getnframes())
                arr = np.frombuffer(data, dtype=np.int16)
                segments.append(arr)
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
    
    if not segments:
        return jsonify({'error': 'No valid recordings to combine'}), 400
    
    # Combine audio segments
    combined = np.concatenate(segments)
    filename = f"combined_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.wav"
    out_path = os.path.join(COMBINED_DIR, filename)
    
    with wave.open(out_path, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(combined.tobytes())
    
    return jsonify({
        'success': True,
        'filename': filename,
        'audioUrl': f'/api/audio/{filename}'
    })

@app.route('/api/audio/<filename>')
def get_audio(filename):
    filepath = os.path.join(COMBINED_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'Audio file not found'}), 404
    return send_file(filepath, mimetype='audio/wav')

if __name__ == '__main__':
    app.run(debug=True, port=5000) 