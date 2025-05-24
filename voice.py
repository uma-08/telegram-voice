
import streamlit as st
import numpy as np
import time
import os
import wave
import assemblyai as aai
from dotenv import load_dotenv
import uuid
from audio_recorder_streamlit import audio_recorder

# Load environment variables
load_dotenv()

# Configuration
SAMPLE_RATE = 44100  # Sample rate (Hz)
CHANNELS = 1         # Mono audio
RECORDINGS_DIR = "recordings"
COMBINED_DIR = "combined"
TAG_OPTIONS = ["💖 Personal", "❓ Question", "⚡ Priority", "😎 Chill"]

# Ensure directories exist
os.makedirs(RECORDINGS_DIR, exist_ok=True)
os.makedirs(COMBINED_DIR, exist_ok=True)

# Initialize session state defaults
defaults = {
    'recordings': [],
    'api_key': os.getenv('ASSEMBLY_API_KEY', ''),
    'debug': []
}
for key, default in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default
if 'combine_selection' not in st.session_state:
    st.session_state.combine_selection = set()

# Debug logging


def add_debug(msg):
    st.session_state.debug.append(f"{time.strftime('%H:%M:%S')}: {msg}")

# Transcribe audio via AssemblyAI


def transcribe_audio(audio_bytes, api_key):
    if not api_key:
        add_debug("No API key for transcription")
        return ''

    # Save audio bytes to a temporary file
    temp_path = os.path.join(
        RECORDINGS_DIR, f"temp_{uuid.uuid4().hex[:8]}.wav")
    with open(temp_path, 'wb') as f:
        f.write(audio_bytes)

    try:
        aai.settings.api_key = api_key
        add_debug("Transcribing audio")
        transcriber = aai.Transcriber()
        result = transcriber.transcribe(temp_path)
        text = getattr(result, 'text', '') or 'No transcription'
        add_debug(f"Received transcription ({len(text)} chars)")
        return text
    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)

# Combine recordings into one WAV


def combine_audio_files():
    selected_indices = st.session_state.combine_selection
    if not selected_indices:
        add_debug("No recordings selected for combining")
        return None

    segments = []
    for idx in selected_indices:
        rec = st.session_state.recordings[idx]
        try:
            with wave.open(rec['filepath'], 'rb') as wf:
                data = wf.readframes(wf.getnframes())
                arr = np.frombuffer(data, dtype=np.int16)
                segments.append(arr)
        except Exception as e:
            add_debug(f"Error reading {rec['filepath']}: {e}")

    if not segments:
        return None

    combined = np.concatenate(segments)
    filename = f"combined_{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.wav"
    out_path = os.path.join(COMBINED_DIR, filename)
    with wave.open(out_path, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(combined.tobytes())
    add_debug(f"Combined WAV saved: {out_path}")
    return out_path

# Callback for tag changes


def on_tag_change(idx):
    new = st.session_state[f"tag_{idx}"]
    st.session_state.recordings[idx]['tag'] = new
    add_debug(f"Recording {idx+1} tagged as {new}")


# App UI
st.title("🎙️ Voice Recorder with Tags")

# API Key Input
with st.expander("API Settings", expanded=False):
    key = st.text_input(
        "AssemblyAI API Key", value=st.session_state.api_key, type='password'
    )
    if key != st.session_state.api_key:
        st.session_state.api_key = key
        add_debug("API key updated")

# Recording Controls
st.subheader("Record Audio")
audio_bytes = audio_recorder(
    text="Click to record",
    recording_color="#e74c3c",
    neutral_color="#3498db",
    key="audio_recorder"
)

if audio_bytes:
    # Save the recording
    fname = f"recording_{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.wav"
    fpath = os.path.join(RECORDINGS_DIR, fname)
    with open(fpath, 'wb') as f:
        f.write(audio_bytes)

    add_debug(f"Saved WAV: {fpath}")
    st.audio(audio_bytes)

    with st.spinner("Transcribing..."):
        txt = transcribe_audio(audio_bytes, st.session_state.api_key)
    st.success("Transcription complete 🎉")
    st.write(f"📝 {txt}")

    st.session_state.recordings.append({
        'filepath': fpath,
        # Approximate duration
        'duration': len(audio_bytes) / (SAMPLE_RATE * 2),
        'text': txt,
        'tag': TAG_OPTIONS[0]
    })

# Combine Selected Recordings Button
selected_count = len(st.session_state.combine_selection)
button_text = f"Combine Selected ({selected_count})" if selected_count > 0 else "Select recordings to combine"
if st.button(button_text, use_container_width=True, disabled=selected_count == 0):
    combined_path = combine_audio_files()
    if combined_path:
        st.success(f"Combined audio saved: {combined_path}")
        st.audio(combined_path)
    else:
        st.warning("Failed to combine recordings")

# List recordings with tag selector
st.markdown("---")
total = len(st.session_state.recordings)
for rev_idx, rec in enumerate(reversed(st.session_state.recordings)):
    orig_idx = total - 1 - rev_idx

    # Add selection checkbox
    col1, col2 = st.columns([1, 10])
    with col1:
        if st.checkbox("", key=f"select_{orig_idx}"):
            st.session_state.combine_selection.add(orig_idx)
        else:
            st.session_state.combine_selection.discard(orig_idx)

    with col2:
        st.subheader(f"Recording {orig_idx+1}")
        # Show tag badge
        badge = rec.get('tag', TAG_OPTIONS[0])
        st.markdown(
            f"<span style='background-color:#444;color:#fff;padding:4px 8px;border-radius:4px;'>{badge}</span>",
            unsafe_allow_html=True
        )
        # Audio + details
        st.audio(rec['filepath'])
        st.write(f"⏱️ Duration: {rec.get('duration', 0):.2f}s")
        st.write(f"📝 {rec.get('text', '')}")
        # Tag dropdown with on_change callback
        st.selectbox(
            "Change Tag", TAG_OPTIONS,
            index=TAG_OPTIONS.index(badge),
            key=f"tag_{orig_idx}",
            on_change=on_tag_change,
            args=(orig_idx,)
        )

# Debug log
with st.expander("Debug Log", expanded=False):
    for msg in st.session_state.debug:
        st.write(msg)
