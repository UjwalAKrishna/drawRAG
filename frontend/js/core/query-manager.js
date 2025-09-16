/**
 * Query Manager
 * Handles query execution and result processing
 */
class QueryManager {
    constructor(pipelineManager, apiClient, eventBus) {
        this.pipelineManager = pipelineManager;
        this.apiClient = apiClient;
        this.eventBus = eventBus;
        this.queryHistory = [];
        this.maxHistorySize = 50;
        this.currentQuery = null;
        
        this.loadQueryHistory();
    }

    /**
     * Execute a query through the pipeline
     * @param {string} query - Query text
     * @param {Object} options - Query options
     * @returns {Promise<Object>} Query result
     */
    async executeQuery(query, options = {}) {
        try {
            // Validate inputs
            if (!query || typeof query !== 'string' || !query.trim()) {
                throw new QueryError('Query cannot be empty', 'INVALID_QUERY');
            }

            // Validate pipeline
            const validation = this.pipelineManager.validatePipeline();
            if (!validation.isValid) {
                throw new QueryError(
                    `Pipeline validation failed: ${validation.issues.join(', ')}`,
                    'PIPELINE_INVALID'
                );
            }

            const queryId = this.generateQueryId();
            const startTime = Date.now();

            this.currentQuery = {
                id: queryId,
                query: query.trim(),
                status: 'executing',
                startTime,
                options
            };

            // Emit query started event
            this.eventBus.emit('query:started', {
                queryId,
                query: this.currentQuery.query,
                options
            });

            // Get pipeline configuration
            const pipelineConfig = this.pipelineManager.getPipelineConfiguration();

            // Execute query through API
            const result = await this.apiClient.executeQuery(this.currentQuery.query, pipelineConfig);

            const executionTime = Date.now() - startTime;

            // Process and enhance result
            const processedResult = this.processQueryResult(result, {
                queryId,
                query: this.currentQuery.query,
                executionTime,
                pipelineConfig
            });

            // Update current query status
            this.currentQuery.status = 'completed';
            this.currentQuery.result = processedResult;
            this.currentQuery.executionTime = executionTime;

            // Add to history
            this.addToHistory(this.currentQuery);

            // Emit query completed event
            this.eventBus.emit('query:completed', {
                queryId,
                result: processedResult,
                executionTime
            });

            return processedResult;

        } catch (error) {
            const executionTime = Date.now() - (this.currentQuery?.startTime || Date.now());
            
            // Update current query status
            if (this.currentQuery) {
                this.currentQuery.status = 'failed';
                this.currentQuery.error = error.message;
                this.currentQuery.executionTime = executionTime;
                this.addToHistory(this.currentQuery);
            }

            // Emit query failed event
            this.eventBus.emit('query:failed', {
                queryId: this.currentQuery?.id,
                query: this.currentQuery?.query,
                error,
                executionTime
            });

            // Re-throw with additional context
            if (error instanceof QueryError) {
                throw error;
            }
            
            throw new QueryError(`Query execution failed: ${error.message}`, 'EXECUTION_ERROR', {
                originalError: error,
                query: this.currentQuery?.query
            });
        } finally {
            this.currentQuery = null;
        }
    }

    /**
     * Process and enhance query result
     * @param {Object} rawResult - Raw result from API
     * @param {Object} context - Query context
     * @returns {Object} Processed result
     * @private
     */
    processQueryResult(rawResult, context) {
        const processedResult = {
            // Core result data
            answer: rawResult.answer || 'No answer provided',
            sources: this.processSources(rawResult.sources || []),
            confidence: rawResult.confidence || null,
            
            // Metadata
            queryId: context.queryId,
            query: context.query,
            executionTime: context.executionTime,
            timestamp: new Date().toISOString(),
            
            // Pipeline information
            pipelineId: context.pipelineConfig.metadata?.id,
            componentsUsed: this.extractUsedComponents(context.pipelineConfig),
            
            // Performance metrics
            metrics: this.calculateMetrics(rawResult, context),
            
            // Additional data
            tokensUsed: rawResult.tokens_used || null,
            model: rawResult.model || null,
            rawResult: rawResult
        };

        return processedResult;
    }

    /**
     * Process sources array
     * @param {Array} sources - Raw sources
     * @returns {Array} Processed sources
     * @private
     */
    processSources(sources) {
        return sources.map((source, index) => {
            if (typeof source === 'string') {
                return {
                    id: `source_${index}`,
                    content: source,
                    relevance: null,
                    metadata: {}
                };
            }
            
            return {
                id: source.id || `source_${index}`,
                content: source.content || source.text || source,
                relevance: source.relevance || source.score || null,
                metadata: source.metadata || {},
                title: source.title || null,
                url: source.url || null
            };
        });
    }

    /**
     * Extract used components from pipeline config
     * @param {Object} pipelineConfig - Pipeline configuration
     * @returns {Array} Used components
     * @private
     */
    extractUsedComponents(pipelineConfig) {
        if (!pipelineConfig.components) return [];
        
        return pipelineConfig.components
            .filter(component => component.status === 'configured')
            .map(component => ({
                id: component.id,
                type: component.type,
                subtype: component.subtype,
                name: component.name || `${component.type}_${component.subtype}`
            }));
    }

    /**
     * Calculate performance metrics
     * @param {Object} rawResult - Raw result
     * @param {Object} context - Query context
     * @returns {Object} Metrics
     * @private
     */
    calculateMetrics(rawResult, context) {
        return {
            executionTime: context.executionTime,
            executionTimeFormatted: this.formatExecutionTime(context.executionTime),
            sourceCount: rawResult.sources?.length || 0,
            confidence: rawResult.confidence || null,
            tokensUsed: rawResult.tokens_used || null,
            cost: this.calculateCost(rawResult),
            cacheHit: rawResult.cache_hit || false
        };
    }

    /**
     * Format execution time for display
     * @param {number} timeMs - Time in milliseconds
     * @returns {string} Formatted time
     * @private
     */
    formatExecutionTime(timeMs) {
        if (timeMs < 1000) {
            return `${timeMs}ms`;
        } else if (timeMs < 60000) {
            return `${(timeMs / 1000).toFixed(1)}s`;
        } else {
            const minutes = Math.floor(timeMs / 60000);
            const seconds = ((timeMs % 60000) / 1000).toFixed(0);
            return `${minutes}m ${seconds}s`;
        }
    }

    /**
     * Calculate estimated cost
     * @param {Object} rawResult - Raw result
     * @returns {Object|null} Cost information
     * @private
     */
    calculateCost(rawResult) {
        if (!rawResult.tokens_used || !rawResult.model) {
            return null;
        }

        // Simplified cost calculation (would need real pricing data)
        const costPerToken = this.getModelCostPerToken(rawResult.model);
        if (!costPerToken) return null;

        const estimatedCost = rawResult.tokens_used * costPerToken;
        
        return {
            estimatedCost,
            formattedCost: `$${estimatedCost.toFixed(6)}`,
            tokensUsed: rawResult.tokens_used,
            model: rawResult.model
        };
    }

    /**
     * Get cost per token for a model
     * @param {string} model - Model name
     * @returns {number|null} Cost per token
     * @private
     */
    getModelCostPerToken(model) {
        // Simplified pricing (would be loaded from configuration)
        const pricing = {
            'gpt-4': 0.00006,
            'gpt-3.5-turbo': 0.000002,
            'claude-3-sonnet': 0.000015,
            'claude-3-haiku': 0.000005
        };
        
        return pricing[model] || null;
    }

    /**
     * Generate unique query ID
     * @returns {string} Query ID
     * @private
     */
    generateQueryId() {
        return `query_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Add query to history
     * @param {Object} queryData - Query data
     * @private
     */
    addToHistory(queryData) {
        this.queryHistory.unshift({
            ...queryData,
            addedAt: new Date().toISOString()
        });

        // Limit history size
        if (this.queryHistory.length > this.maxHistorySize) {
            this.queryHistory = this.queryHistory.slice(0, this.maxHistorySize);
        }

        this.saveQueryHistory();
        this.eventBus.emit('query:history-updated', { history: this.queryHistory });
    }

    /**
     * Get query history
     * @param {Object} options - Filter options
     * @returns {Array} Query history
     */
    getQueryHistory(options = {}) {
        let history = [...this.queryHistory];

        // Filter by status
        if (options.status) {
            history = history.filter(query => query.status === options.status);
        }

        // Filter by date range
        if (options.startDate || options.endDate) {
            history = history.filter(query => {
                const queryDate = new Date(query.addedAt);
                if (options.startDate && queryDate < new Date(options.startDate)) {
                    return false;
                }
                if (options.endDate && queryDate > new Date(options.endDate)) {
                    return false;
                }
                return true;
            });
        }

        // Limit results
        if (options.limit) {
            history = history.slice(0, options.limit);
        }

        return history;
    }

    /**
     * Clear query history
     */
    clearHistory() {
        this.queryHistory = [];
        this.saveQueryHistory();
        this.eventBus.emit('query:history-cleared', {});
    }

    /**
     * Get query by ID
     * @param {string} queryId - Query ID
     * @returns {Object|null} Query data
     */
    getQueryById(queryId) {
        return this.queryHistory.find(query => query.id === queryId) || null;
    }

    /**
     * Re-run a previous query
     * @param {string} queryId - Query ID to re-run
     * @returns {Promise<Object>} Query result
     */
    async reRunQuery(queryId) {
        const previousQuery = this.getQueryById(queryId);
        if (!previousQuery) {
            throw new QueryError(`Query not found: ${queryId}`, 'QUERY_NOT_FOUND');
        }

        return this.executeQuery(previousQuery.query, previousQuery.options);
    }

    /**
     * Get query statistics
     * @returns {Object} Statistics
     */
    getStatistics() {
        const totalQueries = this.queryHistory.length;
        const successfulQueries = this.queryHistory.filter(q => q.status === 'completed').length;
        const failedQueries = this.queryHistory.filter(q => q.status === 'failed').length;
        
        const executionTimes = this.queryHistory
            .filter(q => q.executionTime)
            .map(q => q.executionTime);
        
        const averageExecutionTime = executionTimes.length > 0 
            ? executionTimes.reduce((sum, time) => sum + time, 0) / executionTimes.length
            : 0;

        return {
            totalQueries,
            successfulQueries,
            failedQueries,
            successRate: totalQueries > 0 ? (successfulQueries / totalQueries) * 100 : 0,
            averageExecutionTime,
            averageExecutionTimeFormatted: this.formatExecutionTime(averageExecutionTime),
            lastQueryAt: this.queryHistory[0]?.addedAt || null
        };
    }

    /**
     * Export query history
     * @param {string} format - Export format ('json', 'csv')
     * @returns {Object} Export data
     */
    exportHistory(format = 'json') {
        const history = this.getQueryHistory();
        
        if (format === 'json') {
            return {
                data: JSON.stringify(history, null, 2),
                filename: `query_history_${new Date().toISOString().split('T')[0]}.json`,
                mimeType: 'application/json'
            };
        }
        
        if (format === 'csv') {
            const csvHeaders = ['Timestamp', 'Query', 'Status', 'Execution Time', 'Answer'];
            const csvRows = history.map(query => [
                query.addedAt,
                `"${query.query.replace(/"/g, '""')}"`,
                query.status,
                query.executionTime || '',
                query.result ? `"${query.result.answer.replace(/"/g, '""')}"` : ''
            ]);
            
            const csvContent = [csvHeaders.join(','), ...csvRows.map(row => row.join(','))].join('\n');
            
            return {
                data: csvContent,
                filename: `query_history_${new Date().toISOString().split('T')[0]}.csv`,
                mimeType: 'text/csv'
            };
        }
        
        throw new Error(`Unsupported export format: ${format}`);
    }

    /**
     * Save query history to localStorage
     * @private
     */
    saveQueryHistory() {
        try {
            localStorage.setItem('ragbuilder_query_history', JSON.stringify(this.queryHistory));
        } catch (error) {
            console.warn('Failed to save query history:', error);
        }
    }

    /**
     * Load query history from localStorage
     * @private
     */
    loadQueryHistory() {
        try {
            const saved = localStorage.getItem('ragbuilder_query_history');
            if (saved) {
                this.queryHistory = JSON.parse(saved);
                // Limit to max size in case it was saved with a larger limit
                if (this.queryHistory.length > this.maxHistorySize) {
                    this.queryHistory = this.queryHistory.slice(0, this.maxHistorySize);
                }
            }
        } catch (error) {
            console.warn('Failed to load query history:', error);
            this.queryHistory = [];
        }
    }

    /**
     * Get current query status
     * @returns {Object|null} Current query status
     */
    getCurrentQueryStatus() {
        return this.currentQuery ? { ...this.currentQuery } : null;
    }

    /**
     * Cancel current query if possible
     * @returns {boolean} Whether cancellation was successful
     */
    cancelCurrentQuery() {
        if (this.currentQuery) {
            // In a real implementation, this would cancel the API request
            this.currentQuery.status = 'cancelled';
            this.currentQuery.executionTime = Date.now() - this.currentQuery.startTime;
            this.addToHistory(this.currentQuery);
            
            this.eventBus.emit('query:cancelled', {
                queryId: this.currentQuery.id,
                query: this.currentQuery.query
            });
            
            this.currentQuery = null;
            return true;
        }
        return false;
    }

    /**
     * Destroy query manager and cleanup
     */
    destroy() {
        this.saveQueryHistory();
        this.queryHistory = [];
        this.currentQuery = null;
    }
}

/**
 * Query Error class
 */
class QueryError extends Error {
    constructor(message, code = 'QUERY_ERROR', details = null) {
        super(message);
        this.name = 'QueryError';
        this.code = code;
        this.details = details;
        this.timestamp = new Date().toISOString();
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { QueryManager, QueryError };
}