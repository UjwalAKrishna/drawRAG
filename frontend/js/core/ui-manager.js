/**
 * UI Manager
 * Handles DOM manipulation and user interface interactions
 */
class UIManager {
    constructor(componentManager, eventBus) {
        this.componentManager = componentManager;
        this.eventBus = eventBus;
        this.canvasElement = null;
        this.draggedElement = null;
        this.isDragging = false;
        this.selectedComponentId = null;
        
        this.initializeElements();
        this.setupEventListeners();
        this.setupDragAndDrop();
    }

    /**
     * Initialize the UI Manager
     */
    async initialize() {
        // UI Manager initialization - already done in constructor
        if (this.statusText) {
            this.statusText.textContent = 'Ready';
        }
        if (this.statusIndicator) {
            this.statusIndicator.className = 'status-indicator ready';
        }
        return true;
    }

    /**
     * Initialize DOM elements
     */
    initializeElements() {
        this.canvasElement = document.getElementById('pipeline-canvas');
        this.configPanel = document.getElementById('config-content');
        this.statusIndicator = document.getElementById('status-indicator');
        this.statusText = document.getElementById('status-text');
        
        if (!this.canvasElement) {
            throw new Error('Pipeline canvas element not found');
        }
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Component manager events
        this.eventBus.on('component:created', this.handleComponentCreated.bind(this));
        this.eventBus.on('component:updated', this.handleComponentUpdated.bind(this));
        this.eventBus.on('component:deleted', this.handleComponentDeleted.bind(this));
        this.eventBus.on('component:moved', this.handleComponentMoved.bind(this));
        this.eventBus.on('component:connected', this.handleComponentConnected.bind(this));
        this.eventBus.on('component:disconnected', this.handleComponentDisconnected.bind(this));

        // Canvas events
        this.canvasElement.addEventListener('click', this.handleCanvasClick.bind(this));
        
        // Window events
        window.addEventListener('resize', this.handleWindowResize.bind(this));
    }

    /**
     * Setup drag and drop functionality
     */
    setupDragAndDrop() {
        // Canvas drop zone
        this.canvasElement.addEventListener('dragover', this.handleDragOver.bind(this));
        this.canvasElement.addEventListener('dragleave', this.handleDragLeave.bind(this));
        this.canvasElement.addEventListener('drop', this.handleDrop.bind(this));
        
        // Listen for plugins loaded to setup component items
        this.eventBus.on('plugins-loaded', this.handlePluginsLoaded.bind(this));
        
        // Listen for palette rendered to setup drag handlers
        this.eventBus.on('palette-rendered', () => {
            console.log('Palette rendered, setting up drag handlers...');
            this.setupComponentItemDragHandlers();
        });
    }

    /**
     * Handle plugins loaded from API
     * @param {Object} data - Event data
     */
    handlePluginsLoaded(data) {
        this.renderComponentPalette(data.plugins);
        this.setupComponentItemDragHandlers();
    }

    /**
     * Render component palette with loaded plugins
     * @param {Object} plugins - Plugin definitions
     */
    renderComponentPalette(plugins) {
        const palette = document.querySelector('.component-palette');
        if (!palette) return;

        // Clear existing content except the title
        const title = palette.querySelector('h3');
        palette.innerHTML = '';
        if (title) palette.appendChild(title);

        // Render categories
        Object.entries(plugins).forEach(([category, categoryPlugins]) => {
            if (Object.keys(categoryPlugins).length === 0) return;

            const categoryDiv = document.createElement('div');
            categoryDiv.className = 'component-category';
            
            const categoryTitle = document.createElement('h4');
            categoryTitle.textContent = this.getCategoryDisplayName(category);
            categoryDiv.appendChild(categoryTitle);

            Object.entries(categoryPlugins).forEach(([pluginType, plugin]) => {
                const componentItem = document.createElement('div');
                componentItem.className = 'component-item';
                componentItem.draggable = true;
                componentItem.dataset.type = category;
                componentItem.dataset.subtype = pluginType;
                componentItem.title = plugin.description || plugin.name;

                componentItem.innerHTML = `
                    <div class="component-icon">${plugin.icon}</div>
                    <span>${plugin.name}</span>
                `;

                categoryDiv.appendChild(componentItem);
            });

            palette.appendChild(categoryDiv);
        });
    }

    /**
     * Get display name for category
     * @param {string} category - Category name
     * @returns {string} Display name
     */
    getCategoryDisplayName(category) {
        const displayNames = {
            datasource: '📊 Data Sources',
            vectordb: '🔍 Vector Databases', 
            llm: '🤖 LLMs',
            embedding: '🔗 Embeddings'
        };
        return displayNames[category] || category;
    }

    /**
     * Setup drag handlers for component items
     */
    setupComponentItemDragHandlers() {
        const componentItems = document.querySelectorAll('.component-item');
        console.log('Setting up drag handlers for', componentItems.length, 'items');
        
        componentItems.forEach((item, index) => {
            console.log(`Setting up item ${index}:`, item.dataset.type, item.dataset.subtype);
            
            // Remove existing listeners to avoid duplicates
            item.removeEventListener('dragstart', this.handleDragStart);
            item.removeEventListener('dragend', this.handleDragEnd);
            
            // Add new listeners
            item.addEventListener('dragstart', this.handleDragStart.bind(this));
            item.addEventListener('dragend', this.handleDragEnd.bind(this));
        });
    }

    /**
     * Handle drag start
     * @param {DragEvent} event 
     */
    handleDragStart(event) {
        const item = event.currentTarget;
        this.draggedElement = {
            type: item.dataset.type,
            subtype: item.dataset.subtype
        };
        console.log('Drag started:', this.draggedElement, item);
        item.classList.add('dragging');
    }

    /**
     * Handle drag end
     * @param {DragEvent} event 
     */
    handleDragEnd(event) {
        event.currentTarget.classList.remove('dragging');
        this.draggedElement = null;
    }

    /**
     * Handle drag over canvas
     * @param {DragEvent} event 
     */
    handleDragOver(event) {
        event.preventDefault();
        this.canvasElement.classList.add('drag-over');
    }

    /**
     * Handle drag leave canvas
     * @param {DragEvent} event 
     */
    handleDragLeave(event) {
        if (!this.canvasElement.contains(event.relatedTarget)) {
            this.canvasElement.classList.remove('drag-over');
        }
    }

    /**
     * Handle drop on canvas
     * @param {DragEvent} event 
     */
    handleDrop(event) {
        console.log('Drop event triggered!', this.draggedElement);
        event.preventDefault();
        this.canvasElement.classList.remove('drag-over');
        
        if (this.draggedElement) {
            const rect = this.canvasElement.getBoundingClientRect();
            const x = event.clientX - rect.left;
            const y = event.clientY - rect.top;
            
            console.log('Creating component at:', x, y, this.draggedElement);
            
            try {
                const component = this.componentManager.createComponent(
                    this.draggedElement.type,
                    this.draggedElement.subtype,
                    x,
                    y
                );
                console.log('Component created:', component);
                
                // Manually trigger component rendering since event might not be working
                this.renderComponent(component);
                this.hidePlaceholder();
                this.updatePipelineStats();
                this.selectComponent(component.id);
            } catch (error) {
                console.error('Component creation error:', error);
                this.showNotification(`Error creating component: ${error.message}`, 'error');
            }
        } else {
            console.log('No draggedElement found');
        }
        
        this.draggedElement = null;
    }

    /**
     * Handle canvas click
     * @param {MouseEvent} event 
     */
    handleCanvasClick(event) {
        if (event.target === this.canvasElement) {
            this.deselectComponent();
        }
    }

    /**
     * Handle window resize
     */
    handleWindowResize() {
        this.updateConnectionLines();
    }

    /**
     * Handle component created
     * @param {Object} data 
     */
    handleComponentCreated(data) {
        this.renderComponent(data.component);
        this.hidePlaceholder();
        this.updatePipelineStats();
    }

    /**
     * Handle component updated
     * @param {Object} data 
     */
    handleComponentUpdated(data) {
        this.updateComponentDisplay(data.component);
        this.updatePipelineStats();
    }

    /**
     * Handle component deleted
     * @param {Object} data 
     */
    handleComponentDeleted(data) {
        this.removeComponentFromDOM(data.componentId);
        this.updatePipelineStats();
        this.showPlaceholderIfEmpty();
    }

    /**
     * Handle component moved
     * @param {Object} data 
     */
    handleComponentMoved(data) {
        this.updateComponentPosition(data.component);
        this.updateConnectionLines();
    }

    /**
     * Handle component connected
     */
    handleComponentConnected() {
        this.updateConnectionLines();
        this.updatePipelineStats();
    }

    /**
     * Handle component disconnected
     */
    handleComponentDisconnected() {
        this.updateConnectionLines();
        this.updatePipelineStats();
    }

    /**
     * Render component on canvas
     * @param {Object} component 
     */
    renderComponent(component) {
        const componentElement = this.createComponentElement(component);
        this.canvasElement.appendChild(componentElement);
        this.makeComponentDraggable(componentElement, component.id);
    }

    /**
     * Create component DOM element
     * @param {Object} component 
     * @returns {HTMLElement}
     */
    createComponentElement(component) {
        const element = document.createElement('div');
        element.className = 'dropped-component';
        element.id = component.id;
        element.style.left = `${component.position.x}px`;
        element.style.top = `${component.position.y}px`;
        
        element.innerHTML = `
            <div class="component-header">
                <span class="component-icon">${component.icon}</span>
                <div class="component-info">
                    <div class="component-title">${component.name}</div>
                    <div class="component-status ${component.status}">
                        ${this.getStatusText(component.status)}
                    </div>
                </div>
                <div class="component-actions">
                    <button class="component-action-btn" data-action="configure" title="Configure">
                        ⚙️
                    </button>
                    <button class="component-action-btn" data-action="delete" title="Delete">
                        🗑️
                    </button>
                </div>
            </div>
            <div class="component-ports">
                <div class="input-port" data-port="input" title="Input Port"></div>
                <div class="output-port" data-port="output" title="Output Port"></div>
            </div>
        `;

        // Add event listeners
        element.addEventListener('click', (e) => {
            e.stopPropagation();
            this.selectComponent(component.id);
        });

        // Action button listeners
        element.querySelectorAll('.component-action-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const action = btn.dataset.action;
                if (action === 'configure') {
                    this.selectComponent(component.id);
                } else if (action === 'delete') {
                    this.confirmDeleteComponent(component.id);
                }
            });
        });

        // Port connection listeners - setup after element is added to DOM
        setTimeout(() => {
            this.setupPortConnections(element, component.id);
        }, 100);

        return element;
    }

    /**
     * Make component draggable
     * @param {HTMLElement} element 
     * @param {string} componentId 
     */
    makeComponentDraggable(element, componentId) {
        let isDragging = false;
        let dragStartTime = 0;
        let hasMoved = false;

        const handleMouseDown = (e) => {
            // Don't drag on buttons or ports
            if (e.target.closest('.component-action-btn') || e.target.closest('.component-ports')) {
                return;
            }

            e.preventDefault();
            isDragging = true;
            dragStartTime = Date.now();
            hasMoved = false;
            
            // Calculate offset from mouse to element's top-left corner
            const rect = element.getBoundingClientRect();
            const canvasRect = this.canvasElement.getBoundingClientRect();
            const offsetX = e.clientX - rect.left;
            const offsetY = e.clientY - rect.top;
            
            element.style.cursor = 'grabbing';
            element.classList.add('dragging');
            
            const handleMouseMove = (e) => {
                if (!isDragging) return;
                
                hasMoved = true;
                const canvasRect = this.canvasElement.getBoundingClientRect();
                const newX = e.clientX - canvasRect.left - offsetX;
                const newY = e.clientY - canvasRect.top - offsetY;

                // Constrain to canvas bounds
                const maxX = this.canvasElement.clientWidth - element.offsetWidth;
                const maxY = this.canvasElement.clientHeight - element.offsetHeight;
                const constrainedX = Math.max(0, Math.min(newX, maxX));
                const constrainedY = Math.max(0, Math.min(newY, maxY));

                element.style.left = `${constrainedX}px`;
                element.style.top = `${constrainedY}px`;
                
                // Update connection lines during drag
                this.updateSimpleConnectionLines();
            };

            const handleMouseUp = () => {
                if (!isDragging) return;

                isDragging = false;
                element.style.cursor = 'grab';
                element.classList.remove('dragging');
                
                // Update component position in manager only if moved
                if (hasMoved) {
                    const finalX = parseInt(element.style.left) || 0;
                    const finalY = parseInt(element.style.top) || 0;
                    
                    if (this.componentManager.moveComponent) {
                        this.componentManager.moveComponent(componentId, finalX, finalY);
                    }
                    
                    // Update connections after move
                    this.updateConnectionLines();
                }
                
                document.removeEventListener('mousemove', handleMouseMove);
                document.removeEventListener('mouseup', handleMouseUp);
            };
            
            document.addEventListener('mousemove', handleMouseMove);
            document.addEventListener('mouseup', handleMouseUp);
        };

        element.style.cursor = 'grab';
        element.addEventListener('mousedown', handleMouseDown);
    }

    /**
     * Setup port connections for component
     * @param {HTMLElement} element 
     * @param {string} componentId 
     */
    setupPortConnections(element, componentId) {
        const outputPort = element.querySelector('.output-port');
        const inputPort = element.querySelector('.input-port');
        
        if (outputPort) {
            console.log('Setting up output port for', componentId);
            outputPort.addEventListener('mousedown', (e) => {
                e.stopPropagation();
                e.preventDefault();
                console.log('Output port clicked, starting connection from', componentId);
                this.startConnection(componentId, 'output', e);
            });
            outputPort.style.cursor = 'crosshair';
        } else {
            console.log('No output port found for', componentId);
        }
        
        if (inputPort) {
            console.log('Setting up input port for', componentId);
            inputPort.addEventListener('mouseenter', (e) => {
                if (this.isConnecting) {
                    e.target.classList.add('connection-target');
                    console.log('Input port highlighted for connection');
                }
            });
            
            inputPort.addEventListener('mouseleave', (e) => {
                e.target.classList.remove('connection-target');
            });
            
            inputPort.addEventListener('mouseup', (e) => {
                if (this.isConnecting) {
                    console.log('Completing connection to', componentId);
                    this.completeConnection(componentId, 'input');
                }
            });
            inputPort.style.cursor = 'crosshair';
        } else {
            console.log('No input port found for', componentId);
        }
    }

    /**
     * Start creating a connection
     * @param {string} componentId 
     * @param {string} portType 
     * @param {MouseEvent} event 
     */
    startConnection(componentId, portType, event) {
        this.isConnecting = true;
        this.connectionStart = { componentId, portType };
        
        console.log('Starting connection from', componentId, portType);
        
        document.addEventListener('mousemove', this.handleConnectionDrag.bind(this));
        document.addEventListener('mouseup', this.cancelConnection.bind(this));
    }

    /**
     * Handle connection dragging
     * @param {MouseEvent} event 
     */
    handleConnectionDrag(event) {
        if (this.temporaryLine) {
            const rect = this.canvasElement.getBoundingClientRect();
            const x = event.clientX - rect.left;
            const y = event.clientY - rect.top;
            
            // Update temporary line endpoint
            this.updateTemporaryLine(x, y);
        }
    }

    /**
     * Complete connection
     * @param {string} targetComponentId 
     * @param {string} targetPortType 
     */
    completeConnection(targetComponentId, targetPortType) {
        if (this.connectionStart && this.connectionStart.componentId !== targetComponentId) {
            // Store connection in simple array
            if (!this.connections) {
                this.connections = [];
            }
            
            const connection = {
                from: this.connectionStart.componentId,
                to: targetComponentId,
                id: `connection-${Date.now()}`
            };
            
            this.connections.push(connection);
            console.log('Connection created:', connection);
            
            // Draw the connection line immediately
            this.drawSimpleConnectionLine(connection);
        }
        
        this.cancelConnection();
    }

    /**
     * Cancel connection creation
     */
    cancelConnection() {
        this.isConnecting = false;
        this.connectionStart = null;
        
        if (this.temporaryLine) {
            this.temporaryLine.remove();
            this.temporaryLine = null;
        }
        
        document.removeEventListener('mousemove', this.handleConnectionDrag);
        document.removeEventListener('mouseup', this.cancelConnection);
        
        // Remove connection target highlights
        document.querySelectorAll('.connection-target').forEach(el => {
            el.classList.remove('connection-target');
        });
    }

    /**
     * Create temporary connection line
     * @param {MouseEvent} event 
     */
    createTemporaryConnectionLine(event) {
        // Implementation for temporary connection line
        // This would create a visual line that follows the mouse
    }

    /**
     * Update temporary connection line
     * @param {number} x 
     * @param {number} y 
     */
    updateTemporaryLine(x, y) {
        if (this.temporaryLine) {
            this.temporaryLine.setAttribute('x2', x);
            this.temporaryLine.setAttribute('y2', y);
        }
    }

    /**
     * Draw connection line between components
     * @param {Object} connection 
     */
    drawConnectionLine(connection) {
        const fromElement = document.getElementById(connection.from);
        const toElement = document.getElementById(connection.to);
        
        if (!fromElement || !toElement) {
            console.log('Connection elements not found:', connection.from, connection.to);
            return;
        }

        // Get port positions
        const fromPort = fromElement.querySelector('.output-port');
        const toPort = toElement.querySelector('.input-port');
        
        if (!fromPort || !toPort) {
            console.log('Ports not found');
            return;
        }

        const canvasRect = this.canvasElement.getBoundingClientRect();
        const fromRect = fromPort.getBoundingClientRect();
        const toRect = toPort.getBoundingClientRect();

        // Calculate positions relative to canvas
        const fromX = fromRect.left + fromRect.width/2 - canvasRect.left;
        const fromY = fromRect.top + fromRect.height/2 - canvasRect.top;
        const toX = toRect.left + toRect.width/2 - canvasRect.left;
        const toY = toRect.top + toRect.height/2 - canvasRect.top;

        // Create or get SVG container
        let svg = this.canvasElement.querySelector('.connection-svg');
        if (!svg) {
            svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            svg.classList.add('connection-svg');
            svg.style.position = 'absolute';
            svg.style.top = '0';
            svg.style.left = '0';
            svg.style.width = '100%';
            svg.style.height = '100%';
            svg.style.pointerEvents = 'none';
            svg.style.zIndex = '5';
            svg.style.overflow = 'visible';
            this.canvasElement.appendChild(svg);
            console.log('Created SVG container');
        }

        // Create connection line
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.classList.add('connection-line');
        line.setAttribute('x1', fromX);
        line.setAttribute('y1', fromY);
        line.setAttribute('x2', toX);
        line.setAttribute('y2', toY);
        line.setAttribute('stroke', '#ff0000');
        line.setAttribute('stroke-width', '5');
        line.setAttribute('stroke-opacity', '1');
        line.setAttribute('marker-end', 'url(#arrowhead)');
        line.dataset.connectionId = connection.id;

        // Add arrowhead marker if not exists
        this.addArrowMarker(svg);
        
        svg.appendChild(line);
        
        console.log('Connection line drawn:', fromX, fromY, '->', toX, toY);
        console.log('SVG element:', svg);
        console.log('Line element:', line);
    }

    /**
     * Draw simple connection line that definitely works
     * @param {Object} connection 
     */
    drawSimpleConnectionLine(connection) {
        const fromElement = document.getElementById(connection.from);
        const toElement = document.getElementById(connection.to);
        
        if (!fromElement || !toElement) {
            console.log('Connection elements not found:', connection.from, connection.to);
            return;
        }

        // Get port positions instead of center positions
        const fromPort = fromElement.querySelector('.output-port');
        const toPort = toElement.querySelector('.input-port');
        
        if (!fromPort || !toPort) {
            console.log('Ports not found for connection');
            return;
        }

        const canvasRect = this.canvasElement.getBoundingClientRect();
        const fromRect = fromPort.getBoundingClientRect();
        const toRect = toPort.getBoundingClientRect();

        // Calculate port center positions
        const fromX = fromRect.left + fromRect.width/2 - canvasRect.left;
        const fromY = fromRect.top + fromRect.height/2 - canvasRect.top;
        const toX = toRect.left + toRect.width/2 - canvasRect.left;
        const toY = toRect.top + toRect.height/2 - canvasRect.top;

        // Create simple div-based line
        const line = document.createElement('div');
        line.className = 'simple-connection-line';
        line.dataset.connectionId = connection.id;
        
        // Calculate line properties
        const deltaX = toX - fromX;
        const deltaY = toY - fromY;
        const length = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
        const angle = Math.atan2(deltaY, deltaX) * 180 / Math.PI;
        
        // Position and style the line
        line.style.position = 'absolute';
        line.style.left = fromX + 'px';
        line.style.top = fromY + 'px';
        line.style.width = length + 'px';
        line.style.height = '4px';
        line.style.background = '#ff0000';
        line.style.transformOrigin = '0 50%';
        line.style.transform = `rotate(${angle}deg)`;
        line.style.zIndex = '1000';
        line.style.pointerEvents = 'none';
        
        this.canvasElement.appendChild(line);
        
        console.log('Simple connection line created:', fromX, fromY, '->', toX, toY, 'length:', length, 'angle:', angle);
    }

    /**
     * Update all simple connection lines
     */
    updateSimpleConnectionLines() {
        if (!this.connections) return;
        
        // Remove existing simple lines
        document.querySelectorAll('.simple-connection-line').forEach(line => line.remove());
        
        // Redraw all connections
        this.connections.forEach(connection => {
            this.drawSimpleConnectionLine(connection);
        });
    }

    /**
     * Add arrow marker to SVG
     * @param {SVGElement} svg 
     */
    addArrowMarker(svg) {
        let defs = svg.querySelector('defs');
        if (!defs) {
            defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
            svg.appendChild(defs);
            
            const marker = document.createElementNS('http://www.w3.org/2000/svg', 'marker');
            marker.setAttribute('id', 'arrowhead');
            marker.setAttribute('markerWidth', '10');
            marker.setAttribute('markerHeight', '7');
            marker.setAttribute('refX', '9');
            marker.setAttribute('refY', '3.5');
            marker.setAttribute('orient', 'auto');
            
            const polygon = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
            polygon.setAttribute('points', '0 0, 10 3.5, 0 7');
            polygon.setAttribute('fill', '#4299e1');
            
            marker.appendChild(polygon);
            defs.appendChild(marker);
        }
    }

    /**
     * Select component
     * @param {string} componentId 
     */
    selectComponent(componentId) {
        // Remove previous selection
        document.querySelectorAll('.dropped-component').forEach(el => {
            el.classList.remove('selected');
        });

        // Select new component
        const componentElement = document.getElementById(componentId);
        if (componentElement) {
            componentElement.classList.add('selected');
            this.selectedComponentId = componentId;
            this.showComponentConfiguration(componentId);
            this.componentManager.selectedComponentId = componentId;
        }
    }

    /**
     * Deselect component
     */
    deselectComponent() {
        document.querySelectorAll('.dropped-component').forEach(el => {
            el.classList.remove('selected');
        });
        this.selectedComponentId = null;
        this.componentManager.selectedComponentId = null;
        this.hideComponentConfiguration();
    }

    /**
     * Show component configuration panel
     * @param {string} componentId 
     */
    showComponentConfiguration(componentId) {
        const component = this.componentManager.getComponent(componentId);
        if (!component || !this.configPanel) return;

        const definition = this.componentManager.getComponentDefinition(component.type, component.subtype);
        
        this.configPanel.innerHTML = `
            <div class="config-header">
                <h4>${component.icon} ${component.name}</h4>
                <div class="config-status">
                    <span class="status-badge ${component.status}">${this.getStatusText(component.status)}</span>
                </div>
            </div>
            <form id="component-config-form" class="config-form">
                ${this.generateConfigFields(component.config, definition)}
                <div class="config-actions">
                    <button type="submit" class="btn btn-primary">Save Configuration</button>
                    <button type="button" class="btn btn-secondary" id="test-component">Test Connection</button>
                </div>
            </form>
        `;

        // Setup form submission
        const form = document.getElementById('component-config-form');
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveComponentConfiguration(componentId);
        });

        // Setup test button
        const testButton = document.getElementById('test-component');
        if (testButton) {
            testButton.addEventListener('click', () => {
                this.testComponentConnection(componentId);
            });
        }
    }

    /**
     * Generate configuration form fields
     * @param {Object} config 
     * @param {Object} definition 
     * @returns {string}
     */
    generateConfigFields(config, definition) {
        if (!definition) return '<p>No configuration available</p>';

        return Object.entries(config).map(([key, value]) => {
            const isRequired = definition.requiredFields?.includes(key);
            const fieldType = this.getFieldType(key, value);
            const fieldName = this.formatFieldName(key);

            return `
                <div class="form-group">
                    <label for="${key}" class="${isRequired ? 'required' : ''}">
                        ${fieldName}${isRequired ? ' *' : ''}
                    </label>
                    <input 
                        type="${fieldType}" 
                        id="${key}" 
                        name="${key}" 
                        value="${value || ''}"
                        ${isRequired ? 'required' : ''}
                        placeholder="Enter ${fieldName.toLowerCase()}"
                    />
                </div>
            `;
        }).join('');
    }

    /**
     * Get field type for input
     * @param {string} key 
     * @param {*} value 
     * @returns {string}
     */
    getFieldType(key, value) {
        if (key.includes('password') || key.includes('secret') || key.includes('key')) {
            return 'password';
        }
        if (key.includes('port') || typeof value === 'number') {
            return 'number';
        }
        if (key.includes('url') || key.includes('endpoint')) {
            return 'url';
        }
        return 'text';
    }

    /**
     * Format field name for display
     * @param {string} key 
     * @returns {string}
     */
    formatFieldName(key) {
        return key
            .replace(/_/g, ' ')
            .replace(/\b\w/g, l => l.toUpperCase());
    }

    /**
     * Save component configuration
     * @param {string} componentId 
     */
    async saveComponentConfiguration(componentId) {
        const form = document.getElementById('component-config-form');
        if (!form) return;

        const formData = new FormData(form);
        const config = {};
        
        for (const [key, value] of formData.entries()) {
            config[key] = value;
        }

        try {
            this.componentManager.updateComponentConfig(componentId, config);
            this.showNotification('Configuration saved successfully', 'success');
        } catch (error) {
            this.showNotification(`Error saving configuration: ${error.message}`, 'error');
        }
    }

    /**
     * Test component connection
     * @param {string} componentId 
     */
    async testComponentConnection(componentId) {
        const component = this.componentManager.getComponent(componentId);
        if (!component) return;

        this.showNotification('Testing connection...', 'info');
        
        try {
            // This would call the backend to test the component
            const result = await this.testConnection(component);
            if (result.success) {
                this.showNotification('Connection test successful', 'success');
            } else {
                this.showNotification(`Connection test failed: ${result.error}`, 'error');
            }
        } catch (error) {
            this.showNotification(`Connection test error: ${error.message}`, 'error');
        }
    }

    /**
     * Test connection (placeholder for backend integration)
     * @param {Object} component 
     * @returns {Promise<Object>}
     */
    async testConnection(component) {
        // Simulate connection test
        await new Promise(resolve => setTimeout(resolve, 1000));
        return { success: true };
    }

    /**
     * Hide component configuration panel
     */
    hideComponentConfiguration() {
        if (this.configPanel) {
            this.configPanel.innerHTML = '<p class="config-placeholder">Select a component to configure its settings</p>';
        }
    }

    /**
     * Update component display
     * @param {Object} component 
     */
    updateComponentDisplay(component) {
        const element = document.getElementById(component.id);
        if (!element) return;

        const statusElement = element.querySelector('.component-status');
        if (statusElement) {
            statusElement.className = `component-status ${component.status}`;
            statusElement.textContent = this.getStatusText(component.status);
        }
    }

    /**
     * Update component position
     * @param {Object} component 
     */
    updateComponentPosition(component) {
        const element = document.getElementById(component.id);
        if (element) {
            element.style.left = `${component.position.x}px`;
            element.style.top = `${component.position.y}px`;
        }
    }

    /**
     * Remove component from DOM
     * @param {string} componentId 
     */
    removeComponentFromDOM(componentId) {
        const element = document.getElementById(componentId);
        if (element) {
            element.remove();
        }
        
        if (this.selectedComponentId === componentId) {
            this.deselectComponent();
        }
    }

    /**
     * Confirm component deletion
     * @param {string} componentId 
     */
    confirmDeleteComponent(componentId) {
        const element = document.getElementById(componentId);
        if (!element) return;

        const componentName = element.querySelector('.component-title')?.textContent || 'component';
        
        if (confirm(`Are you sure you want to delete "${componentName}"?`)) {
            // Remove from DOM immediately
            element.remove();
            
            // Update component manager if it exists
            if (this.componentManager && this.componentManager.deleteComponent) {
                this.componentManager.deleteComponent(componentId);
            }
            
            // Update stats and show placeholder if needed
            this.updatePipelineStats();
            this.showPlaceholderIfEmpty();
            
            // Deselect if this was the selected component
            if (this.selectedComponentId === componentId) {
                this.deselectComponent();
            }
        }
    }

    /**
     * Update connection lines
     */
    updateConnectionLines() {
        // Remove existing lines
        document.querySelectorAll('.connection-line').forEach(line => line.remove());

        // Draw connections from our simple storage
        if (this.connections) {
            this.connections.forEach(connection => {
                this.drawConnectionLine(connection);
            });
        }
    }

    /**
     * Draw connection line between components
     * @param {Object} connection 
     */
    drawConnectionLine(connection) {
        const fromElement = document.getElementById(connection.from);
        const toElement = document.getElementById(connection.to);
        
        if (!fromElement || !toElement) return;

        const line = this.createConnectionLine(fromElement, toElement);
        this.canvasElement.appendChild(line);
    }

    /**
     * Create connection line element
     * @param {HTMLElement} fromElement 
     * @param {HTMLElement} toElement 
     * @returns {HTMLElement}
     */
    createConnectionLine(fromElement, toElement) {
        const canvasRect = this.canvasElement.getBoundingClientRect();
        const fromRect = fromElement.getBoundingClientRect();
        const toRect = toElement.getBoundingClientRect();

        const fromX = fromRect.right - canvasRect.left;
        const fromY = fromRect.top + fromRect.height / 2 - canvasRect.top;
        const toX = toRect.left - canvasRect.left;
        const toY = toRect.top + toRect.height / 2 - canvasRect.top;

        const line = document.createElement('div');
        line.className = 'connection-line';
        
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        
        const pathData = this.createCurvedPath(fromX, fromY, toX, toY);
        
        path.setAttribute('d', pathData);
        path.setAttribute('class', 'connection-path');
        
        svg.appendChild(path);
        line.appendChild(svg);
        
        // Position and size the SVG
        const minX = Math.min(fromX, toX) - 10;
        const minY = Math.min(fromY, toY) - 10;
        const width = Math.abs(toX - fromX) + 20;
        const height = Math.abs(toY - fromY) + 20;
        
        svg.style.position = 'absolute';
        svg.style.left = `${minX}px`;
        svg.style.top = `${minY}px`;
        svg.style.width = `${width}px`;
        svg.style.height = `${height}px`;
        svg.setAttribute('viewBox', `0 0 ${width} ${height}`);

        return line;
    }

    /**
     * Create curved path for connection
     * @param {number} fromX 
     * @param {number} fromY 
     * @param {number} toX 
     * @param {number} toY 
     * @returns {string}
     */
    createCurvedPath(fromX, fromY, toX, toY) {
        const dx = toX - fromX;
        const dy = toY - fromY;
        const controlOffset = Math.abs(dx) * 0.5;
        
        const cp1x = fromX + controlOffset;
        const cp1y = fromY;
        const cp2x = toX - controlOffset;
        const cp2y = toY;
        
        return `M ${fromX} ${fromY} C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${toX} ${toY}`;
    }

    /**
     * Get status text
     * @param {string} status 
     * @returns {string}
     */
    getStatusText(status) {
        const statusTexts = {
            unconfigured: 'Not Configured',
            configured: 'Configured',
            error: 'Error',
            processing: 'Processing'
        };
        return statusTexts[status] || status;
    }

    /**
     * Show notification
     * @param {string} message 
     * @param {string} type 
     */
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => notification.classList.add('show'), 100);
        
        // Remove after delay
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    /**
     * Update pipeline statistics
     */
    updatePipelineStats() {
        const componentCount = this.componentManager.getAllComponents().length;
        const connectionCount = this.componentManager.getAllConnections().length;
        
        // Update component count
        const componentCountEl = document.getElementById('component-count');
        if (componentCountEl) {
            componentCountEl.textContent = componentCount;
        }
        
        // Update connection count
        const connectionCountEl = document.getElementById('connection-count');
        if (connectionCountEl) {
            connectionCountEl.textContent = connectionCount;
        }
        
        // Update pipeline health
        this.updatePipelineStatus();
    }

    /**
     * Update pipeline status
     */
    updatePipelineStatus() {
        const validation = this.componentManager.validatePipeline();
        
        if (this.statusIndicator && this.statusText) {
            if (validation.isValid) {
                this.statusIndicator.className = 'status-indicator ready';
                this.statusText.textContent = 'Pipeline Ready';
            } else {
                this.statusIndicator.className = 'status-indicator warning';
                this.statusText.textContent = 'Pipeline Incomplete';
            }
        }
        
        // Update pipeline health display
        const healthElement = document.getElementById('pipeline-health');
        if (healthElement) {
            healthElement.textContent = validation.isValid ? 'Ready' : 'Incomplete';
        }
    }

    /**
     * Hide placeholder when components exist
     */
    hidePlaceholder() {
        const placeholder = this.canvasElement.querySelector('.canvas-placeholder');
        if (placeholder) {
            placeholder.style.display = 'none';
        }
    }

    /**
     * Show placeholder when no components exist
     */
    showPlaceholderIfEmpty() {
        if (this.componentManager.getAllComponents().length === 0) {
            const placeholder = this.canvasElement.querySelector('.canvas-placeholder');
            if (placeholder) {
                placeholder.style.display = 'block';
            }
        }
    }

    /**
     * Clear all components from canvas
     */
    clearCanvas() {
        this.canvasElement.querySelectorAll('.dropped-component, .connection-line').forEach(el => {
            el.remove();
        });
        this.showPlaceholderIfEmpty();
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { UIManager };
}