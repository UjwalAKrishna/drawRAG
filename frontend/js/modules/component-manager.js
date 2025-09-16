// Component Manager - Handles component library and templates
export class ComponentManager {
    constructor(eventBus) {
        this.eventBus = eventBus;
        this.componentLibrary = new Map();
        this.templates = new Map();
        this.categories = ['datasource', 'vectordb', 'llm', 'processor'];
    }
    
    async initialize() {
        await this.loadComponentLibrary();
        this.setupComponentPalette();
        this.setupEventListeners();
    }
    
    async loadComponentLibrary() {
        // Define available components
        const components = [
            // Data Sources
            {
                type: 'datasource',
                subtype: 'sqlite',
                name: 'SQLite',
                icon: '🗄️',
                description: 'SQLite database connection',
                category: 'Data Sources',
                inputs: [],
                outputs: ['documents'],
                config: {
                    connectionString: { type: 'string', required: true, placeholder: 'sqlite:///data.db' },
                    tableName: { type: 'string', required: true, placeholder: 'documents' },
                    textColumn: { type: 'string', required: true, placeholder: 'content' }
                }
            },
            {
                type: 'datasource',
                subtype: 'upload',
                name: 'File Upload',
                icon: '📄',
                description: 'Upload documents directly',
                category: 'Data Sources',
                inputs: [],
                outputs: ['documents'],
                config: {
                    allowedTypes: { type: 'array', default: ['.txt', '.pdf', '.docx'] },
                    maxSize: { type: 'string', default: '10MB' }
                }
            },
            {
                type: 'datasource',
                subtype: 'postgres',
                name: 'PostgreSQL',
                icon: '🐘',
                description: 'PostgreSQL database connection',
                category: 'Data Sources',
                inputs: [],
                outputs: ['documents'],
                config: {
                    connectionString: { type: 'string', required: true, placeholder: 'postgresql://user:pass@localhost/db' },
                    tableName: { type: 'string', required: true, placeholder: 'documents' },
                    textColumn: { type: 'string', required: true, placeholder: 'content' }
                }
            },
            
            // Vector Databases
            {
                type: 'vectordb',
                subtype: 'chroma',
                name: 'ChromaDB',
                icon: '🎨',
                description: 'ChromaDB vector database',
                category: 'Vector Databases',
                inputs: ['documents'],
                outputs: ['vectors', 'search_results'],
                config: {
                    collectionName: { type: 'string', required: true, placeholder: 'documents' },
                    embeddingModel: { type: 'select', options: ['sentence-transformers/all-MiniLM-L6-v2', 'sentence-transformers/all-mpnet-base-v2'] },
                    chunkSize: { type: 'number', default: 1000, min: 100, max: 4000 }
                }
            },
            {
                type: 'vectordb',
                subtype: 'faiss',
                name: 'FAISS',
                icon: '🔢',
                description: 'Facebook AI Similarity Search',
                category: 'Vector Databases',
                inputs: ['documents'],
                outputs: ['vectors', 'search_results'],
                config: {
                    indexType: { type: 'select', options: ['HNSW', 'IVF', 'Flat'] },
                    dimension: { type: 'number', default: 384 },
                    metric: { type: 'select', options: ['cosine', 'euclidean', 'inner_product'] }
                }
            },
            {
                type: 'vectordb',
                subtype: 'pinecone',
                name: 'Pinecone',
                icon: '🌲',
                description: 'Pinecone vector database',
                category: 'Vector Databases',
                inputs: ['documents'],
                outputs: ['vectors', 'search_results'],
                config: {
                    apiKey: { type: 'string', required: true, sensitive: true },
                    indexName: { type: 'string', required: true, placeholder: 'documents' },
                    dimension: { type: 'number', default: 1536 }
                }
            },
            
            // LLMs
            {
                type: 'llm',
                subtype: 'openai',
                name: 'OpenAI GPT',
                icon: '🧠',
                description: 'OpenAI GPT models',
                category: 'LLMs',
                inputs: ['context', 'query'],
                outputs: ['response'],
                config: {
                    apiKey: { type: 'string', required: true, sensitive: true },
                    modelName: { type: 'select', options: ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo'] },
                    temperature: { type: 'range', min: 0, max: 1, step: 0.1, default: 0.7 },
                    maxTokens: { type: 'number', default: 2048, min: 1, max: 8192 }
                }
            },
            {
                type: 'llm',
                subtype: 'anthropic',
                name: 'Anthropic Claude',
                icon: '🎭',
                description: 'Anthropic Claude models',
                category: 'LLMs',
                inputs: ['context', 'query'],
                outputs: ['response'],
                config: {
                    apiKey: { type: 'string', required: true, sensitive: true },
                    modelName: { type: 'select', options: ['claude-3-sonnet', 'claude-3-opus', 'claude-3-haiku'] },
                    temperature: { type: 'range', min: 0, max: 1, step: 0.1, default: 0.7 },
                    maxTokens: { type: 'number', default: 2048, min: 1, max: 8192 }
                }
            },
            {
                type: 'llm',
                subtype: 'local',
                name: 'Local Model',
                icon: '🏠',
                description: 'Local or self-hosted model',
                category: 'LLMs',
                inputs: ['context', 'query'],
                outputs: ['response'],
                config: {
                    endpoint: { type: 'string', required: true, placeholder: 'http://localhost:11434' },
                    modelName: { type: 'string', required: true, placeholder: 'llama2' },
                    temperature: { type: 'range', min: 0, max: 1, step: 0.1, default: 0.7 }
                }
            }
        ];
        
        // Store components in library
        components.forEach(component => {
            const key = `${component.type}_${component.subtype}`;
            this.componentLibrary.set(key, component);
        });
    }
    
    setupComponentPalette() {
        const palette = document.querySelector('.component-palette');
        if (!palette) return;
        
        // Clear existing content
        palette.innerHTML = '<h3>Components</h3>';
        
        // Group components by category
        const categories = this.groupComponentsByCategory();
        
        categories.forEach((components, categoryName) => {
            const categoryDiv = document.createElement('div');
            categoryDiv.className = 'component-category';
            
            const header = document.createElement('h4');
            header.textContent = `${this.getCategoryIcon(categoryName)} ${categoryName}`;
            categoryDiv.appendChild(header);
            
            components.forEach(component => {
                const item = this.createComponentItem(component);
                categoryDiv.appendChild(item);
            });
            
            palette.appendChild(categoryDiv);
        });
    }
    
    groupComponentsByCategory() {
        const categories = new Map();
        
        this.componentLibrary.forEach(component => {
            const category = component.category;
            if (!categories.has(category)) {
                categories.set(category, []);
            }
            categories.get(category).push(component);
        });
        
        return categories;
    }
    
    createComponentItem(component) {
        const item = document.createElement('div');
        item.className = 'component-item';
        item.draggable = true;
        item.dataset.type = component.type;
        item.dataset.subtype = component.subtype;
        item.title = component.description;
        
        item.innerHTML = `
            <div class="component-icon">${component.icon}</div>
            <span class="component-label">${component.name}</span>
        `;
        
        // Add hover effects
        item.addEventListener('mouseenter', () => {
            this.showComponentTooltip(item, component);
        });
        
        item.addEventListener('mouseleave', () => {
            this.hideComponentTooltip();
        });
        
        return item;
    }
    
    showComponentTooltip(element, component) {
        const existing = document.querySelector('.component-tooltip');
        if (existing) existing.remove();
        
        const tooltip = document.createElement('div');
        tooltip.className = 'component-tooltip';
        tooltip.innerHTML = `
            <div class="tooltip-header">
                <span class="tooltip-icon">${component.icon}</span>
                <strong>${component.name}</strong>
            </div>
            <div class="tooltip-description">${component.description}</div>
            <div class="tooltip-io">
                <div class="tooltip-inputs">
                    <strong>Inputs:</strong> ${component.inputs.length ? component.inputs.join(', ') : 'None'}
                </div>
                <div class="tooltip-outputs">
                    <strong>Outputs:</strong> ${component.outputs.length ? component.outputs.join(', ') : 'None'}
                </div>
            </div>
        `;
        
        document.body.appendChild(tooltip);
        
        // Position tooltip
        const rect = element.getBoundingClientRect();
        tooltip.style.position = 'fixed';
        tooltip.style.left = (rect.right + 10) + 'px';
        tooltip.style.top = rect.top + 'px';
        tooltip.style.zIndex = '1000';
    }
    
    hideComponentTooltip() {
        const tooltip = document.querySelector('.component-tooltip');
        if (tooltip) tooltip.remove();
    }
    
    getCategoryIcon(category) {
        const icons = {
            'Data Sources': '📊',
            'Vector Databases': '🔍',
            'LLMs': '🤖',
            'Processors': '⚙️'
        };
        return icons[category] || '📦';
    }
    
    setupEventListeners() {
        this.eventBus.on('component:search', (query) => {
            this.searchComponents(query);
        });
        
        this.eventBus.on('component:filter', (filter) => {
            this.filterComponents(filter);
        });
    }
    
    searchComponents(query) {
        const items = document.querySelectorAll('.component-item');
        const searchTerm = query.toLowerCase();
        
        items.forEach(item => {
            const name = item.querySelector('.component-label').textContent.toLowerCase();
            const type = item.dataset.type.toLowerCase();
            const subtype = item.dataset.subtype.toLowerCase();
            
            const matches = name.includes(searchTerm) || 
                           type.includes(searchTerm) || 
                           subtype.includes(searchTerm);
            
            item.style.display = matches ? 'flex' : 'none';
        });
        
        // Hide empty categories
        document.querySelectorAll('.component-category').forEach(category => {
            const visibleItems = category.querySelectorAll('.component-item[style*="flex"], .component-item:not([style])');
            category.style.display = visibleItems.length > 0 ? 'block' : 'none';
        });
    }
    
    filterComponents(filter) {
        const items = document.querySelectorAll('.component-item');
        
        items.forEach(item => {
            if (!filter || filter === 'all') {
                item.style.display = 'flex';
            } else {
                const matches = item.dataset.type === filter;
                item.style.display = matches ? 'flex' : 'none';
            }
        });
        
        // Update category visibility
        document.querySelectorAll('.component-category').forEach(category => {
            const visibleItems = category.querySelectorAll('.component-item[style*="flex"], .component-item:not([style])');
            category.style.display = visibleItems.length > 0 ? 'block' : 'none';
        });
    }
    
    getComponent(type, subtype) {
        const key = `${type}_${subtype}`;
        return this.componentLibrary.get(key);
    }
    
    getComponentConfig(type, subtype) {
        const component = this.getComponent(type, subtype);
        return component ? component.config : {};
    }
    
    validateComponentConfig(type, subtype, config) {
        const component = this.getComponent(type, subtype);
        if (!component) return { valid: false, errors: ['Unknown component type'] };
        
        const errors = [];
        const componentConfig = component.config;
        
        // Check required fields
        Object.entries(componentConfig).forEach(([key, fieldConfig]) => {
            if (fieldConfig.required && (!config[key] || config[key] === '')) {
                errors.push(`${key} is required`);
            }
            
            // Type validation
            if (config[key] !== undefined && config[key] !== '') {
                const value = config[key];
                
                switch (fieldConfig.type) {
                    case 'number':
                        if (isNaN(value)) {
                            errors.push(`${key} must be a number`);
                        } else {
                            const num = Number(value);
                            if (fieldConfig.min !== undefined && num < fieldConfig.min) {
                                errors.push(`${key} must be at least ${fieldConfig.min}`);
                            }
                            if (fieldConfig.max !== undefined && num > fieldConfig.max) {
                                errors.push(`${key} must be at most ${fieldConfig.max}`);
                            }
                        }
                        break;
                        
                    case 'range':
                        const rangeValue = Number(value);
                        if (rangeValue < fieldConfig.min || rangeValue > fieldConfig.max) {
                            errors.push(`${key} must be between ${fieldConfig.min} and ${fieldConfig.max}`);
                        }
                        break;
                        
                    case 'select':
                        if (fieldConfig.options && !fieldConfig.options.includes(value)) {
                            errors.push(`${key} must be one of: ${fieldConfig.options.join(', ')}`);
                        }
                        break;
                }
            }
        });
        
        return {
            valid: errors.length === 0,
            errors
        };
    }
    
    // Template management
    saveComponentTemplate(component, templateName) {
        const template = {
            name: templateName,
            component: {
                type: component.type,
                subtype: component.subtype,
                config: component.config
            },
            created: new Date().toISOString()
        };
        
        this.templates.set(templateName, template);
        
        // Save to localStorage
        const savedTemplates = JSON.parse(localStorage.getItem('ragbuilder_templates') || '{}');
        savedTemplates[templateName] = template;
        localStorage.setItem('ragbuilder_templates', JSON.stringify(savedTemplates));
        
        this.eventBus.emit('template:saved', template);
    }
    
    loadComponentTemplates() {
        const savedTemplates = JSON.parse(localStorage.getItem('ragbuilder_templates') || '{}');
        
        Object.entries(savedTemplates).forEach(([name, template]) => {
            this.templates.set(name, template);
        });
        
        return Array.from(this.templates.values());
    }
    
    applyTemplate(templateName, targetComponent) {
        const template = this.templates.get(templateName);
        if (!template) return false;
        
        // Apply template configuration
        Object.assign(targetComponent.config, template.component.config);
        
        this.eventBus.emit('template:applied', { template, targetComponent });
        return true;
    }
    
    deleteTemplate(templateName) {
        this.templates.delete(templateName);
        
        const savedTemplates = JSON.parse(localStorage.getItem('ragbuilder_templates') || '{}');
        delete savedTemplates[templateName];
        localStorage.setItem('ragbuilder_templates', JSON.stringify(savedTemplates));
        
        this.eventBus.emit('template:deleted', templateName);
    }
    
    // Component suggestions
    getSuggestedComponents(existingComponents) {
        const suggestions = [];
        const types = existingComponents.map(c => c.type);
        
        // Suggest based on pipeline patterns
        if (!types.includes('datasource')) {
            suggestions.push({
                reason: 'Every pipeline needs a data source',
                components: this.getComponentsByType('datasource')
            });
        }
        
        if (types.includes('datasource') && !types.includes('vectordb')) {
            suggestions.push({
                reason: 'Vector database needed for similarity search',
                components: this.getComponentsByType('vectordb')
            });
        }
        
        if (types.includes('vectordb') && !types.includes('llm')) {
            suggestions.push({
                reason: 'LLM needed to generate responses',
                components: this.getComponentsByType('llm')
            });
        }
        
        return suggestions;
    }
    
    getComponentsByType(type) {
        return Array.from(this.componentLibrary.values()).filter(c => c.type === type);
    }
    
    // Bulk operations
    exportComponentLibrary() {
        const library = Object.fromEntries(this.componentLibrary);
        const dataStr = JSON.stringify(library, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        
        const link = document.createElement('a');
        link.href = URL.createObjectURL(dataBlob);
        link.download = 'component-library.json';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
    
    async importComponentLibrary(file) {
        try {
            const text = await file.text();
            const library = JSON.parse(text);
            
            Object.entries(library).forEach(([key, component]) => {
                this.componentLibrary.set(key, component);
            });
            
            this.setupComponentPalette(); // Refresh UI
            this.eventBus.emit('library:imported', { count: Object.keys(library).length });
            
            return { success: true, count: Object.keys(library).length };
        } catch (error) {
            this.eventBus.emit('error', error);
            return { success: false, error: error.message };
        }
    }
}