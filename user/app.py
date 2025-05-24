import streamlit as st
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

# Constants
SAMPLE_RATE = 44100
CHANNELS = 1

# Initialize session state
if 'recordings' not in st.session_state:
    st.session_state.recordings = []

def save_recording(audio_data, filename):
    """Save audio data to a WAV file"""
    filepath = os.path.join('recordings', filename)
    with open(filepath, 'wb') as f:
        f.write(audio_data)
    return filepath

def combine_recordings(recordings):
    """Combine multiple recordings into one"""
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
        
        return combined_path
    return None

# Create recordings directory if it doesn't exist
os.makedirs('recordings', exist_ok=True)

# App title and description
st.title("🎙️ Voice Recorder")
st.write("Record and combine voice messages easily!")

# Recording controls
col1, col2 = st.columns(2)
with col1:
    if st.button("Start Recording", key="record"):
        st.audio("recording.wav", format="audio/wav")
        # Here you would implement the actual recording logic
        # For now, we'll use a placeholder

with col2:
    if st.button("Stop Recording", key="stop"):
        st.success("Recording saved!")

# Volume control
volume = st.slider("Input Volume", 0.1, 5.0, 1.0, 0.1)

# Recordings list
st.subheader("Your Recordings")
for i, rec in enumerate(st.session_state.recordings):
    st.audio(rec['audio'], format="audio/wav")
    st.write(f"Duration: {rec['duration']:.1f}s")
    
    # Tag selection
    tag = st.selectbox(
        f"Tag for recording {i+1}",
        ["💖 Personal", "❓ Question", "⚡ Priority", "😎 Chill"],
        key=f"tag_{i}"
    )
    
    if st.button("Delete", key=f"delete_{i}"):
        st.session_state.recordings.pop(i)
        st.rerun()

# Combine recordings
if st.button("Combine All Recordings"):
    if len(st.session_state.recordings) > 0:
        combined_path = combine_recordings(st.session_state.recordings)
        if combined_path:
            st.audio(combined_path, format="audio/wav")
            st.success("Recordings combined successfully!")
    else:
        st.warning("No recordings to combine!")

# Footer
st.markdown("---")
st.markdown("Made with ❤️ using Streamlit") 