/**
 * API Client for RAG Builder Backend Communication
 * Handles all HTTP requests to the backend with proper error handling
 */
class APIClient {
    constructor(baseUrl = '') {
        this.baseUrl = baseUrl;
        this.defaultHeaders = {
            'Content-Type': 'application/json',
        };
        this.requestTimeout = 30000; // 30 seconds
    }

    /**
     * Make authenticated HTTP request
     * @param {string} method - HTTP method
     * @param {string} endpoint - API endpoint
     * @param {Object} data - Request payload
     * @param {Object} headers - Additional headers
     * @returns {Promise<Object>} Response data
     */
    async makeRequest(method, endpoint, data = null, headers = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const requestHeaders = { ...this.defaultHeaders, ...headers };

        const config = {
            method: method.toUpperCase(),
            headers: requestHeaders,
        };

        if (data && ['POST', 'PUT', 'PATCH'].includes(config.method)) {
            config.body = JSON.stringify(data);
        }

        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), this.requestTimeout);
            
            config.signal = controller.signal;

            const response = await fetch(url, config);
            clearTimeout(timeoutId);

            if (!response.ok) {
                throw new APIError(
                    `HTTP ${response.status}: ${response.statusText}`,
                    response.status,
                    await this._safeParseJSON(response)
                );
            }

            return await this._safeParseJSON(response);
        } catch (error) {
            if (error.name === 'AbortError') {
                throw new APIError('Request timeout', 408);
            }
            
            if (error instanceof APIError) {
                throw error;
            }

            throw new APIError(`Network error: ${error.message}`, 0);
        }
    }

    /**
     * Safely parse JSON response
     * @param {Response} response - Fetch response
     * @returns {Promise<Object>} Parsed JSON or empty object
     */
    async _safeParseJSON(response) {
        try {
            const text = await response.text();
            return text ? JSON.parse(text) : {};
        } catch (error) {
            console.warn('Failed to parse JSON response:', error);
            return {};
        }
    }

    // HTTP method shortcuts
    async get(endpoint, headers = {}) {
        return this.makeRequest('GET', endpoint, null, headers);
    }

    async post(endpoint, data = {}, headers = {}) {
        return this.makeRequest('POST', endpoint, data, headers);
    }

    async put(endpoint, data = {}, headers = {}) {
        return this.makeRequest('PUT', endpoint, data, headers);
    }

    async delete(endpoint, headers = {}) {
        return this.makeRequest('DELETE', endpoint, null, headers);
    }

    // RAG Builder specific API methods
    async getCapabilities() {
        return this.get('/api/capabilities/');
    }

    async getPlugins() {
        return this.get('/api/plugins/');
    }

    async getHealthStatus() {
        return this.get('/api/health');
    }

    async executeQuery(query, pipelineConfig) {
        return this.post('/api/rag/query', {
            query,
            pipeline_config: pipelineConfig
        });
    }

    async validatePipeline(pipelineConfig) {
        return this.post('/api/pipeline/validate', pipelineConfig);
    }

    async savePipeline(pipelineData) {
        return this.post('/api/pipeline/save', pipelineData);
    }

    async loadPipeline(pipelineId) {
        return this.get(`/api/pipeline/load/${pipelineId}`);
    }

    async getMetrics() {
        return this.get('/api/metrics');
    }
}

/**
 * Custom API Error class
 */
class APIError extends Error {
    constructor(message, status = 0, details = null) {
        super(message);
        this.name = 'APIError';
        this.status = status;
        this.details = details;
    }

    get isNetworkError() {
        return this.status === 0;
    }

    get isServerError() {
        return this.status >= 500;
    }

    get isClientError() {
        return this.status >= 400 && this.status < 500;
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { APIClient, APIError };
}