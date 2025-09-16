/**
 * Component Manager
 * Manages pipeline components, their configurations, and relationships
 */
class ComponentManager {
    constructor() {
        this.components = new Map();
        this.connections = [];
        this.componentCounter = 0;
        this.selectedComponentId = null;
        
        this.eventBus = new EventBus();
        this._initializeComponentDefinitions();
    }

    /**
     * Initialize component type definitions
     * @private
     */
    _initializeComponentDefinitions() {
        // This will be populated from API
        this.componentDefinitions = {};
    }

    /**
     * Load available plugins from API
     * @param {APIClient} apiClient - API client instance
     * @returns {Promise<void>}
     */
    async loadAvailablePlugins(apiClient) {
        try {
            const response = await apiClient.getPlugins();
            this.componentDefinitions = this.parsePluginsResponse(response);
            
            // Emit event that plugins are loaded
            this.eventBus.emit('plugins:loaded', { plugins: this.componentDefinitions });
        } catch (error) {
            console.warn('Failed to load plugins from API, using fallback definitions:', error);
            this.loadFallbackDefinitions();
        }
    }

    /**
     * Parse plugins response from API
     * @param {Object} response - API response
     * @returns {Object} Parsed component definitions
     */
    parsePluginsResponse(response) {
        const definitions = {};
        
        if (response.plugins && Array.isArray(response.plugins)) {
            response.plugins.forEach(plugin => {
                // Handle both string plugin names and plugin objects
                const pluginName = typeof plugin === 'string' ? plugin : (plugin.name || 'unknown');
                const category = this.categorizePlugin(pluginName);
                const pluginType = pluginName.toLowerCase().replace(/[^a-z0-9]/g, '_');
                
                if (!definitions[category]) {
                    definitions[category] = {};
                }
                
                definitions[category][pluginType] = {
                    name: pluginName,
                    icon: this.getPluginIcon(category, pluginType),
                    category: category,
                    defaultConfig: {},
                    requiredFields: [],
                    description: `${pluginName} plugin`,
                    version: '1.0.0',
                    capabilities: []
                };
            });
        }
        
        return definitions;
    }

    /**
     * Categorize plugin based on its name
     * @param {string} pluginName - Plugin name
     * @returns {string} Category
     */
    categorizePlugin(pluginName) {
        const name = pluginName.toLowerCase();
        const capabilities = [];
        
        // Check by capabilities first
        if (capabilities.some(cap => cap.includes('generate') || cap.includes('chat') || cap.includes('completion'))) {
            return 'llm';
        }
        if (capabilities.some(cap => cap.includes('embed') || cap.includes('vector'))) {
            return 'embedding';
        }
        if (capabilities.some(cap => cap.includes('search') || cap.includes('retrieve') || cap.includes('index'))) {
            return 'vectordb';
        }
        if (capabilities.some(cap => cap.includes('load') || cap.includes('read') || cap.includes('fetch'))) {
            return 'datasource';
        }
        
        // Fallback to name-based categorization
        if (name.includes('llm') || name.includes('gpt') || name.includes('claude') || name.includes('ollama')) {
            return 'llm';
        }
        if (name.includes('chroma') || name.includes('faiss') || name.includes('pinecone') || name.includes('vector')) {
            return 'vectordb';
        }
        if (name.includes('embed')) {
            return 'embedding';
        }
        if (name.includes('sql') || name.includes('database') || name.includes('file') || name.includes('load')) {
            return 'datasource';
        }
        if (name.includes('process') || name.includes('text') || name.includes('clean')) {
            return 'processor';
        }
        
        return 'other'; // Default category
    }

    /**
     * Get icon for plugin based on category and type
     * @param {string} category - Plugin category
     * @param {string} type - Plugin type
     * @returns {string} Icon emoji
     */
    getPluginIcon(category, type) {
        const iconMap = {
            datasource: {
                default: '📊',
                sqlite: '🗄️',
                postgres: '🐘',
                mysql: '🐬',
                file: '📄',
                upload: '📤'
            },
            vectordb: {
                default: '🔍',
                chroma: '🎨',
                faiss: '🔢',
                pinecone: '🌲',
                weaviate: '🕸️'
            },
            llm: {
                default: '🤖',
                openai: '🧠',
                gpt: '🧠',
                claude: '🎭',
                anthropic: '🎭',
                ollama: '🦙',
                lmstudio: '🎬'
            },
            embedding: {
                default: '🔗',
                openai: '🔗',
                sentence_transformers: '⚡'
            }
        };
        
        return iconMap[category]?.[type] || iconMap[category]?.default || '🔧';
    }

    /**
     * Load fallback definitions when API is unavailable
     */
    loadFallbackDefinitions() {
        this.componentDefinitions = {
            datasource: {
                file_upload: {
                    name: 'File Upload',
                    icon: '📄',
                    category: 'datasource',
                    defaultConfig: {
                        file_types: ['pdf', 'txt', 'docx'],
                        max_size_mb: 10
                    },
                    requiredFields: ['file_types'],
                    description: 'Upload and process documents'
                }
            },
            llm: {
                openai: {
                    name: 'OpenAI GPT',
                    icon: '🧠',
                    category: 'llm',
                    defaultConfig: {
                        api_key: '',
                        model: 'gpt-4',
                        temperature: 0.7
                    },
                    requiredFields: ['api_key', 'model'],
                    description: 'OpenAI language model'
                }
            },
            vectordb: {
                chroma: {
                    name: 'ChromaDB',
                    icon: '🎨',
                    category: 'vectordb',
                    defaultConfig: {
                        collection_name: 'rag_collection'
                    },
                    requiredFields: ['collection_name'],
                    description: 'ChromaDB vector database'
                }
            }
        };
    }

    /**
     * Create a new component
     * @param {string} type - Component type (datasource, vectordb, llm, embedding)
     * @param {string} subtype - Component subtype
     * @param {number} x - X position
     * @param {number} y - Y position
     * @returns {Object} Created component
     */
    createComponent(type, subtype, x, y) {
        const componentId = `component-${++this.componentCounter}`;
        const definition = this.getComponentDefinition(type, subtype);
        
        if (!definition) {
            throw new Error(`Unknown component type: ${type}.${subtype}`);
        }

        const component = {
            id: componentId,
            type: type,
            subtype: subtype,
            name: definition.name,
            icon: definition.icon,
            category: definition.category,
            position: { x, y },
            config: { ...definition.defaultConfig },
            status: ComponentStatus.UNCONFIGURED,
            connections: {
                input: [],
                output: []
            },
            metadata: {
                createdAt: new Date().toISOString(),
                lastModified: new Date().toISOString()
            }
        };

        this.components.set(componentId, component);
        this.eventBus.emit(ComponentEvents.CREATED, { component });
        
        return component;
    }

    /**
     * Update component configuration
     * @param {string} componentId - Component ID
     * @param {Object} config - New configuration
     * @returns {boolean} Success status
     */
    updateComponentConfig(componentId, config) {
        const component = this.components.get(componentId);
        if (!component) {
            throw new Error(`Component not found: ${componentId}`);
        }

        // Validate required fields
        const definition = this.getComponentDefinition(component.type, component.subtype);
        const isValid = this.validateComponentConfig(config, definition);

        // Update component
        component.config = { ...component.config, ...config };
        component.status = isValid ? ComponentStatus.CONFIGURED : ComponentStatus.UNCONFIGURED;
        component.metadata.lastModified = new Date().toISOString();

        this.eventBus.emit(ComponentEvents.UPDATED, { component });
        return true;
    }

    /**
     * Delete a component
     * @param {string} componentId - Component ID
     * @returns {boolean} Success status
     */
    deleteComponent(componentId) {
        const component = this.components.get(componentId);
        if (!component) {
            return false;
        }

        // Remove all connections involving this component
        this.removeComponentConnections(componentId);

        // Remove component
        this.components.delete(componentId);
        
        if (this.selectedComponentId === componentId) {
            this.selectedComponentId = null;
        }

        this.eventBus.emit(ComponentEvents.DELETED, { componentId, component });
        return true;
    }

    /**
     * Move component to new position
     * @param {string} componentId - Component ID
     * @param {number} x - New X position
     * @param {number} y - New Y position
     * @returns {boolean} Success status
     */
    moveComponent(componentId, x, y) {
        const component = this.components.get(componentId);
        if (!component) {
            return false;
        }

        component.position = { x, y };
        component.metadata.lastModified = new Date().toISOString();
        
        this.eventBus.emit(ComponentEvents.MOVED, { component });
        return true;
    }

    /**
     * Create connection between components
     * @param {string} fromComponentId - Source component ID
     * @param {string} toComponentId - Target component ID
     * @returns {Object|null} Created connection
     */
    createConnection(fromComponentId, toComponentId) {
        const fromComponent = this.components.get(fromComponentId);
        const toComponent = this.components.get(toComponentId);
        
        if (!fromComponent || !toComponent) {
            throw new Error('Invalid component IDs for connection');
        }

        // Validate connection rules
        if (!this.canConnect(fromComponent, toComponent)) {
            throw new Error('Invalid connection: incompatible component types');
        }

        const connectionId = `connection-${Date.now()}`;
        const connection = {
            id: connectionId,
            from: fromComponentId,
            to: toComponentId,
            type: this.getConnectionType(fromComponent, toComponent),
            createdAt: new Date().toISOString()
        };

        // Update component connections
        fromComponent.connections.output.push(connectionId);
        toComponent.connections.input.push(connectionId);

        this.connections.push(connection);
        this.eventBus.emit(ComponentEvents.CONNECTED, { connection });
        
        return connection;
    }

    /**
     * Remove connection
     * @param {string} connectionId - Connection ID
     * @returns {boolean} Success status
     */
    removeConnection(connectionId) {
        const connectionIndex = this.connections.findIndex(conn => conn.id === connectionId);
        if (connectionIndex === -1) {
            return false;
        }

        const connection = this.connections[connectionIndex];
        
        // Update component connections
        const fromComponent = this.components.get(connection.from);
        const toComponent = this.components.get(connection.to);
        
        if (fromComponent) {
            fromComponent.connections.output = fromComponent.connections.output.filter(id => id !== connectionId);
        }
        
        if (toComponent) {
            toComponent.connections.input = toComponent.connections.input.filter(id => id !== connectionId);
        }

        this.connections.splice(connectionIndex, 1);
        this.eventBus.emit(ComponentEvents.DISCONNECTED, { connection });
        
        return true;
    }

    /**
     * Remove all connections for a component
     * @param {string} componentId - Component ID
     * @private
     */
    removeComponentConnections(componentId) {
        const connectionsToRemove = this.connections.filter(
            conn => conn.from === componentId || conn.to === componentId
        );
        
        connectionsToRemove.forEach(connection => {
            this.removeConnection(connection.id);
        });
    }

    /**
     * Validate if two components can be connected
     * @param {Object} fromComponent - Source component
     * @param {Object} toComponent - Target component
     * @returns {boolean} Can connect
     */
    canConnect(fromComponent, toComponent) {
        const validConnections = {
            datasource: ['embedding', 'vectordb'],
            embedding: ['vectordb'],
            vectordb: ['llm'],
            llm: []
        };

        return validConnections[fromComponent.category]?.includes(toComponent.category) || false;
    }

    /**
     * Get connection type between components
     * @param {Object} fromComponent - Source component
     * @param {Object} toComponent - Target component
     * @returns {string} Connection type
     */
    getConnectionType(fromComponent, toComponent) {
        if (fromComponent.category === 'datasource' && toComponent.category === 'embedding') {
            return 'text_to_embedding';
        }
        if (fromComponent.category === 'embedding' && toComponent.category === 'vectordb') {
            return 'embedding_to_storage';
        }
        if (fromComponent.category === 'vectordb' && toComponent.category === 'llm') {
            return 'retrieval_to_generation';
        }
        return 'data_flow';
    }

    /**
     * Get component definition
     * @param {string} type - Component type
     * @param {string} subtype - Component subtype
     * @returns {Object|null} Component definition
     */
    getComponentDefinition(type, subtype) {
        return this.componentDefinitions[type]?.[subtype] || null;
    }

    /**
     * Validate component configuration
     * @param {Object} config - Configuration to validate
     * @param {Object} definition - Component definition
     * @returns {boolean} Is valid
     */
    validateComponentConfig(config, definition) {
        if (!definition || !definition.requiredFields) {
            return false;
        }

        return definition.requiredFields.every(field => {
            const value = config[field];
            return value !== undefined && value !== null && value !== '';
        });
    }

    /**
     * Get pipeline configuration for API
     * @returns {Object} Pipeline configuration
     */
    getPipelineConfig() {
        const componentArray = Array.from(this.components.values());
        
        return {
            components: componentArray.map(component => ({
                id: component.id,
                type: component.type,
                subtype: component.subtype,
                config: component.config,
                position: component.position
            })),
            connections: this.connections,
            metadata: {
                totalComponents: this.components.size,
                totalConnections: this.connections.length,
                lastModified: new Date().toISOString()
            }
        };
    }

    /**
     * Validate entire pipeline
     * @returns {Object} Validation result
     */
    validatePipeline() {
        const issues = [];
        const warnings = [];
        
        // Check for required component types
        const componentsByCategory = this.getComponentsByCategory();
        
        if (!componentsByCategory.datasource || componentsByCategory.datasource.length === 0) {
            issues.push('Pipeline must have at least one data source');
        }
        
        if (!componentsByCategory.vectordb || componentsByCategory.vectordb.length === 0) {
            issues.push('Pipeline must have at least one vector database');
        }
        
        if (!componentsByCategory.llm || componentsByCategory.llm.length === 0) {
            issues.push('Pipeline must have at least one LLM');
        }

        // Check component configurations
        Array.from(this.components.values()).forEach(component => {
            if (component.status === ComponentStatus.UNCONFIGURED) {
                issues.push(`Component "${component.name}" is not properly configured`);
            }
        });

        // Check connections
        if (this.connections.length === 0 && this.components.size > 1) {
            warnings.push('Components are not connected');
        }

        return {
            isValid: issues.length === 0,
            issues,
            warnings,
            componentCount: this.components.size,
            connectionCount: this.connections.length
        };
    }

    /**
     * Get components grouped by category
     * @returns {Object} Components by category
     */
    getComponentsByCategory() {
        const componentArray = Array.from(this.components.values());
        return componentArray.reduce((acc, component) => {
            if (!acc[component.category]) {
                acc[component.category] = [];
            }
            acc[component.category].push(component);
            return acc;
        }, {});
    }

    /**
     * Get component by ID
     * @param {string} componentId - Component ID
     * @returns {Object|null} Component
     */
    getComponent(componentId) {
        return this.components.get(componentId) || null;
    }

    /**
     * Get all components
     * @returns {Array} All components
     */
    getAllComponents() {
        return Array.from(this.components.values());
    }

    /**
     * Get all connections
     * @returns {Array} All connections
     */
    getAllConnections() {
        return [...this.connections];
    }

    /**
     * Clear all components and connections
     */
    clear() {
        this.components.clear();
        this.connections = [];
        this.selectedComponentId = null;
        this.componentCounter = 0;
        this.eventBus.emit(ComponentEvents.CLEARED, {});
    }

    /**
     * Load pipeline from data
     * @param {Object} pipelineData - Pipeline data
     */
    loadFromData(pipelineData) {
        this.clear();
        
        if (pipelineData.components) {
            pipelineData.components.forEach(componentData => {
                const component = {
                    ...componentData,
                    metadata: componentData.metadata || {
                        createdAt: new Date().toISOString(),
                        lastModified: new Date().toISOString()
                    }
                };
                this.components.set(component.id, component);
                
                // Update counter to avoid ID conflicts
                const componentNumber = parseInt(component.id.split('-')[1]);
                if (componentNumber >= this.componentCounter) {
                    this.componentCounter = componentNumber;
                }
            });
        }
        
        if (pipelineData.connections) {
            this.connections = [...pipelineData.connections];
        }
        
        this.eventBus.emit(ComponentEvents.LOADED, { pipelineData });
    }
}

/**
 * Component status enumeration
 */
const ComponentStatus = {
    UNCONFIGURED: 'unconfigured',
    CONFIGURED: 'configured',
    ERROR: 'error',
    PROCESSING: 'processing'
};

/**
 * Component events enumeration
 */
const ComponentEvents = {
    CREATED: 'component:created',
    UPDATED: 'component:updated',
    DELETED: 'component:deleted',
    MOVED: 'component:moved',
    CONNECTED: 'component:connected',
    DISCONNECTED: 'component:disconnected',
    CLEARED: 'component:cleared',
    LOADED: 'component:loaded'
};

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ComponentManager, ComponentStatus, ComponentEvents };
}