// Initialize Telegram WebApp
const tg = window.Telegram.WebApp;
tg.expand();

// Constants
const SAMPLE_RATE = 44100;
const CHANNELS = 1;
const TAG_OPTIONS = ["💖 Personal", "❓ Question", "⚡ Priority", "😎 Chill"];

// State
let isRecording = false;
let mediaRecorder = null;
let audioChunks = [];
let recordings = [];
let recordingStartTime = 0;
let recordingTimer = null;
let selectedRecordings = new Set();

// DOM Elements
const recordButton = document.getElementById('recordButton');
const recordingStatus = document.getElementById('recordingStatus');
const recordingTime = document.getElementById('recordingTime');
const volumeSlider = document.getElementById('volume');
const volumeValue = document.getElementById('volumeValue');
const recordingsContainer = document.getElementById('recordingsContainer');
const combineButton = document.getElementById('combineButton');
const recordingsList = document.getElementById('recordingsList');
const tagSelect = document.getElementById('tagSelect');

// Initialize volume slider
volumeSlider.addEventListener('input', (e) => {
    volumeValue.textContent = e.target.value;
});

// Initialize recording functionality
async function initializeRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        
        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            const audioUrl = URL.createObjectURL(audioBlob);
            
            // Create recording object
            const recording = {
                id: Date.now(),
                audioUrl,
                tag: tagSelect.value,
                timestamp: new Date().toISOString()
            };
            
            recordings.push(recording);
            addRecordingToList(recording);
            
            // Send to backend
            await sendRecordingToServer(audioBlob, recording);
            
            // Reset for next recording
            audioChunks = [];
        };
    } catch (error) {
        console.error('Error accessing microphone:', error);
        recordingStatus.textContent = 'Error accessing microphone';
    }
}

// Recording controls
recordButton.addEventListener('click', () => {
    if (!mediaRecorder) {
        initializeRecording();
        return;
    }

    if (mediaRecorder.state === 'inactive') {
        // Start recording
        mediaRecorder.start();
        recordButton.textContent = 'Stop Recording';
        recordButton.classList.add('recording');
        recordingStatus.textContent = 'Recording...';
    } else {
        // Stop recording
        mediaRecorder.stop();
        recordButton.textContent = 'Start Recording';
        recordButton.classList.remove('recording');
        recordingStatus.textContent = 'Processing...';
    }
});

// Add recording to list
function addRecordingToList(recording) {
    const div = document.createElement('div');
    div.className = 'recording-item';
    div.innerHTML = `
        <div class="recording-header">
            <input type="checkbox" class="recording-checkbox" data-id="${recording.id}">
            <span class="recording-tag">${recording.tag}</span>
        </div>
        <audio controls src="${recording.audioUrl}"></audio>
        <div class="recording-time">${new Date(recording.timestamp).toLocaleString()}</div>
    `;
    
    // Add checkbox handler
    const checkbox = div.querySelector('.recording-checkbox');
    checkbox.addEventListener('change', (e) => {
        if (e.target.checked) {
            selectedRecordings.add(recording.id);
        } else {
            selectedRecordings.delete(recording.id);
        }
        updateCombineButton();
    });
    
    recordingsList.insertBefore(div, recordingsList.firstChild);
}

// Update combine button state
function updateCombineButton() {
    combineButton.disabled = selectedRecordings.size === 0;
}

// Send recording to server
async function sendRecordingToServer(audioBlob, recording) {
    const formData = new FormData();
    formData.append('audio', audioBlob);
    formData.append('tag', recording.tag);
    
    try {
        const response = await fetch('/api/recordings', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Failed to save recording');
        }
        
        const result = await response.json();
        recordingStatus.textContent = 'Recording saved!';
    } catch (error) {
        console.error('Error saving recording:', error);
        recordingStatus.textContent = 'Error saving recording';
    }
}

// Combine selected recordings
combineButton.addEventListener('click', async () => {
    if (selectedRecordings.size === 0) return;
    
    try {
        const response = await fetch('/api/combine', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                recordingIds: Array.from(selectedRecordings)
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to combine recordings');
        }
        
        const result = await response.json();
        // Handle combined audio
        const audioUrl = result.audioUrl;
        const audio = new Audio(audioUrl);
        audio.play();
        
        // Clear selection
        selectedRecordings.clear();
        updateCombineButton();
        document.querySelectorAll('.recording-checkbox').forEach(cb => cb.checked = false);
        
    } catch (error) {
        console.error('Error combining recordings:', error);
        recordingStatus.textContent = 'Error combining recordings';
    }
});

// Initialize the app
initializeRecording();

// Utility function to convert Blob to base64
function blobToBase64(blob) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve(reader.result.split(',')[1]);
        reader.onerror = reject;
        reader.readAsDataURL(blob);
    });
}

// Event Listeners
recordButton.addEventListener('click', () => {
    if (isRecording) {
        stopRecording();
    } else {
        startRecording();
    }
});

combineButton.addEventListener('click', combineRecordings);

// Handle messages from Telegram
tg.onEvent('message', (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'combined_audio') {
        // Handle combined audio response
        const audioUrl = `data:audio/wav;base64,${data.audio}`;
        recordingsContainer.innerHTML += `
            <div class="recording-item">
                <div class="tag">Combined Recording</div>
                <audio controls src="${audioUrl}"></audio>
            </div>
        `;
    }
}); 