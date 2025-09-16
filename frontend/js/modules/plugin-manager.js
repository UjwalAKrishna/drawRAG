/**
 * Plugin Manager - Handles plugin discovery, upload, and management
 */
window.PluginManager = class PluginManager {
    constructor(apiClient, eventBus) {
        this.apiClient = apiClient;
        this.eventBus = eventBus;
        this.plugins = new Map();
        this.capabilities = new Map();
        this.categories = {
            'datasource': { name: 'Data Sources', icon: '📊', color: '#4CAF50' },
            'vectordb': { name: 'Vector Databases', icon: '🔍', color: '#2196F3' },
            'llm': { name: 'Language Models', icon: '🤖', color: '#FF9800' },
            'processor': { name: 'Text Processors', icon: '📝', color: '#9C27B0' },
            'embeddings': { name: 'Embedding Models', icon: '🔗', color: '#607D8B' },
            'other': { name: 'Other', icon: '⚙️', color: '#795548' }
        };
        
        this.setupEventListeners();
    }

    async initialize() {
        await this.loadPlugins();
        await this.loadCapabilities();
        this.renderPluginPalette();
        this.setupUploadArea();
    }

    async loadPlugins() {
        try {
            const response = await this.apiClient.get('/api/plugins/');
            this.plugins.clear();
            
            if (response.plugins) {
                response.plugins.forEach(pluginId => {
                    this.plugins.set(pluginId, { plugin_id: pluginId, capabilities: {} });
                });
            }
            
            this.eventBus.emit('plugins-loaded', { plugins: Array.from(this.plugins.values()) });
            // Also emit the event that UIManager is listening for
            this.eventBus.emit('plugins:loaded', { plugins: this.plugins });
        } catch (error) {
            console.error('Failed to load plugins:', error);
            this.eventBus.emit('error', { message: 'Failed to load plugins', error });
        }
    }

    async loadCapabilities() {
        try {
            const response = await this.apiClient.get('/api/capabilities/');
            this.capabilities.clear();
            
            if (response.capabilities) {
                Object.entries(response.capabilities).forEach(([capability, providers]) => {
                    this.capabilities.set(capability, providers);
                    
                    // Update plugin capabilities
                    providers.forEach(pluginId => {
                        if (this.plugins.has(pluginId)) {
                            const plugin = this.plugins.get(pluginId);
                            plugin.capabilities[capability] = true;
                        }
                    });
                });
            }
            
            this.eventBus.emit('capabilities-loaded', { capabilities: Object.fromEntries(this.capabilities) });
        } catch (error) {
            console.error('Failed to load capabilities:', error);
        }
    }

    categorizePlugin(plugin) {
        const pluginId = plugin.plugin_id.toLowerCase();
        const capabilities = plugin.capabilities || {};
        
        // Categorize based on capabilities
        if (capabilities.generate_text || capabilities.generate_response || pluginId.includes('llm') || pluginId.includes('gpt')) {
            return 'llm';
        }
        if (capabilities.store_vectors || capabilities.query_vectors || pluginId.includes('vector') || pluginId.includes('chroma') || pluginId.includes('faiss')) {
            return 'vectordb';
        }
        if (capabilities.generate_embeddings || pluginId.includes('embedding')) {
            return 'embeddings';
        }
        if (capabilities.get_documents || capabilities.load_data || pluginId.includes('data') || pluginId.includes('source')) {
            return 'datasource';
        }
        if (capabilities.clean_text || capabilities.process_text || pluginId.includes('process') || pluginId.includes('text')) {
            return 'processor';
        }
        
        return 'other';
    }

    renderPluginPalette() {
        const palette = document.querySelector('.component-palette');
        if (!palette) return;

        // Clear everything and rebuild with ONLY dynamic plugins
        const title = palette.querySelector('h3');
        palette.innerHTML = '';
        if (title) palette.appendChild(title);

        // Group plugins by category
        const categorizedPlugins = {};
        this.plugins.forEach(plugin => {
            const category = this.categorizePlugin(plugin);
            if (!categorizedPlugins[category]) {
                categorizedPlugins[category] = [];
            }
            categorizedPlugins[category].push(plugin);
        });
        
        console.log('Categorized plugins:', categorizedPlugins);

        // Render each category
        Object.entries(this.categories).forEach(([categoryKey, categoryInfo]) => {
            const plugins = categorizedPlugins[categoryKey] || [];
            if (plugins.length === 0) return;
            
            console.log(`Rendering category ${categoryKey}:`, plugins);

            const categoryDiv = document.createElement('div');
            categoryDiv.className = 'component-category';
            categoryDiv.innerHTML = `
                <h4 style="color: ${categoryInfo.color}">
                    ${categoryInfo.icon} ${categoryInfo.name}
                </h4>
            `;

            plugins.forEach((plugin, index) => {
                console.log(`Creating element for plugin ${index}:`, plugin);
                const pluginElement = this.createPluginElement(plugin, categoryInfo);
                categoryDiv.appendChild(pluginElement);
            });

            palette.appendChild(categoryDiv);
        });

        // Add upload area
        this.renderUploadArea(palette);
        
        // Notify that rendering is complete so UI Manager can set up drag handlers
        this.eventBus.emit('palette-rendered');
    }

    createPluginElement(plugin, categoryInfo) {
        const element = document.createElement('div');
        element.className = 'component-item';
        element.draggable = true;
        
        const category = this.categorizePlugin(plugin);
        const pluginType = plugin.plugin_id.toLowerCase().replace(/[^a-z0-9]/g, '_');
        
        // Set proper data attributes for drag and drop
        element.dataset.type = category;
        element.dataset.subtype = pluginType;
        element.dataset.pluginId = plugin.plugin_id;
        
        const capabilities = Object.keys(plugin.capabilities || {});
        const capabilityText = capabilities.length > 0 ? capabilities.slice(0, 2).join(', ') : 'Loading...';
        
        element.innerHTML = `
            <div class="component-icon" style="background: ${categoryInfo.color}20; color: ${categoryInfo.color}">
                ${categoryInfo.icon}
            </div>
            <div class="component-details">
                <span class="component-name">${plugin.plugin_id}</span>
                <small class="component-capabilities">${capabilityText}</small>
            </div>
            <div class="component-actions">
                <button class="btn-small reload-plugin" data-plugin-id="${plugin.plugin_id}" title="Reload Plugin">
                    🔄
                </button>
            </div>
        `;

        // Add drag event listeners
        element.addEventListener('dragstart', (e) => {
            e.dataTransfer.setData('application/json', JSON.stringify({
                type: 'plugin',
                plugin_id: plugin.plugin_id,
                category: this.categorizePlugin(plugin),
                capabilities: Object.keys(plugin.capabilities || {})
            }));
        });

        return element;
    }

    renderUploadArea(palette) {
        const uploadDiv = document.createElement('div');
        uploadDiv.className = 'component-category upload-area';
        uploadDiv.innerHTML = `
            <h4>📤 Upload Plugin</h4>
            <div class="upload-zone" id="plugin-upload-zone">
                <div class="upload-content">
                    <div class="upload-icon">📁</div>
                    <p>Drag & drop a Python plugin file here</p>
                    <p>or <button class="btn btn-small" id="browse-plugin-btn">Browse Files</button></p>
                    <input type="file" id="plugin-file-input" accept=".py" style="display: none;">
                </div>
            </div>
        `;
        palette.appendChild(uploadDiv);
    }

    setupUploadArea() {
        const uploadZone = document.getElementById('plugin-upload-zone');
        const fileInput = document.getElementById('plugin-file-input');
        const browseBtn = document.getElementById('browse-plugin-btn');

        if (!uploadZone || !fileInput || !browseBtn) return;

        // Browse button
        browseBtn.addEventListener('click', () => {
            fileInput.click();
        });

        fileInput.addEventListener('change', async (e) => {
            const files = Array.from(e.target.files);
            for (const file of files) {
                await this.uploadPlugin(file);
            }
            fileInput.value = ''; // Reset input
        });
    }

    async uploadPlugin(file) {
        try {
            this.eventBus.emit('plugin-upload-start', { filename: file.name });
            
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('/api/plugins/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`Upload failed: ${response.statusText}`);
            }

            const result = await response.json();
            
            this.eventBus.emit('plugin-upload-success', { 
                filename: file.name, 
                result 
            });

            // Reload plugins to show the new one
            await this.loadPlugins();
            await this.loadCapabilities();
            this.renderPluginPalette();

        } catch (error) {
            console.error('Plugin upload failed:', error);
            this.eventBus.emit('plugin-upload-error', { 
                filename: file.name, 
                error: error.message 
            });
        }
    }

    setupEventListeners() {
        // Plugin action buttons
        document.addEventListener('click', async (e) => {
            if (e.target.classList.contains('reload-plugin')) {
                const pluginId = e.target.dataset.pluginId;
                await this.reloadPlugin(pluginId);
            }
        });

        // Listen for plugin refresh requests
        this.eventBus.on('refresh-plugins', async () => {
            await this.loadPlugins();
            this.renderPluginPalette();
        });
    }

    async reloadPlugin(pluginId) {
        try {
            const response = await this.apiClient.post(`/api/plugins/${pluginId}/reload`);
            this.eventBus.emit('plugin-reloaded', { pluginId, success: response.success });
            
            // Refresh plugin list
            await this.loadPlugins();
            this.renderPluginPalette();
            
        } catch (error) {
            console.error('Plugin reload failed:', error);
            this.eventBus.emit('error', { message: `Failed to reload plugin ${pluginId}`, error });
        }
    }

    getPluginsByCategory(category) {
        return Array.from(this.plugins.values()).filter(plugin => 
            this.categorizePlugin(plugin) === category
        );
    }

    getPluginCapabilities(pluginId) {
        const plugin = this.plugins.get(pluginId);
        return plugin ? Object.keys(plugin.capabilities || {}) : [];
    }

    hasCapability(capability) {
        return this.capabilities.has(capability) && this.capabilities.get(capability).length > 0;
    }

    getCapabilityProviders(capability) {
        return this.capabilities.get(capability) || [];
    }
};