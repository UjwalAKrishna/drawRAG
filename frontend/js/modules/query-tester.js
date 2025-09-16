// Query Tester - Handles testing RAG pipeline queries
export class QueryTester {
    constructor(apiClient, eventBus) {
        this.apiClient = apiClient;
        this.eventBus = eventBus;
        this.testHistory = [];
        this.currentTest = null;
    }
    
    async runQuery(query, pipeline = null) {
        const testId = this.generateTestId();
        
        this.currentTest = {
            id: testId,
            query: query,
            pipeline: pipeline,
            startTime: new Date(),
            status: 'running'
        };
        
        this.eventBus.emit('query:started', this.currentTest);
        
        try {
            let result;
            
            if (pipeline) {
                // Execute using pipeline configuration
                result = await this.apiClient.executePipeline(pipeline, { query });
            } else {
                // Simple capability execution (fallback)
                result = await this.apiClient.executeCapability('answer_question', [query]);
            }
            
            this.currentTest.endTime = new Date();
            this.currentTest.duration = this.currentTest.endTime - this.currentTest.startTime;
            this.currentTest.result = result;
            this.currentTest.status = result.success ? 'completed' : 'failed';
            
            this.testHistory.push({ ...this.currentTest });
            this.eventBus.emit('query:completed', this.currentTest);
            
            return this.currentTest;
            
        } catch (error) {
            this.currentTest.endTime = new Date();
            this.currentTest.duration = this.currentTest.endTime - this.currentTest.startTime;
            this.currentTest.error = error.message;
            this.currentTest.status = 'error';
            
            this.testHistory.push({ ...this.currentTest });
            this.eventBus.emit('query:failed', this.currentTest);
            
            throw error;
        }
    }
    
    generateTestId() {
        return 'test_' + Math.random().toString(36).substr(2, 9);
    }
    
    getTestHistory() {
        return [...this.testHistory];
    }
    
    clearHistory() {
        this.testHistory = [];
        this.eventBus.emit('query:history-cleared');
    }
}