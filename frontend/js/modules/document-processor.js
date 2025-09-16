/**
 * Document Processor - Handle document upload and processing
 */
window.DocumentProcessor = class DocumentProcessor {
    constructor(apiClient, eventBus) {
        this.apiClient = apiClient;
        this.eventBus = eventBus;
        this.supportedFormats = ['.txt', '.pdf', '.docx', '.md', '.json'];
        this.documents = new Map();
        
        this.setupEventListeners();
    }

    initialize() {
        this.setupDocumentUpload();
        this.setupDocumentViewer();
    }

    setupDocumentUpload() {
        // Create document upload area in the UI
        const uploadArea = this.createDocumentUploadArea();
        
        // Find a suitable place to insert it (e.g., a documents tab)
        const configPanel = document.getElementById('config-panel');
        if (configPanel) {
            this.addDocumentTab(configPanel, uploadArea);
        }
    }

    createDocumentUploadArea() {
        const uploadDiv = document.createElement('div');
        uploadDiv.className = 'document-upload-area';
        uploadDiv.innerHTML = `
            <div class="upload-header">
                <h4>📄 Document Management</h4>
                <button class="btn btn-small" id="clear-documents-btn">Clear All</button>
            </div>
            
            <div class="document-upload-zone" id="document-upload-zone">
                <div class="upload-content">
                    <div class="upload-icon">📁</div>
                    <p>Drag & drop documents here</p>
                    <p>Supported: ${this.supportedFormats.join(', ')}</p>
                    <button class="btn btn-primary" id="browse-documents-btn">Browse Files</button>
                    <input type="file" id="document-file-input" multiple accept="${this.supportedFormats.join(',')}" style="display: none;">
                </div>
            </div>
            
            <div class="document-list" id="document-list">
                <h5>Uploaded Documents</h5>
                <div class="document-items" id="document-items">
                    <p class="no-documents">No documents uploaded yet</p>
                </div>
            </div>
            
            <div class="document-actions">
                <button class="btn btn-success" id="index-documents-btn" disabled>
                    🔍 Index Documents
                </button>
                <button class="btn btn-info" id="batch-process-btn" disabled>
                    ⚙️ Batch Process
                </button>
            </div>
        `;
        
        return uploadDiv;
    }

    addDocumentTab(configPanel, uploadArea) {
        // Add document tab to the config panel
        const tabsContainer = configPanel.querySelector('.config-tabs');
        if (tabsContainer) {
            const documentTab = document.createElement('button');
            documentTab.className = 'tab-btn';
            documentTab.dataset.tab = 'documents';
            documentTab.textContent = 'Documents';
            tabsContainer.appendChild(documentTab);
        }

        // Add document tab content
        const documentTabContent = document.createElement('div');
        documentTabContent.className = 'tab-content';
        documentTabContent.id = 'documents-tab';
        documentTabContent.appendChild(uploadArea);
        
        configPanel.appendChild(documentTabContent);
        
        // Setup tab switching
        this.setupDocumentTabEvents();
    }

    setupDocumentTabEvents() {
        document.addEventListener('click', (e) => {
            if (e.target.matches('.tab-btn[data-tab="documents"]')) {
                // Hide other tabs
                document.querySelectorAll('.tab-content').forEach(tab => {
                    tab.classList.remove('active');
                });
                document.querySelectorAll('.tab-btn').forEach(btn => {
                    btn.classList.remove('active');
                });
                
                // Show documents tab
                document.getElementById('documents-tab').classList.add('active');
                e.target.classList.add('active');
            }
        });
    }

    setupDocumentViewer() {
        const uploadZone = document.getElementById('document-upload-zone');
        const fileInput = document.getElementById('document-file-input');
        const browseBtn = document.getElementById('browse-documents-btn');
        const indexBtn = document.getElementById('index-documents-btn');
        const batchProcessBtn = document.getElementById('batch-process-btn');
        const clearBtn = document.getElementById('clear-documents-btn');

        if (!uploadZone) return;

        // Drag and drop
        uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadZone.classList.add('drag-over');
        });

        uploadZone.addEventListener('dragleave', () => {
            uploadZone.classList.remove('drag-over');
        });

        uploadZone.addEventListener('drop', async (e) => {
            e.preventDefault();
            uploadZone.classList.remove('drag-over');
            
            const files = Array.from(e.dataTransfer.files);
            await this.processFiles(files);
        });

        // Browse button
        if (browseBtn && fileInput) {
            browseBtn.addEventListener('click', () => {
                fileInput.click();
            });

            fileInput.addEventListener('change', async (e) => {
                const files = Array.from(e.target.files);
                await this.processFiles(files);
                fileInput.value = ''; // Reset input
            });
        }

        // Action buttons
        if (indexBtn) {
            indexBtn.addEventListener('click', () => this.indexDocuments());
        }
        
        if (batchProcessBtn) {
            batchProcessBtn.addEventListener('click', () => this.batchProcessDocuments());
        }
        
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearAllDocuments());
        }
    }

    async processFiles(files) {
        for (const file of files) {
            if (this.isValidFile(file)) {
                await this.uploadDocument(file);
            } else {
                this.eventBus.emit('error', { 
                    message: `Unsupported file format: ${file.name}` 
                });
            }
        }
    }

    isValidFile(file) {
        const extension = '.' + file.name.split('.').pop().toLowerCase();
        return this.supportedFormats.includes(extension);
    }

    async uploadDocument(file) {
        try {
            this.eventBus.emit('document-upload-start', { filename: file.name });
            
            // Read file content
            const content = await this.readFileContent(file);
            
            const document = {
                id: Date.now() + '_' + Math.random().toString(36).substr(2, 9),
                name: file.name,
                content: content,
                size: file.size,
                type: file.type,
                uploadDate: new Date().toISOString(),
                processed: false
            };
            
            this.documents.set(document.id, document);
            this.renderDocumentList();
            this.updateActionButtons();
            
            this.eventBus.emit('document-upload-success', { 
                filename: file.name, 
                document 
            });

        } catch (error) {
            console.error('Document upload failed:', error);
            this.eventBus.emit('document-upload-error', { 
                filename: file.name, 
                error: error.message 
            });
        }
    }

    async readFileContent(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            
            reader.onload = (e) => {
                resolve(e.target.result);
            };
            
            reader.onerror = () => {
                reject(new Error('Failed to read file'));
            };
            
            // For now, read as text. In production, you'd handle different file types
            reader.readAsText(file);
        });
    }

    renderDocumentList() {
        const documentItems = document.getElementById('document-items');
        if (!documentItems) return;

        if (this.documents.size === 0) {
            documentItems.innerHTML = '<p class="no-documents">No documents uploaded yet</p>';
            return;
        }

        documentItems.innerHTML = Array.from(this.documents.values()).map(doc => `
            <div class="document-item" data-doc-id="${doc.id}">
                <div class="document-info">
                    <div class="document-name">${doc.name}</div>
                    <div class="document-meta">
                        ${this.formatFileSize(doc.size)} • ${new Date(doc.uploadDate).toLocaleString()}
                        ${doc.processed ? '<span class="status-processed">✅ Processed</span>' : '<span class="status-pending">⏳ Pending</span>'}
                    </div>
                </div>
                <div class="document-actions">
                    <button class="btn-small view-document" data-doc-id="${doc.id}" title="View">👁️</button>
                    <button class="btn-small process-document" data-doc-id="${doc.id}" title="Process">⚙️</button>
                    <button class="btn-small remove-document" data-doc-id="${doc.id}" title="Remove">🗑️</button>
                </div>
            </div>
        `).join('');

        this.setupDocumentItemEvents();
    }

    setupDocumentItemEvents() {
        document.addEventListener('click', (e) => {
            const docId = e.target.dataset.docId;
            
            if (e.target.classList.contains('view-document')) {
                this.viewDocument(docId);
            } else if (e.target.classList.contains('process-document')) {
                this.processDocument(docId);
            } else if (e.target.classList.contains('remove-document')) {
                this.removeDocument(docId);
            }
        });
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    async indexDocuments() {
        const documents = Array.from(this.documents.values());
        if (documents.length === 0) return;

        try {
            this.eventBus.emit('document-indexing-start', { count: documents.length });
            
            const response = await this.apiClient.post('/api/rag/index', {
                documents: documents.map(doc => ({
                    id: doc.id,
                    content: doc.content,
                    metadata: {
                        name: doc.name,
                        type: doc.type,
                        uploadDate: doc.uploadDate
                    }
                }))
            });

            if (response.success) {
                // Mark documents as processed
                documents.forEach(doc => {
                    doc.processed = true;
                });
                
                this.renderDocumentList();
                this.eventBus.emit('document-indexing-success', { 
                    count: documents.length, 
                    indexed: response.indexed_count 
                });
            }

        } catch (error) {
            console.error('Document indexing failed:', error);
            this.eventBus.emit('document-indexing-error', { error: error.message });
        }
    }

    async batchProcessDocuments() {
        // Implementation for batch processing
        console.log('Batch process documents');
    }

    viewDocument(docId) {
        const document = this.documents.get(docId);
        if (!document) return;

        // Create a modal to view document content
        const modal = this.createDocumentViewModal(document);
        document.body.appendChild(modal);
    }

    createDocumentViewModal(doc) {
        const modal = document.createElement('div');
        modal.className = 'modal document-view-modal';
        modal.innerHTML = `
            <div class="modal-content large">
                <div class="modal-header">
                    <h3>📄 ${doc.name}</h3>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="document-metadata">
                        <p><strong>Size:</strong> ${this.formatFileSize(doc.size)}</p>
                        <p><strong>Type:</strong> ${doc.type}</p>
                        <p><strong>Uploaded:</strong> ${new Date(doc.uploadDate).toLocaleString()}</p>
                        <p><strong>Status:</strong> ${doc.processed ? '✅ Processed' : '⏳ Pending'}</p>
                    </div>
                    <div class="document-content">
                        <pre>${doc.content}</pre>
                    </div>
                </div>
            </div>
        `;

        // Close modal
        modal.querySelector('.modal-close').addEventListener('click', () => {
            modal.remove();
        });

        return modal;
    }

    async processDocument(docId) {
        const document = this.documents.get(docId);
        if (!document) return;

        try {
            // Process individual document
            await this.apiClient.post('/api/rag/index', {
                documents: [{
                    id: document.id,
                    content: document.content,
                    metadata: {
                        name: document.name,
                        type: document.type,
                        uploadDate: document.uploadDate
                    }
                }]
            });

            document.processed = true;
            this.renderDocumentList();
            
            this.eventBus.emit('document-processed', { document });

        } catch (error) {
            console.error('Document processing failed:', error);
            this.eventBus.emit('error', { message: `Failed to process ${document.name}`, error });
        }
    }

    removeDocument(docId) {
        const document = this.documents.get(docId);
        if (!document) return;

        if (confirm(`Remove document "${document.name}"?`)) {
            this.documents.delete(docId);
            this.renderDocumentList();
            this.updateActionButtons();
            
            this.eventBus.emit('document-removed', { document });
        }
    }

    clearAllDocuments() {
        if (this.documents.size === 0) return;

        if (confirm('Remove all documents? This action cannot be undone.')) {
            this.documents.clear();
            this.renderDocumentList();
            this.updateActionButtons();
            
            this.eventBus.emit('documents-cleared');
        }
    }

    updateActionButtons() {
        const indexBtn = document.getElementById('index-documents-btn');
        const batchProcessBtn = document.getElementById('batch-process-btn');
        
        const hasDocuments = this.documents.size > 0;
        
        if (indexBtn) indexBtn.disabled = !hasDocuments;
        if (batchProcessBtn) batchProcessBtn.disabled = !hasDocuments;
    }

    setupEventListeners() {
        this.eventBus.on('pipeline-ready', () => {
            this.updateActionButtons();
        });
    }

    getDocuments() {
        return Array.from(this.documents.values());
    }

    getProcessedDocuments() {
        return Array.from(this.documents.values()).filter(doc => doc.processed);
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DocumentProcessor;
}