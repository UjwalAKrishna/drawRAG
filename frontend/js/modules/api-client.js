// API Client for RAG Builder Backend
export class APIClient {
    constructor(baseURL = 'http://localhost:8000') {
        this.baseURL = baseURL;
        this.timeout = 30000;
        this.retryAttempts = 3;
        this.retryDelay = 1000;
    }
    
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            timeout: this.timeout,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };
        
        for (let attempt = 0; attempt < this.retryAttempts; attempt++) {
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), this.timeout);
                
                const response = await fetch(url, {
                    ...config,
                    signal: controller.signal
                });
                
                clearTimeout(timeoutId);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                return { success: true, data };
                
            } catch (error) {
                if (attempt === this.retryAttempts - 1) {
                    return { 
                        success: false, 
                        error: error.message,
                        code: error.name === 'AbortError' ? 'TIMEOUT' : 'NETWORK_ERROR'
                    };
                }
                
                await new Promise(resolve => setTimeout(resolve, this.retryDelay * Math.pow(2, attempt)));
            }
        }
    }
    
    // Health check
    async checkHealth() {
        return await this.request('/api/health');
    }
    
    // Plugin management
    async getPlugins() {
        return await this.request('/api/plugins');
    }
    
    async getCapabilities() {
        return await this.request('/api/capabilities');
    }
    
    async getPluginDetails(pluginName) {
        return await this.request(`/api/plugins/${pluginName}`);
    }
    
    // Capability execution
    async executeCapability(capabilityName, args = [], kwargs = {}) {
        return await this.request(`/api/call/${capabilityName}`, {
            method: 'POST',
            body: JSON.stringify({ args, kwargs })
        });
    }
    
    async executeBatch(requests) {
        return await this.request('/api/batch', {
            method: 'POST',
            body: JSON.stringify({ requests })
        });
    }
    
    // Pipeline management
    async validatePipeline(pipelineConfig) {
        return await this.request('/api/pipeline/validate', {
            method: 'POST',
            body: JSON.stringify(pipelineConfig)
        });
    }
    
    async executePipeline(pipelineConfig, input) {
        return await this.request('/api/pipeline/execute', {
            method: 'POST',
            body: JSON.stringify({ pipeline: pipelineConfig, input })
        });
    }
    
    // File operations
    async uploadFile(file, onProgress = null) {
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const xhr = new XMLHttpRequest();
            
            return new Promise((resolve, reject) => {
                xhr.upload.addEventListener('progress', (event) => {
                    if (onProgress && event.lengthComputable) {
                        const percentComplete = (event.loaded / event.total) * 100;
                        onProgress(percentComplete);
                    }
                });
                
                xhr.addEventListener('load', () => {
                    if (xhr.status >= 200 && xhr.status < 300) {
                        try {
                            const response = JSON.parse(xhr.responseText);
                            resolve({ success: true, data: response });
                        } catch (e) {
                            resolve({ success: true, data: xhr.responseText });
                        }
                    } else {
                        reject(new Error(`Upload failed: ${xhr.statusText}`));
                    }
                });
                
                xhr.addEventListener('error', () => {
                    reject(new Error('Upload failed: Network error'));
                });
                
                xhr.open('POST', `${this.baseURL}/api/upload`);
                xhr.send(formData);
            });
            
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
    
    // Metrics and monitoring
    async getMetrics() {
        return await this.request('/api/metrics');
    }
    
    async getLogs(level = 'info', limit = 100) {
        return await this.request(`/api/logs?level=${level}&limit=${limit}`);
    }
    
    // Configuration
    async getConfig() {
        return await this.request('/api/config');
    }
    
    async updateConfig(configData) {
        return await this.request('/api/config', {
            method: 'PUT',
            body: JSON.stringify(configData)
        });
    }
    
    // WebSocket connection for real-time updates
    connectWebSocket(onMessage, onError, onClose) {
        const wsURL = this.baseURL.replace('http', 'ws') + '/ws';
        const ws = new WebSocket(wsURL);
        
        ws.onopen = () => {
            console.log('WebSocket connected');
        };
        
        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                onMessage(data);
            } catch (error) {
                console.error('Failed to parse WebSocket message:', error);
            }
        };
        
        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            if (onError) onError(error);
        };
        
        ws.onclose = () => {
            console.log('WebSocket disconnected');
            if (onClose) onClose();
        };
        
        return ws;
    }
}