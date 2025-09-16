/**
 * RAG Builder Application
 * Main application class that orchestrates all components
 */
class RAGBuilderApp {
    constructor() {
        this.eventBus = new EventBus();
        this.apiClient = new APIClient();
        this.componentManager = new ComponentManager();
        this.uiManager = null;
        this.pipelineManager = null;
        this.queryManager = null;
        
        this.isInitialized = false;
        this.config = {
            autoSave: true,
            debugMode: false,
            theme: 'light'
        };

        this.init();
    }

    /**
     * Initialize the application
     */
    async init() {
        try {
            this.showLoadingState('Initializing RAG Builder...');
            
            // Check backend connectivity
            await this.checkBackendConnectivity();
            
            // Initialize managers
            this.uiManager = new UIManager(this.componentManager, this.eventBus);
            this.pipelineManager = new PipelineManager(this.componentManager, this.apiClient, this.eventBus);
            this.queryManager = new QueryManager(this.pipelineManager, this.apiClient, this.eventBus);
            this.pluginManager = new PluginManager(this.apiClient, this.eventBus);
            this.ragTester = new RAGTester(this.apiClient, this.eventBus);
            this.documentProcessor = new DocumentProcessor(this.apiClient, this.eventBus);
            
            // Initialize all managers
            const initPromises = [];
            
            if (this.uiManager && typeof this.uiManager.initialize === 'function') {
                initPromises.push(this.uiManager.initialize());
            }
            if (this.pipelineManager && typeof this.pipelineManager.initialize === 'function') {
                initPromises.push(this.pipelineManager.initialize());
            }
            if (this.queryManager && typeof this.queryManager.initialize === 'function') {
                initPromises.push(this.queryManager.initialize());
            }
            if (this.pluginManager && typeof this.pluginManager.initialize === 'function') {
                initPromises.push(this.pluginManager.initialize());
            }
            if (this.ragTester && typeof this.ragTester.initialize === 'function') {
                initPromises.push(this.ragTester.initialize());
            }
            if (this.documentProcessor && typeof this.documentProcessor.initialize === 'function') {
                initPromises.push(this.documentProcessor.initialize());
            }
            
            await Promise.all(initPromises);
            
            // Load available plugins from backend
            await this.loadAvailablePlugins();
            
            // Setup global event listeners
            this.setupGlobalEventListeners();
            
            // Setup UI event handlers
            this.setupUIEventHandlers();
            
            // Setup keyboard shortcuts
            this.setupKeyboardShortcuts();
            
            // Load user preferences
            this.loadUserPreferences();
            
            // Check for auto-saved data
            await this.checkAutoSavedData();
            
            this.isInitialized = true;
            this.hideLoadingState();
            
            this.showNotification('RAG Builder initialized successfully', 'success');
            this.addLog('Application initialized', 'info');
            
        } catch (error) {
            this.hideLoadingState();
            this.handleInitializationError(error);
        }
    }

    /**
     * Check backend connectivity
     */
    async checkBackendConnectivity() {
        try {
            const health = await this.apiClient.getHealthStatus();
            this.updateConnectionStatus(true, health);
        } catch (error) {
            console.warn('Backend not available, running in offline mode:', error.message);
            this.updateConnectionStatus(false);
        }
    }

    /**
     * Load available plugins from backend
     */
    async loadAvailablePlugins() {
        try {
            this.showLoadingState('Loading available plugins...');
            await this.componentManager.loadAvailablePlugins(this.apiClient);
            this.addLog('Plugins loaded successfully', 'success');
        } catch (error) {
            console.warn('Failed to load plugins:', error);
            this.addLog('Using fallback plugin definitions', 'warning');
            // ComponentManager will fall back to default definitions
        } finally {
            this.hideLoadingState();
        }
    }

    /**
     * Setup global event listeners
     */
    setupGlobalEventListeners() {
        // Component events
        this.eventBus.on('component:created', this.handleComponentCreated.bind(this));
        this.eventBus.on('component:updated', this.handleComponentUpdated.bind(this));
        this.eventBus.on('component:deleted', this.handleComponentDeleted.bind(this));
        
        // Pipeline events
        this.eventBus.on('pipeline:validated', this.handlePipelineValidated.bind(this));
        this.eventBus.on('pipeline:saved', this.handlePipelineSaved.bind(this));
        this.eventBus.on('pipeline:loaded', this.handlePipelineLoaded.bind(this));
        this.eventBus.on('pipeline:modified', this.handlePipelineModified.bind(this));
        
        // Query events
        this.eventBus.on('query:started', this.handleQueryStarted.bind(this));
        this.eventBus.on('query:completed', this.handleQueryCompleted.bind(this));
        this.eventBus.on('query:failed', this.handleQueryFailed.bind(this));
        
        // Error handling
        this.eventBus.on('error:*', this.handleError.bind(this));
        
        // Window events
        window.addEventListener('online', () => this.handleOnlineStatus(true));
        window.addEventListener('offline', () => this.handleOnlineStatus(false));
        window.addEventListener('resize', () => this.handleWindowResize());
    }

    /**
     * Setup UI event handlers
     */
    setupUIEventHandlers() {
        // Header buttons
        this.setupButton('save-pipeline-btn', () => this.savePipeline());
        this.setupButton('load-pipeline-btn', () => this.loadPipeline());
        this.setupButton('test-query-btn', () => this.openQueryModal());
        this.setupButton('export-config-btn', () => this.exportPipeline());
        this.setupButton('validate-pipeline-btn', () => this.validatePipeline());
        this.setupButton('clear-logs-btn', () => this.clearLogs());
        
        // Modal handlers
        this.setupModal();
        
        // Tab handlers
        this.setupTabs();
        
        // Settings handlers
        this.setupSettingsHandlers();
    }

    /**
     * Setup button event handler
     * @param {string} buttonId - Button element ID
     * @param {Function} handler - Click handler
     */
    setupButton(buttonId, handler) {
        const button = document.getElementById(buttonId);
        if (button) {
            button.addEventListener('click', async (e) => {
                e.preventDefault();
                try {
                    await handler();
                } catch (error) {
                    this.handleError({ error, context: buttonId });
                }
            });
        }
    }

    /**
     * Setup modal functionality
     */
    setupModal() {
        const modal = document.getElementById('test-query-modal');
        const closeBtn = document.getElementById('close-modal');
        const runQueryBtn = document.getElementById('run-query-btn');
        
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.closeQueryModal());
        }
        
        if (runQueryBtn) {
            runQueryBtn.addEventListener('click', () => this.executeQuery());
        }
        
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeQueryModal();
                }
            });
        }
        
        // Enter key in query input
        const queryInput = document.getElementById('test-query-input');
        if (queryInput) {
            queryInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.executeQuery();
                }
            });
        }
    }

    /**
     * Setup tab functionality
     */
    setupTabs() {
        const tabButtons = document.querySelectorAll('.tab-btn');
        const tabContents = document.querySelectorAll('.tab-content');

        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                const targetTab = button.dataset.tab;
                
                // Remove active class from all tabs and contents
                tabButtons.forEach(btn => btn.classList.remove('active'));
                tabContents.forEach(content => content.classList.remove('active'));
                
                // Add active class to clicked tab and corresponding content
                button.classList.add('active');
                const targetContent = document.getElementById(`${targetTab}-tab`);
                if (targetContent) {
                    targetContent.classList.add('active');
                }
            });
        });
    }

    /**
     * Setup settings handlers
     */
    setupSettingsHandlers() {
        // Pipeline name and description
        const nameInput = document.getElementById('pipeline-name');
        const descInput = document.getElementById('pipeline-description');
        
        if (nameInput) {
            nameInput.addEventListener('input', (e) => {
                this.pipelineManager.setPipelineMetadata({ name: e.target.value });
            });
        }
        
        if (descInput) {
            descInput.addEventListener('input', (e) => {
                this.pipelineManager.setPipelineMetadata({ description: e.target.value });
            });
        }
    }

    /**
     * Setup keyboard shortcuts
     */
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + S - Save pipeline
            if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                e.preventDefault();
                this.savePipeline();
            }
            
            // Ctrl/Cmd + O - Load pipeline
            if ((e.ctrlKey || e.metaKey) && e.key === 'o') {
                e.preventDefault();
                this.loadPipeline();
            }
            
            // Ctrl/Cmd + T - Test query
            if ((e.ctrlKey || e.metaKey) && e.key === 't') {
                e.preventDefault();
                this.openQueryModal();
            }
            
            // Ctrl/Cmd + E - Export pipeline
            if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
                e.preventDefault();
                this.exportPipeline();
            }
            
            // Escape - Close modals or deselect
            if (e.key === 'Escape') {
                const modal = document.getElementById('test-query-modal');
                if (modal && modal.classList.contains('show')) {
                    this.closeQueryModal();
                } else {
                    this.uiManager.deselectComponent();
                }
            }
            
            // Delete - Delete selected component
            if (e.key === 'Delete' && this.componentManager.selectedComponentId) {
                this.componentManager.deleteComponent(this.componentManager.selectedComponentId);
            }
        });
    }

    /**
     * Save pipeline
     */
    async savePipeline() {
        try {
            const options = {
                saveLocal: true,
                saveToServer: true,
                downloadFile: false
            };
            
            const result = await this.pipelineManager.savePipeline(options);
            
            if (result.success) {
                this.showNotification('Pipeline saved successfully', 'success');
                this.addLog('Pipeline saved', 'success');
            }
        } catch (error) {
            this.showNotification(`Save failed: ${error.message}`, 'error');
            this.addLog(`Save failed: ${error.message}`, 'error');
        }
    }

    /**
     * Load pipeline
     */
    async loadPipeline() {
        try {
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = '.json,.yaml,.yml';
            
            input.onchange = async (e) => {
                const file = e.target.files[0];
                if (file) {
                    try {
                        const result = await this.pipelineManager.importPipeline(file);
                        this.showNotification(`Pipeline loaded: ${file.name}`, 'success');
                        this.addLog(`Pipeline loaded from ${file.name}`, 'success');
                    } catch (error) {
                        this.showNotification(`Load failed: ${error.message}`, 'error');
                        this.addLog(`Load failed: ${error.message}`, 'error');
                    }
                }
            };
            
            input.click();
        } catch (error) {
            this.showNotification(`Load failed: ${error.message}`, 'error');
        }
    }

    /**
     * Export pipeline
     */
    async exportPipeline() {
        try {
            const format = 'json'; // Could be made configurable
            const exportResult = this.pipelineManager.exportPipeline(format);
            
            // Download file
            const blob = new Blob([exportResult.data], { type: exportResult.mimeType });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = exportResult.filename;
            link.click();
            URL.revokeObjectURL(url);
            
            this.showNotification('Pipeline exported successfully', 'success');
            this.addLog(`Pipeline exported as ${exportResult.filename}`, 'success');
        } catch (error) {
            this.showNotification(`Export failed: ${error.message}`, 'error');
            this.addLog(`Export failed: ${error.message}`, 'error');
        }
    }

    /**
     * Validate pipeline
     */
    async validatePipeline() {
        try {
            this.addLog('Validating pipeline...', 'info');
            const validation = await this.pipelineManager.validatePipeline();
            
            if (validation.isValid) {
                this.showNotification('Pipeline validation passed', 'success');
                this.addLog('Pipeline validation passed', 'success');
            } else {
                const issues = validation.issues.join(', ');
                this.showNotification(`Validation issues: ${issues}`, 'warning');
                validation.issues.forEach(issue => this.addLog(`Validation: ${issue}`, 'warning'));
            }
        } catch (error) {
            this.showNotification(`Validation failed: ${error.message}`, 'error');
            this.addLog(`Validation failed: ${error.message}`, 'error');
        }
    }

    /**
     * Open query modal
     */
    openQueryModal() {
        const modal = document.getElementById('test-query-modal');
        if (modal) {
            modal.classList.add('show');
            
            // Focus on query input
            const queryInput = document.getElementById('test-query-input');
            if (queryInput) {
                queryInput.focus();
            }
        }
    }

    /**
     * Close query modal
     */
    closeQueryModal() {
        const modal = document.getElementById('test-query-modal');
        if (modal) {
            modal.classList.remove('show');
            
            // Clear query input and results
            const queryInput = document.getElementById('test-query-input');
            const queryResult = document.getElementById('query-result');
            
            if (queryInput) queryInput.value = '';
            if (queryResult) {
                queryResult.classList.remove('show');
                queryResult.innerHTML = '';
            }
        }
    }

    /**
     * Execute query
     */
    async executeQuery() {
        const queryInput = document.getElementById('test-query-input');
        const queryResult = document.getElementById('query-result');
        
        if (!queryInput || !queryResult) return;
        
        const query = queryInput.value.trim();
        if (!query) {
            this.showNotification('Please enter a question', 'warning');
            return;
        }
        
        try {
            // Show loading state
            queryResult.innerHTML = '<div class="loading-spinner">🔄 Processing your query...</div>';
            queryResult.classList.add('show');
            
            const result = await this.queryManager.executeQuery(query);
            
            // Display results
            this.displayQueryResult(result, queryResult);
            
        } catch (error) {
            this.displayQueryError(error, queryResult);
        }
    }

    /**
     * Display query result
     * @param {Object} result - Query result
     * @param {HTMLElement} container - Result container
     */
    displayQueryResult(result, container) {
        container.innerHTML = `
            <div class="query-response">
                <div class="answer-section">
                    <h4>📝 Answer:</h4>
                    <div class="answer-content">${result.answer}</div>
                </div>
                <div class="sources-section">
                    <h4>📚 Sources:</h4>
                    <ul class="sources-list">
                        ${result.sources?.map(source => `<li>${source}</li>`).join('') || '<li>No sources available</li>'}
                    </ul>
                </div>
                <div class="metrics-section">
                    <h4>📊 Metrics:</h4>
                    <div class="metrics-grid">
                        <div class="metric">
                            <span class="metric-label">Response Time:</span>
                            <span class="metric-value">${result.executionTime}ms</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Sources Found:</span>
                            <span class="metric-value">${result.sources?.length || 0}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Confidence:</span>
                            <span class="metric-value">${result.confidence || 'N/A'}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Display query error
     * @param {Error} error - Error object
     * @param {HTMLElement} container - Result container
     */
    displayQueryError(error, container) {
        container.innerHTML = `
            <div class="error-response">
                <h4>❌ Error</h4>
                <p>${error.message}</p>
                <details>
                    <summary>Technical Details</summary>
                    <pre>${error.stack || error.toString()}</pre>
                </details>
            </div>
        `;
    }

    // Event Handlers

    /**
     * Handle component created
     * @param {Object} data - Event data
     */
    handleComponentCreated(data) {
        this.addLog(`Created ${data.component.name}`, 'success');
    }

    /**
     * Handle component updated
     * @param {Object} data - Event data
     */
    handleComponentUpdated(data) {
        this.addLog(`Updated ${data.component.name}`, 'info');
    }

    /**
     * Handle component deleted
     * @param {Object} data - Event data
     */
    handleComponentDeleted(data) {
        this.addLog(`Deleted component`, 'warning');
    }

    /**
     * Handle pipeline validated
     * @param {Object} data - Event data
     */
    handlePipelineValidated(data) {
        const { result } = data;
        if (result.isValid) {
            this.addLog('Pipeline validation passed', 'success');
        } else {
            result.issues.forEach(issue => this.addLog(`Validation: ${issue}`, 'warning'));
        }
    }

    /**
     * Handle pipeline saved
     * @param {Object} data - Event data
     */
    handlePipelineSaved(data) {
        this.addLog('Pipeline saved', 'success');
    }

    /**
     * Handle pipeline loaded
     * @param {Object} data - Event data
     */
    handlePipelineLoaded(data) {
        this.addLog('Pipeline loaded', 'success');
        this.updatePipelineInfo(data.pipelineData);
    }

    /**
     * Handle pipeline modified
     * @param {Object} data - Event data
     */
    handlePipelineModified(data) {
        // Update UI to show unsaved changes
        this.updateSaveStatus(false);
    }

    /**
     * Handle query started
     * @param {Object} data - Event data
     */
    handleQueryStarted(data) {
        this.addLog(`Query started: "${data.query.substring(0, 50)}..."`, 'info');
    }

    /**
     * Handle query completed
     * @param {Object} data - Event data
     */
    handleQueryCompleted(data) {
        this.addLog(`Query completed in ${data.result.executionTime}ms`, 'success');
    }

    /**
     * Handle query failed
     * @param {Object} data - Event data
     */
    handleQueryFailed(data) {
        this.addLog(`Query failed: ${data.error.message}`, 'error');
    }

    /**
     * Handle application errors
     * @param {Object} data - Event data
     */
    handleError(data) {
        console.error('Application error:', data.error);
        this.addLog(`Error: ${data.error.message}`, 'error');
        
        if (data.context) {
            this.addLog(`Context: ${data.context}`, 'error');
        }
    }

    /**
     * Handle online/offline status
     * @param {boolean} isOnline - Online status
     */
    handleOnlineStatus(isOnline) {
        this.updateConnectionStatus(isOnline);
        const message = isOnline ? 'Connection restored' : 'Working offline';
        this.showNotification(message, isOnline ? 'success' : 'warning');
    }

    /**
     * Handle window resize
     */
    handleWindowResize() {
        if (this.uiManager) {
            this.uiManager.updateConnectionLines();
        }
    }

    /**
     * Handle initialization error
     * @param {Error} error - Initialization error
     */
    handleInitializationError(error) {
        console.error('Initialization failed:', error);
        this.showNotification(`Initialization failed: ${error.message}`, 'error');
        
        // Show error state in UI
        const errorContainer = document.createElement('div');
        errorContainer.className = 'init-error';
        errorContainer.innerHTML = `
            <h3>❌ Initialization Failed</h3>
            <p>${error.message}</p>
            <button onclick="location.reload()" class="btn btn-primary">Reload Application</button>
        `;
        
        document.body.appendChild(errorContainer);
    }

    // Utility Methods

    /**
     * Show loading state
     * @param {string} message - Loading message
     */
    showLoadingState(message = 'Loading...') {
        const loader = document.createElement('div');
        loader.id = 'app-loader';
        loader.className = 'app-loader';
        loader.innerHTML = `
            <div class="loader-content">
                <div class="loader-spinner"></div>
                <p>${message}</p>
            </div>
        `;
        document.body.appendChild(loader);
    }

    /**
     * Hide loading state
     */
    hideLoadingState() {
        const loader = document.getElementById('app-loader');
        if (loader) {
            loader.remove();
        }
    }

    /**
     * Show notification
     * @param {string} message - Notification message
     * @param {string} type - Notification type
     */
    showNotification(message, type = 'info') {
        if (this.uiManager) {
            this.uiManager.showNotification(message, type);
        } else {
            console.log(`[${type.toUpperCase()}] ${message}`);
        }
    }

    /**
     * Add log entry
     * @param {string} message - Log message
     * @param {string} type - Log type
     */
    addLog(message, type = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = { timestamp, message, type };
        
        // Add to logs array (could be moved to a dedicated LogManager)
        if (!this.logs) this.logs = [];
        this.logs.push(logEntry);
        
        // Keep only last 100 logs
        if (this.logs.length > 100) {
            this.logs.shift();
        }
        
        this.renderLogs();
        
        // Emit log event
        this.eventBus.emit('log:added', logEntry);
    }

    /**
     * Render logs in UI
     */
    renderLogs() {
        const logsContent = document.getElementById('logs-content');
        if (!logsContent || !this.logs) return;
        
        const recentLogs = this.logs.slice(-10); // Show last 10 logs
        
        logsContent.innerHTML = recentLogs.map(log => `
            <div class="log-entry ${log.type}">
                <span class="log-time">${log.timestamp}</span>
                <span class="log-message">${log.message}</span>
            </div>
        `).join('');
        
        // Auto-scroll to bottom
        logsContent.scrollTop = logsContent.scrollHeight;
    }

    /**
     * Clear logs
     */
    clearLogs() {
        this.logs = [];
        this.renderLogs();
        this.addLog('Logs cleared', 'info');
    }

    /**
     * Update connection status
     * @param {boolean} isConnected - Connection status
     * @param {Object} healthData - Health data from backend
     */
    updateConnectionStatus(isConnected, healthData = null) {
        const statusIndicator = document.getElementById('status-indicator');
        const statusText = document.getElementById('status-text');
        
        if (statusIndicator && statusText) {
            if (isConnected) {
                statusIndicator.className = 'status-indicator connected';
                statusText.textContent = 'Connected';
            } else {
                statusIndicator.className = 'status-indicator disconnected';
                statusText.textContent = 'Offline Mode';
            }
        }
    }

    /**
     * Update pipeline info
     * @param {Object} pipelineData - Pipeline data
     */
    updatePipelineInfo(pipelineData) {
        if (pipelineData.metadata) {
            const nameInput = document.getElementById('pipeline-name');
            const descInput = document.getElementById('pipeline-description');
            
            if (nameInput) nameInput.value = pipelineData.metadata.name || '';
            if (descInput) descInput.value = pipelineData.metadata.description || '';
        }
    }

    /**
     * Update save status
     * @param {boolean} isSaved - Save status
     */
    updateSaveStatus(isSaved) {
        const saveBtn = document.getElementById('save-pipeline-btn');
        if (saveBtn) {
            if (isSaved) {
                saveBtn.classList.remove('unsaved');
            } else {
                saveBtn.classList.add('unsaved');
            }
        }
    }

    /**
     * Load user preferences
     */
    loadUserPreferences() {
        try {
            const preferences = JSON.parse(localStorage.getItem('ragbuilder_preferences') || '{}');
            this.config = { ...this.config, ...preferences };
            
            // Apply theme
            if (this.config.theme) {
                document.body.setAttribute('data-theme', this.config.theme);
            }
            
            // Apply debug mode
            if (this.config.debugMode) {
                this.eventBus.setDebugMode(true);
            }
        } catch (error) {
            console.warn('Failed to load user preferences:', error);
        }
    }

    /**
     * Save user preferences
     */
    saveUserPreferences() {
        try {
            localStorage.setItem('ragbuilder_preferences', JSON.stringify(this.config));
        } catch (error) {
            console.warn('Failed to save user preferences:', error);
        }
    }

    /**
     * Check for auto-saved data
     */
    async checkAutoSavedData() {
        try {
            const autoSaved = localStorage.getItem('ragbuilder_autosave');
            if (autoSaved) {
                const data = JSON.parse(autoSaved);
                const shouldRestore = confirm(
                    'Found auto-saved pipeline data. Would you like to restore it?'
                );
                
                if (shouldRestore) {
                    await this.pipelineManager.loadPipeline(data);
                    this.addLog('Auto-saved pipeline restored', 'success');
                }
            }
        } catch (error) {
            console.warn('Failed to check auto-saved data:', error);
        }
    }

    /**
     * Get application state
     * @returns {Object} Application state
     */
    getState() {
        return {
            isInitialized: this.isInitialized,
            config: this.config,
            componentCount: this.componentManager.getAllComponents().length,
            connectionCount: this.componentManager.getAllConnections().length,
            pipelineMetadata: this.pipelineManager.getPipelineMetadata()
        };
    }

    /**
     * Destroy application and cleanup resources
     */
    destroy() {
        // Cleanup managers
        if (this.pipelineManager) {
            this.pipelineManager.destroy();
        }
        
        // Clear event bus
        this.eventBus.removeAllListeners();
        
        // Save preferences
        this.saveUserPreferences();
        
        // Clear intervals and timers
        // (Each manager should handle its own cleanup)
        
        this.isInitialized = false;
    }
}

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.ragBuilderApp = new RAGBuilderApp();
});