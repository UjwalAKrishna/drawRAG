/**
 * RAG Tester - Test RAG pipelines with real queries
 */
window.RAGTester = class RAGTester {
    constructor(apiClient, eventBus) {
        this.apiClient = apiClient;
        this.eventBus = eventBus;
        this.currentPipeline = null;
        this.testHistory = [];
        
        this.setupEventListeners();
    }

    initialize() {
        this.setupModal();
        this.loadTestHistory();
    }

    setupModal() {
        const modal = document.getElementById('test-query-modal');
        const closeBtn = document.getElementById('close-modal');
        const runBtn = document.getElementById('run-query-btn');
        const queryInput = document.getElementById('test-query-input');
        const resultDiv = document.getElementById('query-result');

        if (!modal || !closeBtn || !runBtn || !queryInput || !resultDiv) return;

        // Close modal
        closeBtn.addEventListener('click', () => {
            modal.style.display = 'none';
        });

        // Run query
        runBtn.addEventListener('click', async () => {
            const query = queryInput.value.trim();
            if (!query) {
                this.showError('Please enter a query');
                return;
            }

            await this.runTest(query);
        });

        // Enter key to run query
        queryInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && e.ctrlKey) {
                runBtn.click();
            }
        });
    }

    async runTest(query) {
        const resultDiv = document.getElementById('query-result');
        const runBtn = document.getElementById('run-query-btn');
        
        if (!resultDiv || !runBtn) return;

        try {
            runBtn.disabled = true;
            runBtn.textContent = 'Running...';
            
            resultDiv.innerHTML = `
                <div class="loading">
                    <div class="loading-spinner"></div>
                    <p>Processing your query...</p>
                </div>
            `;

            const startTime = Date.now();
            
            // Check RAG status first
            const statusResponse = await this.apiClient.get('/api/rag/status');
            
            if (!statusResponse.ready) {
                this.showError('RAG system is not ready. Please ensure you have plugins for embeddings, vector database, and LLM.');
                return;
            }

            // Execute RAG query
            const response = await this.apiClient.post('/api/rag/query', {
                query: query,
                pipeline_config: this.currentPipeline || {}
            });

            const executionTime = Date.now() - startTime;

            // Display results
            this.displayResults(query, response, executionTime);
            
            // Save to history
            this.saveToHistory({
                query,
                response,
                executionTime,
                timestamp: new Date().toISOString()
            });

        } catch (error) {
            console.error('RAG test failed:', error);
            this.showError(error.message || 'Failed to execute query');
        } finally {
            runBtn.disabled = false;
            runBtn.textContent = 'Run Query';
        }
    }

    displayResults(query, response, executionTime) {
        const resultDiv = document.getElementById('query-result');
        if (!resultDiv) return;

        const sources = response.sources || [];
        const answer = response.answer || 'No answer generated';

        resultDiv.innerHTML = `
            <div class="query-result-content">
                <div class="result-header">
                    <h4>Query Results</h4>
                    <span class="execution-time">${executionTime}ms</span>
                </div>
                
                <div class="result-section">
                    <h5>Query:</h5>
                    <p class="query-text">"${query}"</p>
                </div>
                
                <div class="result-section">
                    <h5>Answer:</h5>
                    <div class="answer-text">${this.formatAnswer(answer)}</div>
                </div>
                
                ${sources.length > 0 ? `
                    <div class="result-section">
                        <h5>Sources (${sources.length}):</h5>
                        <div class="sources-list">
                            ${sources.map((source, index) => `
                                <div class="source-item">
                                    <div class="source-header">
                                        <span class="source-index">${index + 1}</span>
                                        <span class="source-score">Score: ${(source.score || 0).toFixed(3)}</span>
                                    </div>
                                    <div class="source-content">${this.truncateText(source.content || source.text || 'No content', 200)}</div>
                                    ${source.metadata ? `<div class="source-metadata">${JSON.stringify(source.metadata, null, 2)}</div>` : ''}
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
                
                <div class="result-actions">
                    <button class="btn btn-small" onclick="ragTester.saveResult()">💾 Save Result</button>
                    <button class="btn btn-small" onclick="ragTester.shareResult()">🔗 Share</button>
                    <button class="btn btn-small" onclick="ragTester.exportResult()">📤 Export</button>
                </div>
            </div>
        `;
    }

    formatAnswer(answer) {
        // Basic markdown-like formatting
        return answer
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>')
            .replace(/```(.*?)```/gs, '<pre><code>$1</code></pre>');
    }

    truncateText(text, maxLength) {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }

    showError(message) {
        const resultDiv = document.getElementById('query-result');
        if (!resultDiv) return;

        resultDiv.innerHTML = `
            <div class="error-result">
                <div class="error-icon">❌</div>
                <h4>Error</h4>
                <p>${message}</p>
            </div>
        `;
    }

    saveToHistory(testResult) {
        this.testHistory.unshift(testResult);
        
        // Keep only last 50 tests
        if (this.testHistory.length > 50) {
            this.testHistory = this.testHistory.slice(0, 50);
        }
        
        // Save to localStorage
        try {
            localStorage.setItem('rag_test_history', JSON.stringify(this.testHistory));
        } catch (error) {
            console.warn('Failed to save test history:', error);
        }
        
        this.eventBus.emit('test-history-updated', { history: this.testHistory });
    }

    loadTestHistory() {
        try {
            const saved = localStorage.getItem('rag_test_history');
            if (saved) {
                this.testHistory = JSON.parse(saved);
            }
        } catch (error) {
            console.warn('Failed to load test history:', error);
            this.testHistory = [];
        }
    }

    setPipeline(pipelineConfig) {
        this.currentPipeline = pipelineConfig;
    }

    openTestModal() {
        const modal = document.getElementById('test-query-modal');
        const queryInput = document.getElementById('test-query-input');
        
        if (modal && queryInput) {
            modal.style.display = 'block';
            queryInput.focus();
        }
    }

    setupEventListeners() {
        // Test query button
        const testBtn = document.getElementById('test-query-btn');
        if (testBtn) {
            testBtn.addEventListener('click', () => {
                this.openTestModal();
            });
        }

        // Pipeline updates
        this.eventBus.on('pipeline-updated', (data) => {
            this.setPipeline(data.pipeline);
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 't') {
                e.preventDefault();
                this.openTestModal();
            }
        });
    }

    async saveResult() {
        // Implementation for saving test results
        console.log('Save result clicked');
    }

    async shareResult() {
        // Implementation for sharing results
        console.log('Share result clicked');
    }

    async exportResult() {
        // Implementation for exporting results
        console.log('Export result clicked');
    }

    getTestHistory() {
        return this.testHistory;
    }

    clearHistory() {
        this.testHistory = [];
        localStorage.removeItem('rag_test_history');
        this.eventBus.emit('test-history-updated', { history: [] });
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = RAGTester;
}