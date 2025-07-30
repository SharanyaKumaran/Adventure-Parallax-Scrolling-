// Main JavaScript utilities for SignLang AI

// Utility functions
const utils = {
    // Show toast notification
    showToast: function(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
        toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(toast);
        
        // Auto remove
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, duration);
    },
    
    // Format date
    formatDate: function(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },
    
    // Format duration
    formatDuration: function(startTime, endTime) {
        if (!endTime) return 'Active';
        
        const duration = new Date(endTime) - new Date(startTime);
        const minutes = Math.floor(duration / 60000);
        const seconds = Math.floor((duration % 60000) / 1000);
        
        if (minutes > 0) {
            return `${minutes}m ${seconds}s`;
        } else {
            return `${seconds}s`;
        }
    },
    
    // Check if device has camera
    checkCameraSupport: function() {
        return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
    },
    
    // Debounce function
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    // API helper
    apiCall: async function(endpoint, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };
        
        const config = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(endpoint, config);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API call failed:', error);
            throw error;
        }
    }
};

// Performance monitoring
const performance = {
    start: function(label) {
        if (window.performance && window.performance.mark) {
            window.performance.mark(`${label}-start`);
        }
    },
    
    end: function(label) {
        if (window.performance && window.performance.mark && window.performance.measure) {
            window.performance.mark(`${label}-end`);
            window.performance.measure(label, `${label}-start`, `${label}-end`);
        }
    },
    
    getEntries: function() {
        if (window.performance && window.performance.getEntriesByType) {
            return window.performance.getEntriesByType('measure');
        }
        return [];
    }
};

// Initialize common functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Handle navbar toggler animation
    const navbarToggler = document.querySelector('.navbar-toggler');
    if (navbarToggler) {
        navbarToggler.addEventListener('click', function() {
            this.classList.toggle('active');
        });
    }
    
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-dismissible)');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => {
                if (alert.parentNode) {
                    alert.parentNode.removeChild(alert);
                }
            }, 300);
        }, 5000);
    });
    
    // Check camera support and show warning if not available
    if (!utils.checkCameraSupport()) {
        const cameraWarning = document.createElement('div');
        cameraWarning.className = 'alert alert-warning alert-dismissible fade show';
        cameraWarning.innerHTML = `
            <i class="fas fa-exclamation-triangle me-2"></i>
            <strong>Camera not supported:</strong> Your browser doesn't support camera access. 
            Please use a modern browser like Chrome, Firefox, or Safari.
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const container = document.querySelector('.container, .container-fluid');
        if (container) {
            container.insertBefore(cameraWarning, container.firstChild);
        }
    }
});

// Global error handler
window.addEventListener('error', function(event) {
    console.error('Global error:', event.error);
    
    // Don't show toast for script loading errors
    if (event.error && event.error.message && !event.error.message.includes('Script error')) {
        utils.showToast('An unexpected error occurred. Please refresh the page.', 'error');
    }
});

// Handle unhandled promise rejections
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    event.preventDefault();
    
    utils.showToast('An error occurred while processing your request.', 'error');
});

// Export utilities for use in other scripts
window.utils = utils;
window.performanceMonitor = performance;