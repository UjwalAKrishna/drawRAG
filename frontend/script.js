// RAG Builder - Main JavaScript Application
class RAGBuilder {
    constructor() {
        this.components = new Map();
        this.connections = [];
        this.selectedComponent = null;
        this.draggedElement = null;
        this.componentCounter = 0;
        this.pipelineName = "";
        this.pipelineDescription = "";
        this.logs = [];
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupDragAndDrop();
        this.setupModal();
        this.setupTabs();
        this.updatePipelineStats();
        this.addLog('RAG Builder initialized', 'info');
    }

    setupEventListeners() {
        // Header buttons
        document.getElementById('save-pipeline-btn').addEventListener('click', () => this.savePipeline());
        document.getElementById('load-pipeline-btn').addEventListener('click', () => this.loadPipeline());
        document.getElementById('test-query-btn').addEventListener('click', () => this.openTestModal());
        document.getElementById('export-config-btn').addEventListener('click', () => this.exportConfig());
        
        // Pipeline tab buttons
        document.getElementById('validate-pipeline-btn').addEventListener('click', () => this.validatePipeline());
        document.getElementById('clear-logs-btn').addEventListener('click', () => this.clearLogs());
        
        // Pipeline settings
        document.getElementById('pipeline-name').addEventListener('input', (e) => {
            this.pipelineName = e.target.value;
            this.updatePipelineStats();
        });
        
        document.getElementById('pipeline-description').addEventListener('input', (e) => {
            this.pipelineDescription = e.target.value;
        });
        
        // Canvas click (deselect components)
        document.getElementById('pipeline-canvas').addEventListener('click', (e) => {
            if (e.target === e.currentTarget) {
                this.deselectComponent();
            }
        });
    }

    setupDragAndDrop() {
        const componentItems = document.querySelectorAll('.component-item');
        const canvas = document.getElementById('pipeline-canvas');

        // Make component items draggable
        componentItems.forEach(item => {
            item.addEventListener('dragstart', (e) => {
                this.draggedElement = {
                    type: item.dataset.type,
                    subtype: item.dataset.subtype,
                    icon: item.querySelector('.component-icon').textContent,
                    name: item.querySelector('span').textContent
                };
                item.classList.add('dragging');
            });

            item.addEventListener('dragend', () => {
                item.classList.remove('dragging');
            });
        });

        // Canvas drop zone
        canvas.addEventListener('dragover', (e) => {
            e.preventDefault();
            canvas.classList.add('drag-over');
        });

        canvas.addEventListener('dragleave', (e) => {
            if (!canvas.contains(e.relatedTarget)) {
                canvas.classList.remove('drag-over');
            }
        });

        canvas.addEventListener('drop', (e) => {
            e.preventDefault();
            canvas.classList.remove('drag-over');
            
            if (this.draggedElement) {
                const rect = canvas.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                
                this.createComponent(this.draggedElement, x, y);
                this.draggedElement = null;
            }
        });
    }

    setupModal() {
        const modal = document.getElementById('test-query-modal');
        const closeBtn = document.getElementById('close-modal');
        const runQueryBtn = document.getElementById('run-query-btn');

        closeBtn.addEventListener('click', () => this.closeTestModal());
        runQueryBtn.addEventListener('click', () => this.runTestQuery());

        // Close modal on outside click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.closeTestModal();
            }
        });
    }

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
                document.getElementById(`${targetTab}-tab`).classList.add('active');
            });
        });
    }

    createComponent(elementData, x, y) {
        const componentId = `component-${++this.componentCounter}`;
        
        const component = {
            id: componentId,
            type: elementData.type,
            subtype: elementData.subtype,
            name: elementData.name,
            icon: elementData.icon,
            x: x,
            y: y,
            config: this.getDefaultConfig(elementData.type, elementData.subtype),
            status: 'unconfigured'
        };

        this.components.set(componentId, component);
        this.renderComponent(component);
        this.selectComponent(componentId);
        this.updateConnections();
        this.updatePipelineStats();
        this.addLog(`Added ${component.name} component`, 'success');
    }

    getDefaultConfig(type, subtype) {
        const configs = {
            datasource: {
                sqlite: { database_path: '', table_name: '', text_column: '' },
                upload: { file_types: ['pdf', 'txt'], max_size: '10MB' },
                postgres: { host: 'localhost', port: 5432, database: '', username: '', password: '', table_name: '', text_column: '' }
            },
            vectordb: {
                chroma: { collection_name: 'rag_collection', persist_directory: './chroma_db' },
                faiss: { index_type: 'flat', dimension: 1536 },
                pinecone: { api_key: '', environment: '', index_name: '' }
            },
            llm: {
                openai: { api_key: '', model: 'gpt-4o-mini', temperature: 0.7, max_tokens: 1000 },
                anthropic: { api_key: '', model: 'claude-3-sonnet-20240229', temperature: 0.7, max_tokens: 1000 },
                ollama: { base_url: 'http://localhost:11434', model: 'llama2', temperature: 0.7 },
                lmstudio: { base_url: 'http://localhost:1234', model: 'local-model', temperature: 0.7 }
            }
        };

        return configs[type]?.[subtype] || {};
    }

    renderComponent(component) {
        const canvas = document.getElementById('pipeline-canvas');
        
        const componentEl = document.createElement('div');
        componentEl.className = 'dropped-component';
        componentEl.id = component.id;
        componentEl.style.left = `${component.x}px`;
        componentEl.style.top = `${component.y}px`;
        
        componentEl.innerHTML = `
            <div class="component-header">
                <span class="component-icon">${component.icon}</span>
                <div>
                    <div class="component-title">${component.name}</div>
                    <div class="component-status ${component.status}">${this.getStatusText(component.status)}</div>
                </div>
            </div>
        `;

        // Make component draggable within canvas
        this.makeComponentDraggable(componentEl);
        
        // Component selection
        componentEl.addEventListener('click', (e) => {
            e.stopPropagation();
            this.selectComponent(component.id);
        });

        canvas.appendChild(componentEl);
        
        // Hide placeholder if this is the first component
        const placeholder = canvas.querySelector('.canvas-placeholder');
        if (placeholder) {
            placeholder.style.display = 'none';
        }
    }

    makeComponentDraggable(element) {
        let isDragging = false;
        let startX, startY, initialX, initialY;

        element.addEventListener('mousedown', (e) => {
            if (e.target.closest('.component-header')) {
                isDragging = true;
                startX = e.clientX;
                startY = e.clientY;
                initialX = parseInt(element.style.left);
                initialY = parseInt(element.style.top);
                element.style.cursor = 'grabbing';
            }
        });

        document.addEventListener('mousemove', (e) => {
            if (isDragging) {
                const deltaX = e.clientX - startX;
                const deltaY = e.clientY - startY;
                element.style.left = `${initialX + deltaX}px`;
                element.style.top = `${initialY + deltaY}px`;
                
                // Update component position in data
                const componentId = element.id;
                const component = this.components.get(componentId);
                if (component) {
                    component.x = initialX + deltaX;
                    component.y = initialY + deltaY;
                }
                
                this.updateConnections();
            }
        });

        document.addEventListener('mouseup', () => {
            if (isDragging) {
                isDragging = false;
                element.style.cursor = 'move';
            }
        });
    }

    selectComponent(componentId) {
        // Remove previous selection
        document.querySelectorAll('.dropped-component').forEach(el => {
            el.classList.remove('selected');
        });

        // Select new component
        const componentEl = document.getElementById(componentId);
        if (componentEl) {
            componentEl.classList.add('selected');
            this.selectedComponent = componentId;
            this.showComponentConfig(componentId);
        }
    }

    deselectComponent() {
        document.querySelectorAll('.dropped-component').forEach(el => {
            el.classList.remove('selected');
        });
        this.selectedComponent = null;
        this.hideComponentConfig();
    }

    showComponentConfig(componentId) {
        const component = this.components.get(componentId);
        if (!component) return;

        const configPanel = document.getElementById('config-content');
        
        let configHTML = `
            <h4>${component.icon} ${component.name}</h4>
            <form id="component-config-form">
        `;

        // Generate form fields based on component config
        Object.entries(component.config).forEach(([key, value]) => {
            const fieldName = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            const inputType = key.includes('password') || key.includes('key') ? 'password' : 'text';
            
            configHTML += `
                <div class="form-group">
                    <label for="${key}">${fieldName}:</label>
                    <input type="${inputType}" id="${key}" name="${key}" value="${value}" />
                </div>
            `;
        });

        configHTML += `
                <button type="submit" class="btn btn-primary">Save Configuration</button>
                <button type="button" class="btn btn-secondary" id="delete-component">Delete Component</button>
            </form>
        `;

        configPanel.innerHTML = configHTML;

        // Setup form submission
        document.getElementById('component-config-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveComponentConfig(componentId);
        });

        // Setup delete button
        document.getElementById('delete-component').addEventListener('click', () => {
            this.deleteComponent(componentId);
        });
    }

    hideComponentConfig() {
        const configPanel = document.getElementById('config-content');
        configPanel.innerHTML = '<p>Select a component to configure its settings</p>';
    }

    saveComponentConfig(componentId) {
        const component = this.components.get(componentId);
        if (!component) return;

        const form = document.getElementById('component-config-form');
        const formData = new FormData(form);
        
        // Update component config
        Object.keys(component.config).forEach(key => {
            if (formData.has(key)) {
                component.config[key] = formData.get(key);
            }
        });

        // Update component status
        const isConfigured = Object.values(component.config).some(value => value && value.toString().trim() !== '');
        component.status = isConfigured ? 'configured' : 'unconfigured';

        // Update UI
        this.updateComponentStatus(componentId);
        
        // Show success message
        this.showNotification('Configuration saved successfully!', 'success');
        this.addLog(`Configured ${component.name}`, 'info');
        this.updatePipelineStats();
    }

    deleteComponent(componentId) {
        if (confirm('Are you sure you want to delete this component?')) {
            // Remove from DOM
            const componentEl = document.getElementById(componentId);
            if (componentEl) {
                componentEl.remove();
            }

            // Remove from data
            this.components.delete(componentId);
            
            // Remove connections
            this.connections = this.connections.filter(conn => 
                conn.from !== componentId && conn.to !== componentId
            );

            // Clear selection
            this.deselectComponent();
            this.updateConnections();
            this.updatePipelineStats();
            this.addLog(`Deleted component`, 'warning');

            // Show placeholder if no components left
            if (this.components.size === 0) {
                const placeholder = document.querySelector('.canvas-placeholder');
                if (placeholder) {
                    placeholder.style.display = 'block';
                }
            }
        }
    }

    updateComponentStatus(componentId) {
        const component = this.components.get(componentId);
        const componentEl = document.getElementById(componentId);
        
        if (component && componentEl) {
            const statusEl = componentEl.querySelector('.component-status');
            statusEl.textContent = this.getStatusText(component.status);
            statusEl.className = `component-status ${component.status}`;
        }
    }

    getStatusText(status) {
        const statusTexts = {
            unconfigured: 'Not configured',
            configured: 'Configured',
            error: 'Error'
        };
        return statusTexts[status] || status;
    }

    updateConnections() {
        // Auto-connect components based on their types and positions
        const componentArray = Array.from(this.components.values());
        const datasources = componentArray.filter(c => c.type === 'datasource');
        const vectordbs = componentArray.filter(c => c.type === 'vectordb');
        const llms = componentArray.filter(c => c.type === 'llm');

        this.connections = [];

        // Connect datasource to vectordb
        if (datasources.length > 0 && vectordbs.length > 0) {
            this.connections.push({
                from: datasources[0].id,
                to: vectordbs[0].id
            });
        }

        // Connect vectordb to llm
        if (vectordbs.length > 0 && llms.length > 0) {
            this.connections.push({
                from: vectordbs[0].id,
                to: llms[0].id
            });
        }

        this.renderConnections();
    }

    renderConnections() {
        // Remove existing connection lines
        document.querySelectorAll('.connection-line').forEach(line => line.remove());

        this.connections.forEach(connection => {
            this.drawConnection(connection.from, connection.to);
        });
    }

    drawConnection(fromId, toId) {
        const fromEl = document.getElementById(fromId);
        const toEl = document.getElementById(toId);
        
        if (!fromEl || !toEl) return;

        const canvas = document.getElementById('pipeline-canvas');
        const canvasRect = canvas.getBoundingClientRect();
        
        const fromRect = fromEl.getBoundingClientRect();
        const toRect = toEl.getBoundingClientRect();

        const fromX = fromRect.right - canvasRect.left;
        const fromY = fromRect.top + fromRect.height / 2 - canvasRect.top;
        const toX = toRect.left - canvasRect.left;
        const toY = toRect.top + toRect.height / 2 - canvasRect.top;

        const line = document.createElement('div');
        line.className = 'connection-line';
        line.style.position = 'absolute';
        line.style.left = `${Math.min(fromX, toX)}px`;
        line.style.top = `${Math.min(fromY, toY)}px`;
        line.style.width = `${Math.abs(toX - fromX)}px`;
        line.style.height = `${Math.abs(toY - fromY)}px`;

        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        
        const startX = fromX < toX ? 0 : Math.abs(toX - fromX);
        const startY = fromY < toY ? 0 : Math.abs(toY - fromY);
        const endX = fromX < toX ? Math.abs(toX - fromX) : 0;
        const endY = fromY < toY ? Math.abs(toY - fromY) : 0;

        const controlX1 = startX + (endX - startX) * 0.5;
        const controlY1 = startY;
        const controlX2 = startX + (endX - startX) * 0.5;
        const controlY2 = endY;

        const pathData = `M ${startX} ${startY} C ${controlX1} ${controlY1}, ${controlX2} ${controlY2}, ${endX} ${endY}`;
        
        path.setAttribute('d', pathData);
        path.setAttribute('class', 'connection-path');
        
        svg.appendChild(path);
        line.appendChild(svg);
        canvas.appendChild(line);
    }

    openTestModal() {
        const modal = document.getElementById('test-query-modal');
        modal.classList.add('show');
    }

    closeTestModal() {
        const modal = document.getElementById('test-query-modal');
        modal.classList.remove('show');
        document.getElementById('query-result').classList.remove('show');
        document.getElementById('test-query-input').value = '';
    }

    async runTestQuery() {
        const query = document.getElementById('test-query-input').value.trim();
        if (!query) {
            this.showNotification('Please enter a question', 'error');
            return;
        }

        const resultDiv = document.getElementById('query-result');
        resultDiv.innerHTML = '<p>🔄 Processing your query...</p>';
        resultDiv.classList.add('show');

        try {
            // Get pipeline configuration
            const pipelineConfig = this.getPipelineConfig();
            
            // Simulate API call (replace with actual backend call)
            const response = await this.simulateQuery(query, pipelineConfig);
            
            resultDiv.innerHTML = `
                <h4>📝 Answer:</h4>
                <p>${response.answer}</p>
                <h4>📚 Sources:</h4>
                <ul>
                    ${response.sources.map(source => `<li>${source}</li>`).join('')}
                </ul>
                <h4>⚙️ Pipeline Used:</h4>
                <p>${response.pipeline}</p>
            `;
        } catch (error) {
            resultDiv.innerHTML = `<p style="color: #e53e3e;">❌ Error: ${error.message}</p>`;
        }
    }

    async simulateQuery(query, config) {
        // Simulate processing delay
        await new Promise(resolve => setTimeout(resolve, 1500));
        
        return {
            answer: `This is a simulated response to: "${query}". In a real implementation, this would be processed through your configured RAG pipeline.`,
            sources: [
                'Document 1: Sample content related to your query',
                'Document 2: Additional relevant information',
                'Document 3: Supporting context'
            ],
            pipeline: config.summary || 'No pipeline configured'
        };
    }

    getPipelineConfig() {
        const componentArray = Array.from(this.components.values());
        const datasource = componentArray.find(c => c.type === 'datasource');
        const vectordb = componentArray.find(c => c.type === 'vectordb');
        const llm = componentArray.find(c => c.type === 'llm');

        return {
            datasource: datasource ? `${datasource.name} (${datasource.status})` : 'None',
            vectordb: vectordb ? `${vectordb.name} (${vectordb.status})` : 'None',
            llm: llm ? `${llm.name} (${llm.status})` : 'None',
            summary: `${datasource?.name || 'No Data Source'} → ${vectordb?.name || 'No Vector DB'} → ${llm?.name || 'No LLM'}`,
            components: componentArray,
            connections: this.connections
        };
    }

    exportConfig() {
        const config = this.getPipelineConfig();
        const exportData = {
            timestamp: new Date().toISOString(),
            version: '1.0',
            pipeline: config
        };

        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `rag-pipeline-${Date.now()}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        this.showNotification('Pipeline configuration exported!', 'success');
    }

    // Enhanced Pipeline Management Methods
    updatePipelineStats() {
        const componentCount = this.components.size;
        const connectionCount = this.connections.length;
        
        // Update component count
        document.getElementById('component-count').textContent = componentCount;
        document.getElementById('connection-count').textContent = connectionCount;
        
        // Update pipeline health
        const healthElement = document.getElementById('pipeline-health');
        const statusIndicator = document.getElementById('status-indicator');
        const statusText = document.getElementById('status-text');
        
        if (componentCount === 0) {
            healthElement.textContent = 'Empty';
            statusIndicator.className = 'status-indicator ready';
            statusText.textContent = 'Ready';
        } else if (this.hasValidPipeline()) {
            healthElement.textContent = 'Ready';
            statusIndicator.className = 'status-indicator ready';
            statusText.textContent = 'Pipeline Ready';
        } else {
            healthElement.textContent = 'Incomplete';
            statusIndicator.className = 'status-indicator working';
            statusText.textContent = 'Configuring';
        }
    }
    
    hasValidPipeline() {
        const componentArray = Array.from(this.components.values());
        const hasDataSource = componentArray.some(c => c.type === 'datasource' && c.status === 'configured');
        const hasVectorDB = componentArray.some(c => c.type === 'vectordb' && c.status === 'configured');
        const hasLLM = componentArray.some(c => c.type === 'llm' && c.status === 'configured');
        
        return hasDataSource && hasVectorDB && hasLLM;
    }
    
    async validatePipeline() {
        this.addLog('Validating pipeline...', 'info');
        
        const issues = [];
        const componentArray = Array.from(this.components.values());
        
        // Check for required component types
        const hasDataSource = componentArray.some(c => c.type === 'datasource');
        const hasVectorDB = componentArray.some(c => c.type === 'vectordb');
        const hasLLM = componentArray.some(c => c.type === 'llm');
        
        if (!hasDataSource) issues.push('Missing Data Source component');
        if (!hasVectorDB) issues.push('Missing Vector Database component');
        if (!hasLLM) issues.push('Missing LLM component');
        
        // Check component configurations
        componentArray.forEach(component => {
            if (component.status === 'unconfigured') {
                issues.push(`${component.name} is not configured`);
            }
        });
        
        if (issues.length === 0) {
            this.addLog('Pipeline validation passed!', 'success');
            this.showNotification('Pipeline is valid and ready to use!', 'success');
        } else {
            issues.forEach(issue => this.addLog(`Validation issue: ${issue}`, 'error'));
            this.showNotification(`Found ${issues.length} validation issues. Check logs for details.`, 'error');
        }
    }
    
    savePipeline() {
        const config = this.getPipelineConfig();
        const pipelineData = {
            name: this.pipelineName || 'Untitled Pipeline',
            description: this.pipelineDescription || '',
            timestamp: new Date().toISOString(),
            version: '1.0',
            ...config
        };
        
        const blob = new Blob([JSON.stringify(pipelineData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${pipelineData.name.replace(/[^a-z0-9]/gi, '_').toLowerCase()}-${Date.now()}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        this.addLog(`Saved pipeline: ${pipelineData.name}`, 'success');
        this.showNotification('Pipeline saved successfully!', 'success');
    }
    
    loadPipeline() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.json';
        
        input.onchange = (e) => {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    try {
                        const pipelineData = JSON.parse(e.target.result);
                        this.loadPipelineFromData(pipelineData);
                    } catch (error) {
                        this.addLog(`Failed to load pipeline: ${error.message}`, 'error');
                        this.showNotification('Failed to load pipeline file', 'error');
                    }
                };
                reader.readAsText(file);
            }
        };
        
        input.click();
    }
    
    loadPipelineFromData(data) {
        // Clear existing pipeline
        this.components.clear();
        this.connections = [];
        document.querySelectorAll('.dropped-component').forEach(el => el.remove());
        
        // Load pipeline metadata
        this.pipelineName = data.name || '';
        this.pipelineDescription = data.description || '';
        document.getElementById('pipeline-name').value = this.pipelineName;
        document.getElementById('pipeline-description').value = this.pipelineDescription;
        
        // Load components
        if (data.components) {
            data.components.forEach(componentData => {
                this.components.set(componentData.id, componentData);
                this.renderComponent(componentData);
            });
        }
        
        // Load connections
        if (data.connections) {
            this.connections = data.connections;
            this.renderConnections();
        }
        
        this.updatePipelineStats();
        this.addLog(`Loaded pipeline: ${this.pipelineName}`, 'success');
        this.showNotification('Pipeline loaded successfully!', 'success');
        
        // Hide placeholder
        const placeholder = document.querySelector('.canvas-placeholder');
        if (placeholder && this.components.size > 0) {
            placeholder.style.display = 'none';
        }
    }
    
    // Logging Methods
    addLog(message, type = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = { timestamp, message, type };
        
        this.logs.push(logEntry);
        
        // Keep only last 100 logs
        if (this.logs.length > 100) {
            this.logs.shift();
        }
        
        this.renderLogs();
    }
    
    renderLogs() {
        const logsContent = document.getElementById('logs-content');
        
        // Keep existing logs and add new ones
        const newLogs = this.logs.slice(-10); // Show last 10 logs
        
        logsContent.innerHTML = newLogs.map(log => `
            <div class="log-entry ${log.type}">
                <span class="log-time">${log.timestamp}</span>
                <span class="log-message">${log.message}</span>
            </div>
        `).join('');
        
        // Auto-scroll to bottom
        logsContent.scrollTop = logsContent.scrollHeight;
    }
    
    clearLogs() {
        this.logs = [];
        this.renderLogs();
        this.addLog('Logs cleared', 'info');
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 1.5rem;
            background: ${type === 'success' ? '#48bb78' : type === 'error' ? '#f56565' : '#4299e1'};
            color: white;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            z-index: 1001;
            font-weight: 500;
            transform: translateX(100%);
            transition: transform 0.3s ease;
        `;
        notification.textContent = message;

        document.body.appendChild(notification);

        // Animate in
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);

        // Remove after 3 seconds
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new RAGBuilder();
});