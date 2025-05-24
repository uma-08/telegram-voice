# Voice Recorder with Tags

A Streamlit application for recording, transcribing, and organizing voice notes with tags.

## Features
- Voice recording with adjustable input volume
- Real-time transcription using AssemblyAI
- Tag management for recordings
- Combine multiple recordings
- Debug logging

## Deployment to Streamlit Cloud

1. Push this repository to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Sign in with your GitHub account
4. Click "New app"
5. Select your repository
6. Set the main file path to `voice_recorder_enhanced_mic.py`
7. Add your AssemblyAI API key in the secrets management section
8. Deploy!

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your AssemblyAI API key:
```
ASSEMBLY_API_KEY=your-api-key-here
```

3. Run the app:
```bash
streamlit run voice_recorder_enhanced_mic.py
``` 