// Pipeline Builder - Handles drag-and-drop pipeline creation
export class PipelineBuilder {
    constructor(eventBus, apiClient) {
        this.eventBus = eventBus;
        this.apiClient = apiClient;
        this.canvas = null;
        this.components = new Map();
        this.connections = [];
        this.selectedComponent = null;
        this.currentPipeline = null;
        this.draggedElement = null;
        this.connectionMode = false;
        this.connectionStart = null;
    }
    
    async initialize() {
        this.canvas = document.getElementById('pipeline-canvas');
        this.setupDragAndDrop();
        this.setupCanvasEvents();
        this.setupEventListeners();
        this.clearCanvas();
    }
    
    setupDragAndDrop() {
        // Handle component dragging from palette
        const componentItems = document.querySelectorAll('.component-item');
        componentItems.forEach(item => {
            item.addEventListener('dragstart', (e) => {
                this.draggedElement = {
                    type: item.dataset.type,
                    subtype: item.dataset.subtype,
                    icon: item.querySelector('.component-icon').textContent,
                    name: item.querySelector('span').textContent
                };
                e.dataTransfer.effectAllowed = 'copy';
            });
        });
        
        // Handle canvas drop zone
        this.canvas.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'copy';
            this.canvas.classList.add('drag-over');
        });
        
        this.canvas.addEventListener('dragleave', (e) => {
            if (!this.canvas.contains(e.relatedTarget)) {
                this.canvas.classList.remove('drag-over');
            }
        });
        
        this.canvas.addEventListener('drop', (e) => {
            e.preventDefault();
            this.canvas.classList.remove('drag-over');
            
            if (this.draggedElement) {
                const rect = this.canvas.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                
                this.addComponent(this.draggedElement, x, y);
                this.draggedElement = null;
            }
        });
    }
    
    setupCanvasEvents() {
        // Handle component selection and movement
        this.canvas.addEventListener('click', (e) => {
            if (e.target.closest('.pipeline-component')) {
                const component = e.target.closest('.pipeline-component');
                this.selectComponent(component.dataset.id);
            } else {
                this.deselectAll();
            }
        });
        
        // Handle connection creation
        this.canvas.addEventListener('click', (e) => {
            if (e.target.classList.contains('connection-point')) {
                this.handleConnectionPoint(e.target);
            }
        });
    }
    
    setupEventListeners() {
        this.eventBus.on('ui:save-pipeline', () => this.savePipeline());
        this.eventBus.on('ui:load-pipeline', () => this.loadPipelineDialog());
        this.eventBus.on('ui:export-pipeline', () => this.exportPipeline());
        this.eventBus.on('ui:validate-pipeline', () => this.validatePipeline());
        this.eventBus.on('component:config-updated', (data) => {
            this.updateComponentConfig(data.componentId, data.config);
        });
    }
    
    addComponent(componentData, x, y) {
        const id = this.generateId();
        const component = {
            id,
            type: componentData.type,
            subtype: componentData.subtype,
            name: componentData.name,
            icon: componentData.icon,
            position: { x, y },
            config: this.getDefaultConfig(componentData.type, componentData.subtype),
            inputs: this.getComponentInputs(componentData.type),
            outputs: this.getComponentOutputs(componentData.type)
        };
        
        this.components.set(id, component);
        this.renderComponent(component);
        this.updatePipelineStats();
        this.hideCanvasPlaceholder();
        
        this.eventBus.emit('component:added', component);
        return component;
    }
    
    renderComponent(component) {
        const element = document.createElement('div');
        element.className = 'pipeline-component';
        element.dataset.id = component.id;
        element.style.left = component.position.x + 'px';
        element.style.top = component.position.y + 'px';
        
        element.innerHTML = `
            <div class="component-header">
                <span class="component-icon">${component.icon}</span>
                <span class="component-name">${component.name}</span>
                <button class="component-delete" title="Delete component">&times;</button>
            </div>
            <div class="component-body">
                <div class="component-type">${component.subtype}</div>
                ${this.renderConnectionPoints(component)}
            </div>
        `;
        
        // Make component draggable
        this.makeComponentDraggable(element);
        
        // Add delete functionality
        element.querySelector('.component-delete').addEventListener('click', (e) => {
            e.stopPropagation();
            this.removeComponent(component.id);
        });
        
        this.canvas.appendChild(element);
    }
    
    renderConnectionPoints(component) {
        let html = '';
        
        // Input connection points
        if (component.inputs.length > 0) {
            html += '<div class="connection-points inputs">';
            component.inputs.forEach((input, index) => {
                html += `<div class="connection-point input" data-component="${component.id}" data-type="input" data-index="${index}" title="${input}"></div>`;
            });
            html += '</div>';
        }
        
        // Output connection points
        if (component.outputs.length > 0) {
            html += '<div class="connection-points outputs">';
            component.outputs.forEach((output, index) => {
                html += `<div class="connection-point output" data-component="${component.id}" data-type="output" data-index="${index}" title="${output}"></div>`;
            });
            html += '</div>';
        }
        
        return html;
    }
    
    makeComponentDraggable(element) {
        let isDragging = false;
        let startX, startY, initialX, initialY;
        
        element.addEventListener('mousedown', (e) => {
            if (e.target.classList.contains('component-delete') || 
                e.target.classList.contains('connection-point')) {
                return;
            }
            
            isDragging = true;
            startX = e.clientX;
            startY = e.clientY;
            
            const rect = element.getBoundingClientRect();
            const canvasRect = this.canvas.getBoundingClientRect();
            initialX = rect.left - canvasRect.left;
            initialY = rect.top - canvasRect.top;
            
            e.preventDefault();
        });
        
        document.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            
            const deltaX = e.clientX - startX;
            const deltaY = e.clientY - startY;
            
            const newX = Math.max(0, initialX + deltaX);
            const newY = Math.max(0, initialY + deltaY);
            
            element.style.left = newX + 'px';
            element.style.top = newY + 'px';
            
            // Update component position
            const component = this.components.get(element.dataset.id);
            if (component) {
                component.position = { x: newX, y: newY };
            }
            
            this.updateConnections();
        });
        
        document.addEventListener('mouseup', () => {
            isDragging = false;
        });
    }
    
    handleConnectionPoint(point) {
        const componentId = point.dataset.component;
        const type = point.dataset.type;
        const index = parseInt(point.dataset.index);
        
        if (!this.connectionMode) {
            // Start connection
            this.connectionMode = true;
            this.connectionStart = { componentId, type, index, element: point };
            point.classList.add('connecting');
            this.canvas.classList.add('connection-mode');
        } else {
            // Complete connection
            const end = { componentId, type, index, element: point };
            
            if (this.canConnect(this.connectionStart, end)) {
                this.createConnection(this.connectionStart, end);
            }
            
            this.exitConnectionMode();
        }
    }
    
    canConnect(start, end) {
        // Cannot connect to same component
        if (start.componentId === end.componentId) return false;
        
        // Must connect output to input
        if (start.type === end.type) return false;
        
        // Check if connection already exists
        const existingConnection = this.connections.find(conn =>
            (conn.from.componentId === start.componentId && conn.to.componentId === end.componentId) ||
            (conn.from.componentId === end.componentId && conn.to.componentId === start.componentId)
        );
        
        return !existingConnection;
    }
    
    createConnection(start, end) {
        // Ensure start is output, end is input
        const from = start.type === 'output' ? start : end;
        const to = start.type === 'input' ? start : end;
        
        const connection = {
            id: this.generateId(),
            from: from,
            to: to
        };
        
        this.connections.push(connection);
        this.renderConnection(connection);
        this.updatePipelineStats();
        
        this.eventBus.emit('connection:created', connection);
    }
    
    renderConnection(connection) {
        // Create SVG line for connection
        const svg = this.getOrCreateSVG();
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        line.setAttribute('class', 'connection-line');
        line.setAttribute('data-connection-id', connection.id);
        
        this.updateConnectionPath(connection, line);
        svg.appendChild(line);
        
        // Add click handler for deletion
        line.addEventListener('click', () => {
            this.removeConnection(connection.id);
        });
    }
    
    updateConnectionPath(connection, line) {
        const fromPoint = this.getConnectionPointPosition(connection.from);
        const toPoint = this.getConnectionPointPosition(connection.to);
        
        if (fromPoint && toPoint) {
            const path = this.generateConnectionPath(fromPoint, toPoint);
            line.setAttribute('d', path);
        }
    }
    
    generateConnectionPath(from, to) {
        const dx = to.x - from.x;
        const dy = to.y - from.y;
        const curve = Math.abs(dx) * 0.5;
        
        return `M ${from.x} ${from.y} C ${from.x + curve} ${from.y} ${to.x - curve} ${to.y} ${to.x} ${to.y}`;
    }
    
    getConnectionPointPosition(connectionInfo) {
        const element = document.querySelector(
            `[data-component="${connectionInfo.componentId}"] .connection-point[data-type="${connectionInfo.type}"][data-index="${connectionInfo.index}"]`
        );
        
        if (!element) return null;
        
        const rect = element.getBoundingClientRect();
        const canvasRect = this.canvas.getBoundingClientRect();
        
        return {
            x: rect.left + rect.width / 2 - canvasRect.left,
            y: rect.top + rect.height / 2 - canvasRect.top
        };
    }
    
    getOrCreateSVG() {
        let svg = this.canvas.querySelector('.connections-svg');
        if (!svg) {
            svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            svg.setAttribute('class', 'connections-svg');
            svg.style.position = 'absolute';
            svg.style.top = '0';
            svg.style.left = '0';
            svg.style.width = '100%';
            svg.style.height = '100%';
            svg.style.pointerEvents = 'none';
            this.canvas.appendChild(svg);
        }
        return svg;
    }
    
    updateConnections() {
        const svg = this.canvas.querySelector('.connections-svg');
        if (!svg) return;
        
        this.connections.forEach(connection => {
            const line = svg.querySelector(`[data-connection-id="${connection.id}"]`);
            if (line) {
                this.updateConnectionPath(connection, line);
            }
        });
    }
    
    exitConnectionMode() {
        this.connectionMode = false;
        this.connectionStart = null;
        this.canvas.classList.remove('connection-mode');
        
        document.querySelectorAll('.connection-point.connecting').forEach(point => {
            point.classList.remove('connecting');
        });
    }
    
    selectComponent(id) {
        this.deselectAll();
        this.selectedComponent = id;
        
        const element = document.querySelector(`[data-id="${id}"]`);
        if (element) {
            element.classList.add('selected');
        }
        
        const component = this.components.get(id);
        if (component) {
            this.eventBus.emit('component:selected', component);
        }
    }
    
    deselectAll() {
        this.selectedComponent = null;
        document.querySelectorAll('.pipeline-component.selected').forEach(el => {
            el.classList.remove('selected');
        });
    }
    
    removeComponent(id) {
        const component = this.components.get(id);
        if (!component) return;
        
        // Remove connections
        this.connections = this.connections.filter(conn => {
            if (conn.from.componentId === id || conn.to.componentId === id) {
                this.removeConnectionElement(conn.id);
                return false;
            }
            return true;
        });
        
        // Remove component element
        const element = document.querySelector(`[data-id="${id}"]`);
        if (element) {
            element.remove();
        }
        
        // Remove from components map
        this.components.delete(id);
        
        this.updatePipelineStats();
        this.showCanvasPlaceholderIfEmpty();
        
        this.eventBus.emit('component:removed', { id, component });
    }
    
    removeConnection(id) {
        this.removeConnectionElement(id);
        this.connections = this.connections.filter(conn => conn.id !== id);
        this.updatePipelineStats();
        
        this.eventBus.emit('connection:removed', id);
    }
    
    removeConnectionElement(id) {
        const line = document.querySelector(`[data-connection-id="${id}"]`);
        if (line) {
            line.remove();
        }
    }
    
    updateComponentConfig(componentId, config) {
        const component = this.components.get(componentId);
        if (component) {
            component.config = { ...component.config, ...config };
            component.name = config.name || component.name;
            
            // Update visual representation
            const element = document.querySelector(`[data-id="${componentId}"]`);
            if (element) {
                const nameElement = element.querySelector('.component-name');
                if (nameElement) {
                    nameElement.textContent = component.name;
                }
            }
            
            this.eventBus.emit('component:updated', component);
        }
    }
    
    updatePipelineStats() {
        const stats = {
            components: this.components.size,
            connections: this.connections.length,
            health: this.getPipelineHealth()
        };
        
        this.eventBus.emit('pipeline:updated', stats);
    }
    
    getPipelineHealth() {
        if (this.components.size === 0) return 'Empty';
        if (this.components.size === 1) return 'Incomplete';
        if (this.connections.length === 0) return 'Disconnected';
        
        // Check for complete pipeline (data source -> processing -> output)
        const hasDataSource = Array.from(this.components.values()).some(c => c.type === 'datasource');
        const hasLLM = Array.from(this.components.values()).some(c => c.type === 'llm');
        
        if (hasDataSource && hasLLM) return 'Ready';
        return 'Incomplete';
    }
    
    clearCanvas() {
        this.components.clear();
        this.connections = [];
        this.selectedComponent = null;
        
        // Remove all component elements
        document.querySelectorAll('.pipeline-component').forEach(el => el.remove());
        
        // Remove connections SVG
        const svg = this.canvas.querySelector('.connections-svg');
        if (svg) svg.remove();
        
        this.showCanvasPlaceholderIfEmpty();
        this.updatePipelineStats();
    }
    
    hideCanvasPlaceholder() {
        const placeholder = this.canvas.querySelector('.canvas-placeholder');
        if (placeholder) {
            placeholder.style.display = 'none';
        }
    }
    
    showCanvasPlaceholderIfEmpty() {
        if (this.components.size === 0) {
            const placeholder = this.canvas.querySelector('.canvas-placeholder');
            if (placeholder) {
                placeholder.style.display = 'block';
            }
        }
    }
    
    // Configuration helpers
    getDefaultConfig(type, subtype) {
        const configs = {
            datasource: {
                sqlite: { connectionString: 'sqlite:///data.db', tableName: 'documents', textColumn: 'content' },
                postgres: { connectionString: 'postgresql://user:pass@localhost/db', tableName: 'documents', textColumn: 'content' },
                upload: { allowedTypes: ['.txt', '.pdf', '.docx'], maxSize: '10MB' }
            },
            vectordb: {
                chroma: { collectionName: 'documents', embeddingModel: 'sentence-transformers/all-MiniLM-L6-v2', chunkSize: 1000 },
                faiss: { indexType: 'HNSW', dimension: 384, metric: 'cosine' },
                pinecone: { indexName: 'documents', dimension: 1536, metric: 'cosine' }
            },
            llm: {
                openai: { modelName: 'gpt-3.5-turbo', temperature: 0.7, maxTokens: 2048 },
                anthropic: { modelName: 'claude-3-sonnet', temperature: 0.7, maxTokens: 2048 },
                local: { modelName: 'local-model', temperature: 0.7, maxTokens: 2048 }
            }
        };
        
        return configs[type]?.[subtype] || {};
    }
    
    getComponentInputs(type) {
        const inputs = {
            datasource: [],
            vectordb: ['documents'],
            llm: ['context', 'query']
        };
        return inputs[type] || [];
    }
    
    getComponentOutputs(type) {
        const outputs = {
            datasource: ['documents'],
            vectordb: ['vectors', 'search_results'],
            llm: ['response']
        };
        return outputs[type] || [];
    }
    
    generateId() {
        return 'comp_' + Math.random().toString(36).substr(2, 9);
    }
    
    // Pipeline operations
    async savePipeline() {
        const pipeline = this.getCurrentPipeline();
        
        try {
            // Here you would typically save to backend
            localStorage.setItem('ragbuilder_pipeline', JSON.stringify(pipeline));
            this.eventBus.emit('pipeline:saved', pipeline);
            return { success: true, pipeline };
        } catch (error) {
            this.eventBus.emit('error', error);
            return { success: false, error: error.message };
        }
    }
    
    async loadPipelineDialog() {
        // Simple file input for now - could be enhanced with a proper dialog
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.json';
        
        input.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (file) {
                try {
                    const text = await file.text();
                    const pipeline = JSON.parse(text);
                    await this.loadPipeline(pipeline);
                } catch (error) {
                    this.eventBus.emit('error', new Error('Failed to load pipeline file'));
                }
            }
        });
        
        input.click();
    }
    
    async loadPipeline(pipelineData) {
        this.clearCanvas();
        
        if (!pipelineData || !pipelineData.components) return;
        
        // Load components
        for (const [id, componentData] of Object.entries(pipelineData.components)) {
            const component = { ...componentData, id };
            this.components.set(id, component);
            this.renderComponent(component);
        }
        
        // Load connections
        if (pipelineData.connections) {
            this.connections = [...pipelineData.connections];
            this.connections.forEach(connection => {
                this.renderConnection(connection);
            });
        }
        
        this.hideCanvasPlaceholder();
        this.updatePipelineStats();
        
        this.eventBus.emit('pipeline:loaded', pipelineData);
    }
    
    exportPipeline() {
        const pipeline = this.getCurrentPipeline();
        const dataStr = JSON.stringify(pipeline, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        
        const link = document.createElement('a');
        link.href = URL.createObjectURL(dataBlob);
        link.download = `pipeline_${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        this.eventBus.emit('pipeline:exported', pipeline);
    }
    
    async validatePipeline() {
        const pipeline = this.getCurrentPipeline();
        
        try {
            const result = await this.apiClient.validatePipeline(pipeline);
            this.eventBus.emit('pipeline:validated', result);
            return result;
        } catch (error) {
            this.eventBus.emit('error', error);
            return { success: false, error: error.message };
        }
    }
    
    getCurrentPipeline() {
        const components = {};
        this.components.forEach((component, id) => {
            components[id] = component;
        });
        
        return {
            name: document.getElementById('pipeline-name')?.value || 'Untitled Pipeline',
            description: document.getElementById('pipeline-description')?.value || '',
            components,
            connections: this.connections,
            metadata: {
                created: new Date().toISOString(),
                version: '1.0.0'
            }
        };
    }
    
    createNew() {
        this.clearCanvas();
        this.currentPipeline = null;
        this.eventBus.emit('pipeline:new');
    }
}