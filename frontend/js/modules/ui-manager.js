// UI Manager - Handles all UI interactions and state
export class UIManager {
    constructor(eventBus) {
        this.eventBus = eventBus;
        this.currentTheme = 'light';
        this.sidebarExpanded = true;
        this.activeModal = null;
        this.notifications = [];
        this.shortcuts = new Map();
        
        this.elements = {};
    }
    
    async initialize() {
        this.cacheElements();
        this.setupEventListeners();
        this.setupKeyboardShortcuts();
        this.setupNotificationSystem();
        this.setupModals();
        this.setupTabs();
        this.setupTheme();
        this.setupResponsive();
    }
    
    cacheElements() {
        // Cache frequently used DOM elements
        this.elements = {
            // Header elements
            header: document.querySelector('.header'),
            statusIndicator: document.getElementById('status-indicator'),
            statusText: document.getElementById('status-text'),
            
            // Main content areas
            componentPalette: document.querySelector('.component-palette'),
            canvas: document.getElementById('pipeline-canvas'),
            configPanel: document.getElementById('config-panel'),
            
            // Buttons
            saveBtn: document.getElementById('save-pipeline-btn'),
            loadBtn: document.getElementById('load-pipeline-btn'),
            testBtn: document.getElementById('test-query-btn'),
            exportBtn: document.getElementById('export-config-btn'),
            validateBtn: document.getElementById('validate-pipeline-btn'),
            
            // Modals
            testModal: document.getElementById('test-query-modal'),
            
            // Tabs
            tabButtons: document.querySelectorAll('.tab-btn'),
            tabContents: document.querySelectorAll('.tab-content'),
            
            // Config areas
            configContent: document.getElementById('config-content'),
            logsContent: document.getElementById('logs-content'),
            
            // Stats
            componentCount: document.getElementById('component-count'),
            connectionCount: document.getElementById('connection-count'),
            pipelineHealth: document.getElementById('pipeline-health')
        };
    }
    
    setupEventListeners() {
        // Header button events
        this.elements.saveBtn?.addEventListener('click', () => {
            this.eventBus.emit('ui:save-pipeline');
        });
        
        this.elements.loadBtn?.addEventListener('click', () => {
            this.eventBus.emit('ui:load-pipeline');
        });
        
        this.elements.testBtn?.addEventListener('click', () => {
            this.showModal('test-query');
        });
        
        this.elements.exportBtn?.addEventListener('click', () => {
            this.eventBus.emit('ui:export-pipeline');
        });
        
        this.elements.validateBtn?.addEventListener('click', () => {
            this.eventBus.emit('ui:validate-pipeline');
        });
        
        // Event bus listeners
        this.eventBus.on('pipeline:updated', (stats) => {
            this.updatePipelineStats(stats);
        });
        
        this.eventBus.on('status:changed', (status) => {
            this.updateStatus(status);
        });
        
        this.eventBus.on('component:selected', (component) => {
            this.showComponentConfig(component);
        });
        
        this.eventBus.on('logs:new', (logEntry) => {
            this.addLogEntry(logEntry);
        });
    }
    
    setupKeyboardShortcuts() {
        const shortcuts = [
            { key: 'ctrl+s', action: () => this.eventBus.emit('ui:save-pipeline') },
            { key: 'ctrl+o', action: () => this.eventBus.emit('ui:load-pipeline') },
            { key: 'ctrl+t', action: () => this.showModal('test-query') },
            { key: 'ctrl+e', action: () => this.eventBus.emit('ui:export-pipeline') },
            { key: 'escape', action: () => this.closeModal() },
            { key: 'ctrl+/', action: () => this.showShortcutsHelp() }
        ];
        
        shortcuts.forEach(({ key, action }) => {
            this.shortcuts.set(key, action);
        });
        
        document.addEventListener('keydown', (event) => {
            const keyCombo = this.getKeyCombo(event);
            const action = this.shortcuts.get(keyCombo);
            
            if (action) {
                event.preventDefault();
                action();
            }
        });
    }
    
    getKeyCombo(event) {
        const parts = [];
        if (event.ctrlKey) parts.push('ctrl');
        if (event.shiftKey) parts.push('shift');
        if (event.altKey) parts.push('alt');
        parts.push(event.key.toLowerCase());
        return parts.join('+');
    }
    
    setupNotificationSystem() {
        // Create notification container if it doesn't exist
        if (!document.querySelector('.notification-container')) {
            const container = document.createElement('div');
            container.className = 'notification-container';
            document.body.appendChild(container);
        }
    }
    
    setupModals() {
        // Generic modal handling
        document.addEventListener('click', (event) => {
            if (event.target.classList.contains('modal')) {
                this.closeModal();
            }
            
            if (event.target.classList.contains('modal-close')) {
                this.closeModal();
            }
        });
        
        // Prevent modal content clicks from closing modal
        document.querySelectorAll('.modal-content').forEach(content => {
            content.addEventListener('click', (event) => {
                event.stopPropagation();
            });
        });
    }
    
    setupTabs() {
        this.elements.tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                const tabId = button.getAttribute('data-tab');
                this.switchTab(tabId);
            });
        });
    }
    
    setupTheme() {
        // Load saved theme
        const savedTheme = localStorage.getItem('ragbuilder_theme') || 'light';
        this.setTheme(savedTheme);
        
        // Add theme toggle functionality
        this.addThemeToggle();
    }
    
    setupResponsive() {
        // Handle responsive behavior
        window.addEventListener('resize', () => {
            this.handleResize();
        });
        
        this.handleResize(); // Initial call
    }
    
    // UI State Management
    updateStatus(status) {
        if (this.elements.statusIndicator && this.elements.statusText) {
            this.elements.statusIndicator.className = `status-indicator ${status.type}`;
            this.elements.statusText.textContent = status.message;
        }
    }
    
    updatePipelineStats(stats) {
        if (this.elements.componentCount) {
            this.elements.componentCount.textContent = stats.components || 0;
        }
        if (this.elements.connectionCount) {
            this.elements.connectionCount.textContent = stats.connections || 0;
        }
        if (this.elements.pipelineHealth) {
            this.elements.pipelineHealth.textContent = stats.health || 'Not Ready';
            this.elements.pipelineHealth.className = `stat-value ${stats.health?.toLowerCase().replace(' ', '-')}`;
        }
    }
    
    showComponentConfig(component) {
        if (!this.elements.configContent) return;
        
        const configHTML = this.generateComponentConfigHTML(component);
        this.elements.configContent.innerHTML = configHTML;
        
        // Switch to component tab
        this.switchTab('component');
        
        // Setup form listeners
        this.setupComponentConfigListeners(component);
    }
    
    generateComponentConfigHTML(component) {
        const config = component.config || {};
        
        let html = `
            <div class="component-config">
                <div class="config-header">
                    <h4>${component.type} Configuration</h4>
                    <div class="component-icon">${component.icon}</div>
                </div>
                
                <form class="config-form" data-component-id="${component.id}">
                    <div class="form-group">
                        <label for="component-name">Name:</label>
                        <input type="text" id="component-name" name="name" value="${component.name || ''}" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="component-description">Description:</label>
                        <textarea id="component-description" name="description">${component.description || ''}</textarea>
                    </div>
        `;
        
        // Add type-specific configuration fields
        switch (component.type) {
            case 'datasource':
                html += this.generateDataSourceConfig(config);
                break;
            case 'vectordb':
                html += this.generateVectorDBConfig(config);
                break;
            case 'llm':
                html += this.generateLLMConfig(config);
                break;
        }
        
        html += `
                    <div class="config-actions">
                        <button type="submit" class="btn btn-primary">Apply Changes</button>
                        <button type="button" class="btn btn-secondary" onclick="this.closest('form').reset()">Reset</button>
                    </div>
                </form>
            </div>
        `;
        
        return html;
    }
    
    generateDataSourceConfig(config) {
        return `
            <div class="form-group">
                <label for="connection-string">Connection String:</label>
                <input type="text" id="connection-string" name="connectionString" value="${config.connectionString || ''}" placeholder="e.g., sqlite:///data.db">
            </div>
            
            <div class="form-group">
                <label for="table-name">Table Name:</label>
                <input type="text" id="table-name" name="tableName" value="${config.tableName || ''}" placeholder="documents">
            </div>
            
            <div class="form-group">
                <label for="text-column">Text Column:</label>
                <input type="text" id="text-column" name="textColumn" value="${config.textColumn || ''}" placeholder="content">
            </div>
        `;
    }
    
    generateVectorDBConfig(config) {
        return `
            <div class="form-group">
                <label for="collection-name">Collection Name:</label>
                <input type="text" id="collection-name" name="collectionName" value="${config.collectionName || ''}" placeholder="documents">
            </div>
            
            <div class="form-group">
                <label for="embedding-model">Embedding Model:</label>
                <select id="embedding-model" name="embeddingModel">
                    <option value="sentence-transformers/all-MiniLM-L6-v2" ${config.embeddingModel === 'sentence-transformers/all-MiniLM-L6-v2' ? 'selected' : ''}>MiniLM-L6-v2</option>
                    <option value="sentence-transformers/all-mpnet-base-v2" ${config.embeddingModel === 'sentence-transformers/all-mpnet-base-v2' ? 'selected' : ''}>MPNet Base v2</option>
                    <option value="openai/text-embedding-ada-002" ${config.embeddingModel === 'openai/text-embedding-ada-002' ? 'selected' : ''}>OpenAI Ada 002</option>
                </select>
            </div>
            
            <div class="form-group">
                <label for="chunk-size">Chunk Size:</label>
                <input type="number" id="chunk-size" name="chunkSize" value="${config.chunkSize || 1000}" min="100" max="4000">
            </div>
        `;
    }
    
    generateLLMConfig(config) {
        return `
            <div class="form-group">
                <label for="model-name">Model:</label>
                <select id="model-name" name="modelName">
                    <option value="gpt-3.5-turbo" ${config.modelName === 'gpt-3.5-turbo' ? 'selected' : ''}>GPT-3.5 Turbo</option>
                    <option value="gpt-4" ${config.modelName === 'gpt-4' ? 'selected' : ''}>GPT-4</option>
                    <option value="claude-3-sonnet" ${config.modelName === 'claude-3-sonnet' ? 'selected' : ''}>Claude 3 Sonnet</option>
                    <option value="local" ${config.modelName === 'local' ? 'selected' : ''}>Local Model</option>
                </select>
            </div>
            
            <div class="form-group">
                <label for="temperature">Temperature:</label>
                <input type="range" id="temperature" name="temperature" min="0" max="1" step="0.1" value="${config.temperature || 0.7}">
                <span class="range-value">${config.temperature || 0.7}</span>
            </div>
            
            <div class="form-group">
                <label for="max-tokens">Max Tokens:</label>
                <input type="number" id="max-tokens" name="maxTokens" value="${config.maxTokens || 2048}" min="1" max="8192">
            </div>
            
            <div class="form-group">
                <label for="system-prompt">System Prompt:</label>
                <textarea id="system-prompt" name="systemPrompt" rows="4" placeholder="You are a helpful assistant...">${config.systemPrompt || ''}</textarea>
            </div>
        `;
    }
    
    setupComponentConfigListeners(component) {
        const form = document.querySelector('.config-form');
        if (!form) return;
        
        // Handle range input updates
        const rangeInputs = form.querySelectorAll('input[type="range"]');
        rangeInputs.forEach(input => {
            const valueSpan = input.nextElementSibling;
            input.addEventListener('input', () => {
                if (valueSpan) valueSpan.textContent = input.value;
            });
        });
        
        // Handle form submission
        form.addEventListener('submit', (event) => {
            event.preventDefault();
            const formData = new FormData(form);
            const config = Object.fromEntries(formData.entries());
            
            this.eventBus.emit('component:config-updated', {
                componentId: component.id,
                config: config
            });
        });
    }
    
    switchTab(tabId) {
        // Update button states
        this.elements.tabButtons.forEach(button => {
            button.classList.toggle('active', button.getAttribute('data-tab') === tabId);
        });
        
        // Update content visibility
        this.elements.tabContents.forEach(content => {
            content.classList.toggle('active', content.id === `${tabId}-tab`);
        });
    }
    
    // Modal Management
    showModal(modalId) {
        const modal = document.getElementById(`${modalId}-modal`);
        if (modal) {
            modal.style.display = 'flex';
            this.activeModal = modalId;
            document.body.style.overflow = 'hidden';
        }
    }
    
    closeModal() {
        if (this.activeModal) {
            const modal = document.getElementById(`${this.activeModal}-modal`);
            if (modal) {
                modal.style.display = 'none';
                document.body.style.overflow = '';
                this.activeModal = null;
            }
        }
    }
    
    // Notification System
    showNotification(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-icon">${this.getNotificationIcon(type)}</span>
                <span class="notification-message">${message}</span>
                <button class="notification-close">&times;</button>
            </div>
        `;
        
        const container = document.querySelector('.notification-container');
        container.appendChild(notification);
        
        // Auto-remove after duration
        const timeout = setTimeout(() => {
            this.removeNotification(notification);
        }, duration);
        
        // Manual close
        notification.querySelector('.notification-close').addEventListener('click', () => {
            clearTimeout(timeout);
            this.removeNotification(notification);
        });
        
        // Store notification
        this.notifications.push({ element: notification, timeout });
        
        // Trigger animation
        requestAnimationFrame(() => {
            notification.classList.add('show');
        });
    }
    
    removeNotification(notification) {
        notification.classList.add('hide');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
        
        // Remove from tracking
        this.notifications = this.notifications.filter(n => n.element !== notification);
    }
    
    getNotificationIcon(type) {
        const icons = {
            info: 'ℹ️',
            success: '✅',
            warning: '⚠️',
            error: '❌'
        };
        return icons[type] || icons.info;
    }
    
    // Logging
    addLogEntry(logEntry) {
        if (!this.elements.logsContent) return;
        
        const logElement = document.createElement('div');
        logElement.className = `log-entry ${logEntry.level}`;
        logElement.innerHTML = `
            <span class="log-time">${this.formatTime(logEntry.timestamp)}</span>
            <span class="log-level">${logEntry.level.toUpperCase()}</span>
            <span class="log-message">${logEntry.message}</span>
        `;
        
        this.elements.logsContent.appendChild(logElement);
        
        // Auto-scroll to bottom
        this.elements.logsContent.scrollTop = this.elements.logsContent.scrollHeight;
        
        // Limit log entries (keep last 100)
        const logEntries = this.elements.logsContent.querySelectorAll('.log-entry');
        if (logEntries.length > 100) {
            logEntries[0].remove();
        }
    }
    
    formatTime(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleTimeString();
    }
    
    // Theme Management
    setTheme(theme) {
        document.body.className = document.body.className.replace(/theme-\w+/, '');
        document.body.classList.add(`theme-${theme}`);
        this.currentTheme = theme;
        localStorage.setItem('ragbuilder_theme', theme);
    }
    
    addThemeToggle() {
        if (!document.querySelector('.theme-toggle')) {
            const toggle = document.createElement('button');
            toggle.className = 'theme-toggle';
            toggle.innerHTML = this.currentTheme === 'light' ? '🌙' : '☀️';
            toggle.title = 'Toggle theme';
            
            toggle.addEventListener('click', () => {
                const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
                this.setTheme(newTheme);
                toggle.innerHTML = newTheme === 'light' ? '🌙' : '☀️';
            });
            
            this.elements.header?.appendChild(toggle);
        }
    }
    
    handleResize() {
        const width = window.innerWidth;
        
        // Handle mobile/tablet layout
        if (width < 768) {
            document.body.classList.add('mobile');
            this.sidebarExpanded = false;
        } else {
            document.body.classList.remove('mobile');
            this.sidebarExpanded = true;
        }
        
        // Update layout classes
        document.body.classList.toggle('sidebar-expanded', this.sidebarExpanded);
    }
    
    showShortcutsHelp() {
        const shortcuts = [
            { key: 'Ctrl+S', description: 'Save pipeline' },
            { key: 'Ctrl+O', description: 'Load pipeline' },
            { key: 'Ctrl+T', description: 'Test query' },
            { key: 'Ctrl+E', description: 'Export pipeline' },
            { key: 'Escape', description: 'Close modal' },
            { key: 'Ctrl+/', description: 'Show shortcuts' }
        ];
        
        const shortcutsHTML = shortcuts.map(s => 
            `<div class="shortcut-item"><kbd>${s.key}</kbd><span>${s.description}</span></div>`
        ).join('');
        
        this.showNotification(`
            <div class="shortcuts-help">
                <h4>Keyboard Shortcuts</h4>
                ${shortcutsHTML}
            </div>
        `, 'info', 10000);
    }
    
    // State management
    getState() {
        return {
            theme: this.currentTheme,
            sidebarExpanded: this.sidebarExpanded,
            activeTab: document.querySelector('.tab-btn.active')?.getAttribute('data-tab') || 'component'
        };
    }
    
    restoreState(state) {
        if (state.theme) {
            this.setTheme(state.theme);
        }
        
        if (state.activeTab) {
            this.switchTab(state.activeTab);
        }
        
        this.sidebarExpanded = state.sidebarExpanded !== false;
        this.handleResize();
    }
}