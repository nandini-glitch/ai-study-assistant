// Auto-detect environment and set API URL
const API_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:5001'  // Local development
    : 'https://ai-study-assistant-mk69.onrender.com';  // Production - UPDATE THIS AFTER DEPLOYMENT

let currentAnswer = '';

function showLoading() {
    document.getElementById('loading').style.display = 'block';
}

function hideLoading() {
    document.getElementById('loading').style.display = 'none';
}

function showStatus(elementId, message, isError = false) {
    const statusEl = document.getElementById(elementId);
    statusEl.textContent = message;
    statusEl.className = isError ? 'status error' : 'status success';
    setTimeout(() => {
        statusEl.textContent = '';
        statusEl.className = 'status';
    }, 8000);
}

async function uploadDocument() {
    const fileInput = document.getElementById('documentInput');
    const file = fileInput.files[0];
    
    if (!file) {
        showStatus('documentStatus', '✗ Select a file first', true);
        return;
    }
    
    showLoading();
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch(`${API_URL}/upload/document`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            showStatus('documentStatus', `${data.message}\n${data.text_length} characters`);
            fileInput.value = '';
        } else {
            showStatus('documentStatus', `✗ ${data.error}`, true);
        }
    } catch (error) {
        showStatus('documentStatus', `✗ ${error.message}`, true);
    }
    hideLoading();
}

async function uploadImage() {
    const fileInput = document.getElementById('imageInput');
    const file = fileInput.files[0];
    
    if (!file) {
        showStatus('imageStatus', '✗ Select an image first', true);
        return;
    }
    
    showLoading();
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch(`${API_URL}/upload/image`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            showStatus('imageStatus', `${data.message}\n${data.analysis.substring(0, 150)}...`);
            fileInput.value = '';
        } else {
            showStatus('imageStatus', `✗ ${data.error}`, true);
        }
    } catch (error) {
        showStatus('imageStatus', `✗ ${error.message}`, true);
    }
    hideLoading();
}

async function uploadAudio() {
    const fileInput = document.getElementById('audioInput');
    const file = fileInput.files[0];
    
    if (!file) {
        showStatus('audioStatus', '✗ Select audio first', true);
        return;
    }
    
    showLoading();
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch(`${API_URL}/upload/audio`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            showStatus('audioStatus', `✓ ${data.message}`);
            document.getElementById('questionInput').value = data.transcription;
            fileInput.value = '';
        } else {
            showStatus('audioStatus', `✗ ${data.error}`, true);
        }
    } catch (error) {
        showStatus('audioStatus', `✗ ${error.message}`, true);
    }
    hideLoading();
}

async function askQuestion() {
    const question = document.getElementById('questionInput').value.trim();
    
    if (!question) {
        alert('Enter a question');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch(`${API_URL}/ask`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            currentAnswer = data.answer;
            document.getElementById('answerContent').textContent = data.answer;
            document.getElementById('answerSection').style.display = 'block';
            document.getElementById('audioPlayer').style.display = 'none';
            document.getElementById('answerSection').scrollIntoView({ behavior: 'smooth' });
        } else {
            alert(`Error: ${data.error}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
    hideLoading();
}

async function speakAnswer() {
    if (!currentAnswer) {
        alert('No answer to speak');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch(`${API_URL}/speak`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: currentAnswer })
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const audioUrl = URL.createObjectURL(blob);
            const audioPlayer = document.getElementById('audioPlayer');
            audioPlayer.src = audioUrl;
            audioPlayer.style.display = 'block';
            audioPlayer.play();
        } else {
            alert('Speech generation error');
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
    hideLoading();
}

async function generateSummary() {
    showLoading();
    
    try {
        const response = await fetch(`${API_URL}/summary`, { method: 'POST' });
        const data = await response.json();
        
        if (response.ok && data.success) {
            currentAnswer = data.summary;
            document.getElementById('answerContent').textContent = data.summary;
            document.getElementById('answerSection').style.display = 'block';
            document.getElementById('audioPlayer').style.display = 'none';
            document.getElementById('answerSection').scrollIntoView({ behavior: 'smooth' });
        } else {
            alert(`Error: ${data.error}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
    hideLoading();
}

async function clearMaterials() {
    if (!confirm('Clear all materials?')) return;
    
    showLoading();
    
    try {
        const response = await fetch(`${API_URL}/clear`, { method: 'POST' });
        const data = await response.json();
        
        if (response.ok && data.success) {
            alert(data.message);
            document.getElementById('questionInput').value = '';
            document.getElementById('answerSection').style.display = 'none';
            currentAnswer = '';
            ['documentStatus', 'imageStatus', 'audioStatus'].forEach(id => {
                document.getElementById(id).textContent = '';
                document.getElementById(id).className = 'status';
            });
        } else {
            alert(`Error: ${data.error}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
    hideLoading();
}

document.getElementById('questionInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        askQuestion();
    }
});

// Check API connection on load
window.addEventListener('load', async () => {
    console.log('Connecting to API:', API_URL);
    try {
        const response = await fetch(`${API_URL}/health`);
        const data = await response.json();
        console.log('API Status:', data);
    } catch (error) {
        console.error('Cannot connect to API:', error);
        alert('Warning: Cannot connect to backend. Make sure the server is running.');
    }
});