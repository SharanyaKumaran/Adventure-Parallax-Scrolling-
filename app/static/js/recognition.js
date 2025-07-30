class SignLanguageRecognition {
    constructor() {
        this.video = document.getElementById('videoElement');
        this.canvas = document.getElementById('canvasElement');
        this.ctx = this.canvas.getContext('2d');
        this.stream = null;
        this.recognitionActive = false;
        this.sessionStartTime = null;
        this.gestureCount = 0;
        this.sessionTimer = null;
        this.recognitionInterval = null;
        
        this.initializeElements();
        this.bindEvents();
    }
    
    initializeElements() {
        this.elements = {
            startCamera: document.getElementById('startCamera'),
            stopCamera: document.getElementById('stopCamera'),
            toggleRecognition: document.getElementById('toggleRecognition'),
            statusOverlay: document.getElementById('statusOverlay'),
            currentGesture: document.getElementById('currentGesture'),
            confidence: document.getElementById('confidence'),
            accumulatedText: document.getElementById('accumulatedText'),
            clearText: document.getElementById('clearText'),
            speakText: document.getElementById('speakText'),
            gestureCount: document.getElementById('gestureCount'),
            sessionTime: document.getElementById('sessionTime'),
            confidenceThreshold: document.getElementById('confidenceThreshold'),
            thresholdValue: document.getElementById('thresholdValue'),
            speechRate: document.getElementById('speechRate'),
            rateValue: document.getElementById('rateValue'),
            speechVolume: document.getElementById('speechVolume'),
            volumeValue: document.getElementById('volumeValue'),
            autoSpeak: document.getElementById('autoSpeak'),
            loadingModal: new bootstrap.Modal(document.getElementById('loadingModal'))
        };
    }
    
    bindEvents() {
        this.elements.startCamera.addEventListener('click', () => this.startCamera());
        this.elements.stopCamera.addEventListener('click', () => this.stopCamera());
        this.elements.toggleRecognition.addEventListener('click', () => this.toggleRecognition());
        this.elements.clearText.addEventListener('click', () => this.clearText());
        this.elements.speakText.addEventListener('click', () => this.speakAccumulatedText());
        
        // Settings sliders
        this.elements.confidenceThreshold.addEventListener('input', (e) => {
            this.elements.thresholdValue.textContent = e.target.value + '%';
        });
        
        this.elements.speechRate.addEventListener('input', (e) => {
            this.elements.rateValue.textContent = e.target.value;
            this.updateTTSSettings();
        });
        
        this.elements.speechVolume.addEventListener('input', (e) => {
            this.elements.volumeValue.textContent = e.target.value + '%';
            this.updateTTSSettings();
        });
        
        // Handle page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.hidden && this.recognitionActive) {
                this.pauseRecognition();
            }
        });
        
        // Handle window beforeunload
        window.addEventListener('beforeunload', () => {
            this.cleanup();
        });
    }
    
    async startCamera() {
        try {
            this.elements.loadingModal.show();
            
            // Request camera access
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    facingMode: 'user'
                },
                audio: false
            });
            
            this.video.srcObject = this.stream;
            
            // Wait for video to load
            await new Promise((resolve) => {
                this.video.addEventListener('loadedmetadata', resolve, { once: true });
            });
            
            this.elements.statusOverlay.style.display = 'none';
            this.elements.startCamera.disabled = true;
            this.elements.stopCamera.disabled = false;
            this.elements.toggleRecognition.disabled = false;
            
            this.showToast('Camera started successfully!', 'success');
            
        } catch (error) {
            console.error('Error accessing camera:', error);
            this.showToast('Failed to access camera. Please check permissions.', 'error');
        } finally {
            this.elements.loadingModal.hide();
        }
    }
    
    stopCamera() {
        if (this.stream) {
            // Stop recognition first
            if (this.recognitionActive) {
                this.stopRecognition();
            }
            
            // Stop all tracks
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
            this.video.srcObject = null;
            
            this.elements.statusOverlay.style.display = 'flex';
            this.elements.startCamera.disabled = false;
            this.elements.stopCamera.disabled = true;
            this.elements.toggleRecognition.disabled = true;
            
            this.showToast('Camera stopped', 'info');
        }
    }
    
    async toggleRecognition() {
        if (this.recognitionActive) {
            this.stopRecognition();
        } else {
            await this.startRecognition();
        }
    }
    
    async startRecognition() {
        try {
            this.elements.loadingModal.show();
            
            // Start session tracking
            await this.startSession();
            
            this.recognitionActive = true;
            this.sessionStartTime = Date.now();
            this.gestureCount = 0;
            
            // Update UI
            this.elements.toggleRecognition.innerHTML = '<i class="fas fa-stop me-2"></i>Stop Recognition';
            this.elements.toggleRecognition.classList.remove('btn-primary');
            this.elements.toggleRecognition.classList.add('btn-danger');
            this.video.classList.add('recognition-active');
            
            // Start recognition loop
            this.recognitionInterval = setInterval(() => {
                this.processFrame();
            }, 200); // Process every 200ms
            
            // Start session timer
            this.sessionTimer = setInterval(() => {
                this.updateSessionTime();
            }, 1000);
            
            this.showToast('Recognition started!', 'success');
            
        } catch (error) {
            console.error('Error starting recognition:', error);
            this.showToast('Failed to start recognition', 'error');
        } finally {
            this.elements.loadingModal.hide();
        }
    }
    
    stopRecognition() {
        this.recognitionActive = false;
        
        // Clear intervals
        if (this.recognitionInterval) {
            clearInterval(this.recognitionInterval);
            this.recognitionInterval = null;
        }
        
        if (this.sessionTimer) {
            clearInterval(this.sessionTimer);
            this.sessionTimer = null;
        }
        
        // End session
        this.endSession();
        
        // Update UI
        this.elements.toggleRecognition.innerHTML = '<i class="fas fa-brain me-2"></i>Start Recognition';
        this.elements.toggleRecognition.classList.remove('btn-danger');
        this.elements.toggleRecognition.classList.add('btn-primary');
        this.video.classList.remove('recognition-active');
        
        // Reset current gesture display
        this.elements.currentGesture.textContent = '--';
        this.elements.confidence.textContent = 'Confidence: 0%';
        
        this.showToast('Recognition stopped', 'info');
    }
    
    async processFrame() {
        if (!this.recognitionActive || !this.stream) return;
        
        try {
            // Draw current video frame to canvas
            this.ctx.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);
            
            // Convert canvas to base64 image
            const imageData = this.canvas.toDataURL('image/jpeg', 0.8);
            
            // Send to API for prediction
            const response = await fetch('/api/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    image: imageData
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                this.handlePredictionResult(result);
            }
            
        } catch (error) {
            console.error('Error processing frame:', error);
        }
    }
    
    handlePredictionResult(result) {
        const { gesture, confidence, accumulated_text } = result;
        
        // Update current gesture display
        if (gesture && confidence > this.elements.confidenceThreshold.value / 100) {
            this.elements.currentGesture.textContent = gesture;
            this.elements.confidence.textContent = `Confidence: ${(confidence * 100).toFixed(1)}%`;
            
            // Update gesture count
            this.gestureCount++;
            this.elements.gestureCount.textContent = this.gestureCount;
        } else {
            this.elements.currentGesture.textContent = '--';
            this.elements.confidence.textContent = 'Confidence: 0%';
        }
        
        // Update accumulated text
        if (accumulated_text) {
            this.elements.accumulatedText.textContent = accumulated_text;
        }
    }
    
    async clearText() {
        try {
            const response = await fetch('/api/clear_text', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            if (response.ok) {
                this.elements.accumulatedText.textContent = 'Start making gestures to see text appear here...';
                this.showToast('Text cleared', 'info');
            }
            
        } catch (error) {
            console.error('Error clearing text:', error);
        }
    }
    
    async speakAccumulatedText() {
        const text = this.elements.accumulatedText.textContent;
        
        if (!text || text === 'Start making gestures to see text appear here...') {
            this.showToast('No text to speak', 'warning');
            return;
        }
        
        try {
            const response = await fetch('/api/speak', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: text
                })
            });
            
            if (response.ok) {
                this.showToast('Speaking text...', 'info');
            }
            
        } catch (error) {
            console.error('Error speaking text:', error);
            this.showToast('Failed to speak text', 'error');
        }
    }
    
    async updateTTSSettings() {
        try {
            const response = await fetch('/api/tts_settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    rate: parseInt(this.elements.speechRate.value),
                    volume: parseFloat(this.elements.speechVolume.value) / 100
                })
            });
            
        } catch (error) {
            console.error('Error updating TTS settings:', error);
        }
    }
    
    async startSession() {
        try {
            const response = await fetch('/api/start_session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            if (response.ok) {
                const result = await response.json();
                this.sessionId = result.session_id;
            }
            
        } catch (error) {
            console.error('Error starting session:', error);
        }
    }
    
    async endSession() {
        if (this.sessionId) {
            try {
                const response = await fetch('/api/end_session', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        session_id: this.sessionId
                    })
                });
                
            } catch (error) {
                console.error('Error ending session:', error);
            }
        }
    }
    
    updateSessionTime() {
        if (!this.sessionStartTime) return;
        
        const elapsed = Date.now() - this.sessionStartTime;
        const minutes = Math.floor(elapsed / 60000);
        const seconds = Math.floor((elapsed % 60000) / 1000);
        
        this.elements.sessionTime.textContent = 
            `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }
    
    pauseRecognition() {
        if (this.recognitionActive) {
            this.stopRecognition();
        }
    }
    
    cleanup() {
        this.stopCamera();
    }
    
    showToast(message, type = 'info') {
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
        toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(toast);
        
        // Auto remove after 3 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 3000);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.recognitionApp = new SignLanguageRecognition();
});

// Check for camera support
if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    document.addEventListener('DOMContentLoaded', () => {
        const alert = document.createElement('div');
        alert.className = 'alert alert-warning';
        alert.innerHTML = `
            <i class="fas fa-exclamation-triangle me-2"></i>
            <strong>Camera not supported:</strong> Your browser doesn't support camera access. 
            Please use a modern browser like Chrome, Firefox, or Safari.
        `;
        document.querySelector('.container-fluid').prepend(alert);
    });
}