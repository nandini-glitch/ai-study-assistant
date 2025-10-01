const API_URL = 'http://localhost:5001';
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
            // Limit display length for analysis
            const partial = data.analysis ? data.analysis.substring(0, 150) : '';
            showStatus('imageStatus', `${data.message}\n${partial}...`);
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
            // Put transcription into question input
            document.getElementById('questionInput').value = data.transcription || '';
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
        const response = await fetch(`${API_URL}/summary`, {
            method: 'POST'
        });
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
        const response = await fetch(`${API_URL}/clear`, {
            method: 'POST'
        });
        const data = await response.json();
        
        if (response.ok && data.success) {
            alert(data.message);
            document.getElementById('questionInput').value = '';
            document.getElementById('answerSection').style.display = 'none';
        } else {
            alert(`Error: ${data.error}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
    hideLoading();
}
