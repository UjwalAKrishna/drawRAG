/**
 * Pipeline Manager
 * Handles pipeline operations like save, load, validate, and execute
 */
class PipelineManager {
    constructor(componentManager, apiClient, eventBus) {
        this.componentManager = componentManager;
        this.apiClient = apiClient;
        this.eventBus = eventBus;
        this.pipelineMetadata = {
            name: '',
            description: '',
            version: '1.0.0',
            createdAt: null,
            lastModified: null
        };
        this.autoSaveEnabled = true;
        this.autoSaveInterval = 30000; // 30 seconds
        this.autoSaveTimer = null;
        
        this.initializeAutoSave();
        this.setupEventListeners();
    }

    /**
     * Initialize auto-save functionality
     */
    initializeAutoSave() {
        if (this.autoSaveEnabled) {
            this.autoSaveTimer = setInterval(() => {
                this.performAutoSave();
            }, this.autoSaveInterval);
        }

        // Save before page unload
        window.addEventListener('beforeunload', (event) => {
            if (this.hasUnsavedChanges()) {
                this.performAutoSave();
                event.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
            }
        });
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        this.eventBus.on('component:created', () => this.markAsModified());
        this.eventBus.on('component:updated', () => this.markAsModified());
        this.eventBus.on('component:deleted', () => this.markAsModified());
        this.eventBus.on('component:moved', () => this.markAsModified());
        this.eventBus.on('component:connected', () => this.markAsModified());
        this.eventBus.on('component:disconnected', () => this.markAsModified());
    }

    /**
     * Mark pipeline as modified
     */
    markAsModified() {
        this.pipelineMetadata.lastModified = new Date().toISOString();
        this.eventBus.emit('pipeline:modified', { metadata: this.pipelineMetadata });
    }

    /**
     * Set pipeline metadata
     * @param {Object} metadata - Pipeline metadata
     */
    setPipelineMetadata(metadata) {
        this.pipelineMetadata = {
            ...this.pipelineMetadata,
            ...metadata,
            lastModified: new Date().toISOString()
        };
        
        if (!this.pipelineMetadata.createdAt) {
            this.pipelineMetadata.createdAt = new Date().toISOString();
        }
    }

    /**
     * Get pipeline metadata
     * @returns {Object} Pipeline metadata
     */
    getPipelineMetadata() {
        return { ...this.pipelineMetadata };
    }

    /**
     * Validate pipeline
     * @returns {Promise<Object>} Validation result
     */
    async validatePipeline() {
        try {
            // Local validation
            const localValidation = this.componentManager.validatePipeline();
            
            // Server-side validation if available
            let serverValidation = null;
            try {
                const pipelineConfig = this.getPipelineConfiguration();
                serverValidation = await this.apiClient.validatePipeline(pipelineConfig);
            } catch (error) {
                console.warn('Server validation failed:', error.message);
            }

            const result = {
                ...localValidation,
                serverValidation,
                timestamp: new Date().toISOString()
            };

            this.eventBus.emit('pipeline:validated', { result });
            return result;
        } catch (error) {
            throw new PipelineError(`Validation failed: ${error.message}`, 'VALIDATION_ERROR');
        }
    }

    /**
     * Save pipeline
     * @param {Object} options - Save options
     * @returns {Promise<Object>} Save result
     */
    async savePipeline(options = {}) {
        try {
            const pipelineData = this.preparePipelineData();
            
            if (options.saveLocal !== false) {
                this.saveToLocalStorage(pipelineData);
            }

            let serverResult = null;
            if (options.saveToServer !== false) {
                try {
                    serverResult = await this.apiClient.savePipeline(pipelineData);
                } catch (error) {
                    console.warn('Server save failed:', error.message);
                }
            }

            if (options.downloadFile) {
                this.downloadPipelineFile(pipelineData);
            }

            this.eventBus.emit('pipeline:saved', { 
                pipelineData, 
                serverResult,
                options 
            });

            return {
                success: true,
                local: options.saveLocal !== false,
                server: serverResult?.success || false,
                downloaded: options.downloadFile || false
            };
        } catch (error) {
            throw new PipelineError(`Save failed: ${error.message}`, 'SAVE_ERROR');
        }
    }

    /**
     * Load pipeline
     * @param {string|Object} source - Pipeline ID or pipeline data
     * @returns {Promise<Object>} Load result
     */
    async loadPipeline(source) {
        try {
            let pipelineData;

            if (typeof source === 'string') {
                // Load from server by ID
                try {
                    const response = await this.apiClient.loadPipeline(source);
                    pipelineData = response.pipeline;
                } catch (error) {
                    throw new PipelineError(`Failed to load from server: ${error.message}`, 'LOAD_ERROR');
                }
            } else if (typeof source === 'object') {
                // Load from provided data
                pipelineData = source;
            } else {
                throw new PipelineError('Invalid pipeline source', 'INVALID_SOURCE');
            }

            // Validate pipeline data
            this.validatePipelineData(pipelineData);

            // Clear current pipeline
            this.componentManager.clear();

            // Load components and connections
            this.componentManager.loadFromData(pipelineData);

            // Update metadata
            this.setPipelineMetadata(pipelineData.metadata || {});

            this.eventBus.emit('pipeline:loaded', { pipelineData });

            return {
                success: true,
                componentCount: pipelineData.components?.length || 0,
                connectionCount: pipelineData.connections?.length || 0
            };
        } catch (error) {
            throw new PipelineError(`Load failed: ${error.message}`, 'LOAD_ERROR');
        }
    }

    /**
     * Execute pipeline query
     * @param {string} query - Query text
     * @param {Object} options - Execution options
     * @returns {Promise<Object>} Query result
     */
    async executeQuery(query, options = {}) {
        try {
            // Validate pipeline before execution
            const validation = await this.validatePipeline();
            if (!validation.isValid) {
                throw new PipelineError(
                    `Pipeline validation failed: ${validation.issues.join(', ')}`,
                    'VALIDATION_ERROR'
                );
            }

            const pipelineConfig = this.getPipelineConfiguration();
            
            const startTime = Date.now();
            
            this.eventBus.emit('query:started', { query, options });

            const result = await this.apiClient.executeQuery(query, pipelineConfig);
            
            const executionTime = Date.now() - startTime;

            const enhancedResult = {
                ...result,
                executionTime,
                query,
                pipelineId: this.pipelineMetadata.id,
                timestamp: new Date().toISOString()
            };

            this.eventBus.emit('query:completed', { result: enhancedResult });

            return enhancedResult;
        } catch (error) {
            this.eventBus.emit('query:failed', { error, query });
            throw new PipelineError(`Query execution failed: ${error.message}`, 'EXECUTION_ERROR');
        }
    }

    /**
     * Export pipeline configuration
     * @param {string} format - Export format ('json', 'yaml', 'python')
     * @returns {Object} Export result
     */
    exportPipeline(format = 'json') {
        try {
            const pipelineData = this.preparePipelineData();

            let exportData;
            let filename;
            let mimeType;

            switch (format.toLowerCase()) {
                case 'json':
                    exportData = JSON.stringify(pipelineData, null, 2);
                    filename = `${this.generateFilename()}.json`;
                    mimeType = 'application/json';
                    break;

                case 'yaml':
                    exportData = this.convertToYAML(pipelineData);
                    filename = `${this.generateFilename()}.yaml`;
                    mimeType = 'text/yaml';
                    break;

                case 'python':
                    exportData = this.convertToPythonCode(pipelineData);
                    filename = `${this.generateFilename()}.py`;
                    mimeType = 'text/x-python';
                    break;

                default:
                    throw new Error(`Unsupported export format: ${format}`);
            }

            return {
                data: exportData,
                filename,
                mimeType,
                format
            };
        } catch (error) {
            throw new PipelineError(`Export failed: ${error.message}`, 'EXPORT_ERROR');
        }
    }

    /**
     * Import pipeline from file
     * @param {File} file - Pipeline file
     * @returns {Promise<Object>} Import result
     */
    async importPipeline(file) {
        try {
            const fileContent = await this.readFile(file);
            let pipelineData;

            if (file.name.endsWith('.json')) {
                pipelineData = JSON.parse(fileContent);
            } else if (file.name.endsWith('.yaml') || file.name.endsWith('.yml')) {
                pipelineData = this.parseYAML(fileContent);
            } else {
                throw new Error('Unsupported file format. Please use JSON or YAML.');
            }

            await this.loadPipeline(pipelineData);

            return {
                success: true,
                filename: file.name,
                size: file.size
            };
        } catch (error) {
            throw new PipelineError(`Import failed: ${error.message}`, 'IMPORT_ERROR');
        }
    }

    /**
     * Get pipeline configuration for API
     * @returns {Object} Pipeline configuration
     */
    getPipelineConfiguration() {
        const config = this.componentManager.getPipelineConfig();
        
        return {
            ...config,
            metadata: this.pipelineMetadata,
            version: '2.0.0',
            framework: 'RAG Builder'
        };
    }

    /**
     * Prepare pipeline data for saving
     * @returns {Object} Pipeline data
     * @private
     */
    preparePipelineData() {
        const config = this.componentManager.getPipelineConfig();
        
        return {
            metadata: {
                ...this.pipelineMetadata,
                exportedAt: new Date().toISOString()
            },
            ...config,
            version: '2.0.0',
            framework: 'RAG Builder'
        };
    }

    /**
     * Validate pipeline data structure
     * @param {Object} pipelineData - Pipeline data to validate
     * @private
     */
    validatePipelineData(pipelineData) {
        if (!pipelineData || typeof pipelineData !== 'object') {
            throw new Error('Invalid pipeline data format');
        }

        if (!pipelineData.components || !Array.isArray(pipelineData.components)) {
            throw new Error('Pipeline must contain components array');
        }

        if (!pipelineData.connections || !Array.isArray(pipelineData.connections)) {
            throw new Error('Pipeline must contain connections array');
        }

        // Validate component structure
        pipelineData.components.forEach((component, index) => {
            if (!component.id || !component.type || !component.subtype) {
                throw new Error(`Invalid component at index ${index}: missing required fields`);
            }
        });
    }

    /**
     * Save pipeline to localStorage
     * @param {Object} pipelineData - Pipeline data
     * @private
     */
    saveToLocalStorage(pipelineData) {
        try {
            const key = `ragbuilder_pipeline_${Date.now()}`;
            localStorage.setItem(key, JSON.stringify(pipelineData));
            
            // Also save as current pipeline
            localStorage.setItem('ragbuilder_current_pipeline', JSON.stringify(pipelineData));
        } catch (error) {
            console.warn('Failed to save to localStorage:', error);
        }
    }

    /**
     * Download pipeline as file
     * @param {Object} pipelineData - Pipeline data
     * @private
     */
    downloadPipelineFile(pipelineData) {
        const dataStr = JSON.stringify(pipelineData, null, 2);
        const blob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const link = document.createElement('a');
        link.href = url;
        link.download = `${this.generateFilename()}.json`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        URL.revokeObjectURL(url);
    }

    /**
     * Generate filename based on pipeline name and timestamp
     * @returns {string} Generated filename
     * @private
     */
    generateFilename() {
        const name = this.pipelineMetadata.name || 'rag_pipeline';
        const timestamp = new Date().toISOString().slice(0, 16).replace(/[:.]/g, '-');
        return `${name.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_${timestamp}`;
    }

    /**
     * Perform auto-save
     * @private
     */
    async performAutoSave() {
        if (!this.hasUnsavedChanges()) {
            return;
        }

        try {
            const pipelineData = this.preparePipelineData();
            localStorage.setItem('ragbuilder_autosave', JSON.stringify(pipelineData));
            
            this.eventBus.emit('pipeline:autosaved', { pipelineData });
        } catch (error) {
            console.warn('Auto-save failed:', error);
        }
    }

    /**
     * Check if pipeline has unsaved changes
     * @returns {boolean} Has unsaved changes
     * @private
     */
    hasUnsavedChanges() {
        return this.componentManager.getAllComponents().length > 0;
    }

    /**
     * Read file content
     * @param {File} file - File to read
     * @returns {Promise<string>} File content
     * @private
     */
    readFile(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = () => reject(new Error('Failed to read file'));
            reader.readAsText(file);
        });
    }

    /**
     * Convert pipeline data to YAML format
     * @param {Object} data - Pipeline data
     * @returns {string} YAML string
     * @private
     */
    convertToYAML(data) {
        // Simple YAML conversion (for complex scenarios, use a proper YAML library)
        return JSON.stringify(data, null, 2)
            .replace(/"/g, '')
            .replace(/,$/gm, '')
            .replace(/\{$/gm, '')
            .replace(/\}$/gm, '');
    }

    /**
     * Convert pipeline data to Python code
     * @param {Object} data - Pipeline data
     * @returns {string} Python code
     * @private
     */
    convertToPythonCode(data) {
        let pythonCode = '# RAG Builder Pipeline Configuration\n';
        pythonCode += '# Generated automatically - do not edit manually\n\n';
        pythonCode += 'from ragbuilder import Pipeline, Component\n\n';
        pythonCode += 'def create_pipeline():\n';
        pythonCode += '    pipeline = Pipeline()\n\n';
        
        // Add components
        data.components.forEach(component => {
            pythonCode += `    # ${component.name}\n`;
            pythonCode += `    ${component.id} = Component(\n`;
            pythonCode += `        type="${component.type}",\n`;
            pythonCode += `        subtype="${component.subtype}",\n`;
            pythonCode += `        config=${JSON.stringify(component.config, null, 8)}\n`;
            pythonCode += '    )\n';
            pythonCode += `    pipeline.add_component(${component.id})\n\n`;
        });
        
        // Add connections
        data.connections.forEach(connection => {
            pythonCode += `    pipeline.connect("${connection.from}", "${connection.to}")\n`;
        });
        
        pythonCode += '\n    return pipeline\n\n';
        pythonCode += 'if __name__ == "__main__":\n';
        pythonCode += '    pipeline = create_pipeline()\n';
        pythonCode += '    print("Pipeline created successfully")\n';
        
        return pythonCode;
    }

    /**
     * Parse YAML content
     * @param {string} yamlContent - YAML content
     * @returns {Object} Parsed data
     * @private
     */
    parseYAML(yamlContent) {
        // Simple YAML parsing (for complex scenarios, use a proper YAML library)
        try {
            return JSON.parse(yamlContent);
        } catch {
            throw new Error('Invalid YAML format');
        }
    }

    /**
     * Destroy pipeline manager
     */
    destroy() {
        if (this.autoSaveTimer) {
            clearInterval(this.autoSaveTimer);
        }
        
        window.removeEventListener('beforeunload', this.performAutoSave);
        this.eventBus.removeAllListeners('component:*');
    }
}

/**
 * Pipeline Error class
 */
class PipelineError extends Error {
    constructor(message, code = 'PIPELINE_ERROR', details = null) {
        super(message);
        this.name = 'PipelineError';
        this.code = code;
        this.details = details;
        this.timestamp = new Date().toISOString();
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { PipelineManager, PipelineError };
}