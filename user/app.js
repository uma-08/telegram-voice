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

// DOM Elements
const recordButton = document.getElementById('recordButton');
const recordingStatus = document.getElementById('recordingStatus');
const recordingTime = document.getElementById('recordingTime');
const volumeSlider = document.getElementById('volume');
const volumeValue = document.getElementById('volumeValue');
const recordingsContainer = document.getElementById('recordingsContainer');
const combineButton = document.getElementById('combineButton');

// Initialize volume slider
volumeSlider.addEventListener('input', (e) => {
    volumeValue.textContent = e.target.value;
});

// Recording functions
async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            const audioUrl = URL.createObjectURL(audioBlob);
            const duration = (Date.now() - recordingStartTime) / 1000;
            
            // Add to recordings list
            recordings.push({
                audioUrl,
                duration,
                tag: TAG_OPTIONS[0],
                timestamp: new Date().toISOString()
            });
            
            // Update UI
            updateRecordingsList();
            
            // Send to Telegram
            tg.sendData(JSON.stringify({
                type: 'recording',
                audio: await blobToBase64(audioBlob),
                duration,
                tag: TAG_OPTIONS[0]
            }));
        };

        mediaRecorder.start();
        isRecording = true;
        recordingStartTime = Date.now();
        updateRecordingUI();
    } catch (error) {
        console.error('Error accessing microphone:', error);
        tg.showAlert('Error accessing microphone. Please check permissions.');
    }
}

function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        isRecording = false;
        clearInterval(recordingTimer);
        updateRecordingUI();
    }
}

function updateRecordingUI() {
    if (isRecording) {
        recordButton.textContent = 'Stop Recording';
        recordButton.classList.add('recording');
        recordingStatus.classList.remove('hidden');
        recordingTimer = setInterval(() => {
            const elapsed = (Date.now() - recordingStartTime) / 1000;
            recordingTime.textContent = elapsed.toFixed(1);
        }, 100);
    } else {
        recordButton.textContent = 'Start Recording';
        recordButton.classList.remove('recording');
        recordingStatus.classList.add('hidden');
    }
}

function updateRecordingsList() {
    recordingsContainer.innerHTML = recordings.map((rec, index) => `
        <div class="recording-item">
            <div class="tag">${rec.tag}</div>
            <audio controls src="${rec.audioUrl}"></audio>
            <div>Duration: ${rec.duration.toFixed(1)}s</div>
            <select onchange="updateTag(${index}, this.value)">
                ${TAG_OPTIONS.map(tag => 
                    `<option value="${tag}" ${rec.tag === tag ? 'selected' : ''}>${tag}</option>`
                ).join('')}
            </select>
        </div>
    `).join('');
}

function updateTag(index, newTag) {
    recordings[index].tag = newTag;
    tg.sendData(JSON.stringify({
        type: 'update_tag',
        index,
        tag: newTag
    }));
}

async function combineRecordings() {
    if (recordings.length === 0) {
        tg.showAlert('No recordings to combine');
        return;
    }

    // Send combine request to Telegram
    tg.sendData(JSON.stringify({
        type: 'combine_recordings',
        recordings: recordings.map(rec => ({
            audioUrl: rec.audioUrl,
            tag: rec.tag
        }))
    }));
}

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