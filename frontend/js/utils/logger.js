// Logger - Centralized logging system
export class Logger {
    constructor(level = 'info') {
        this.level = level;
        this.levels = {
            debug: 0,
            info: 1,
            warn: 2,
            error: 3
        };
        this.logs = [];
        this.maxLogs = 1000;
    }
    
    log(level, message, ...args) {
        if (this.levels[level] < this.levels[this.level]) {
            return;
        }
        
        const logEntry = {
            timestamp: new Date().toISOString(),
            level,
            message,
            args: args.length > 0 ? args : undefined
        };
        
        this.logs.push(logEntry);
        
        // Limit log size
        if (this.logs.length > this.maxLogs) {
            this.logs.shift();
        }
        
        // Console output
        const consoleMethod = console[level] || console.log;
        consoleMethod(`[${level.toUpperCase()}] ${message}`, ...args);
        
        // Emit to event bus if available
        if (window.RAGBuilder && window.RAGBuilder.eventBus) {
            window.RAGBuilder.eventBus.emit('logs:new', logEntry);
        }
    }
    
    debug(message, ...args) {
        this.log('debug', message, ...args);
    }
    
    info(message, ...args) {
        this.log('info', message, ...args);
    }
    
    warn(message, ...args) {
        this.log('warn', message, ...args);
    }
    
    error(message, ...args) {
        this.log('error', message, ...args);
    }
    
    getLogs(level = null, limit = 100) {
        let logs = this.logs;
        
        if (level) {
            logs = logs.filter(log => log.level === level);
        }
        
        return logs.slice(-limit);
    }
    
    clearLogs() {
        this.logs = [];
    }
}