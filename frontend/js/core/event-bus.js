/**
 * Event Bus
 * Provides publish-subscribe pattern for component communication
 */
class EventBus {
    constructor() {
        this.listeners = new Map();
        this.maxListeners = 100;
        this.debugMode = false;
    }

    /**
     * Subscribe to an event
     * @param {string} eventName - Event name
     * @param {Function} callback - Event callback
     * @param {Object} options - Subscription options
     * @returns {Function} Unsubscribe function
     */
    on(eventName, callback, options = {}) {
        if (typeof callback !== 'function') {
            throw new Error('Event callback must be a function');
        }

        if (!this.listeners.has(eventName)) {
            this.listeners.set(eventName, []);
        }

        const eventListeners = this.listeners.get(eventName);
        
        if (eventListeners.length >= this.maxListeners) {
            console.warn(`Maximum listeners (${this.maxListeners}) exceeded for event: ${eventName}`);
        }

        const listener = {
            callback,
            once: options.once || false,
            priority: options.priority || 0,
            context: options.context || null
        };

        // Insert listener based on priority (higher priority first)
        const insertIndex = eventListeners.findIndex(l => l.priority < listener.priority);
        if (insertIndex === -1) {
            eventListeners.push(listener);
        } else {
            eventListeners.splice(insertIndex, 0, listener);
        }

        if (this.debugMode) {
            console.log(`EventBus: Registered listener for '${eventName}'`);
        }

        // Return unsubscribe function
        return () => this.off(eventName, callback);
    }

    /**
     * Subscribe to an event once
     * @param {string} eventName - Event name
     * @param {Function} callback - Event callback
     * @param {Object} options - Subscription options
     * @returns {Function} Unsubscribe function
     */
    once(eventName, callback, options = {}) {
        return this.on(eventName, callback, { ...options, once: true });
    }

    /**
     * Unsubscribe from an event
     * @param {string} eventName - Event name
     * @param {Function} callback - Event callback
     * @returns {boolean} Success status
     */
    off(eventName, callback) {
        if (!this.listeners.has(eventName)) {
            return false;
        }

        const eventListeners = this.listeners.get(eventName);
        const listenerIndex = eventListeners.findIndex(l => l.callback === callback);
        
        if (listenerIndex !== -1) {
            eventListeners.splice(listenerIndex, 1);
            
            if (eventListeners.length === 0) {
                this.listeners.delete(eventName);
            }

            if (this.debugMode) {
                console.log(`EventBus: Removed listener for '${eventName}'`);
            }
            
            return true;
        }

        return false;
    }

    /**
     * Remove all listeners for an event
     * @param {string} eventName - Event name
     * @returns {boolean} Success status
     */
    removeAllListeners(eventName) {
        if (eventName) {
            return this.listeners.delete(eventName);
        } else {
            this.listeners.clear();
            return true;
        }
    }

    /**
     * Emit an event
     * @param {string} eventName - Event name
     * @param {*} data - Event data
     * @returns {Promise<Array>} Array of results from listeners
     */
    async emit(eventName, data = null) {
        if (!this.listeners.has(eventName)) {
            if (this.debugMode) {
                console.log(`EventBus: No listeners for '${eventName}'`);
            }
            return [];
        }

        const eventListeners = [...this.listeners.get(eventName)];
        const results = [];

        if (this.debugMode) {
            console.log(`EventBus: Emitting '${eventName}' to ${eventListeners.length} listeners`);
        }

        for (const listener of eventListeners) {
            try {
                let result;
                
                if (listener.context) {
                    result = await listener.callback.call(listener.context, data);
                } else {
                    result = await listener.callback(data);
                }
                
                results.push({
                    success: true,
                    result
                });

                // Remove one-time listeners
                if (listener.once) {
                    this.off(eventName, listener.callback);
                }
            } catch (error) {
                console.error(`EventBus: Error in listener for '${eventName}':`, error);
                results.push({
                    success: false,
                    error: error.message
                });
            }
        }

        return results;
    }

    /**
     * Emit event synchronously
     * @param {string} eventName - Event name
     * @param {*} data - Event data
     * @returns {Array} Array of results from listeners
     */
    emitSync(eventName, data = null) {
        if (!this.listeners.has(eventName)) {
            return [];
        }

        const eventListeners = [...this.listeners.get(eventName)];
        const results = [];

        for (const listener of eventListeners) {
            try {
                let result;
                
                if (listener.context) {
                    result = listener.callback.call(listener.context, data);
                } else {
                    result = listener.callback(data);
                }
                
                results.push({
                    success: true,
                    result
                });

                // Remove one-time listeners
                if (listener.once) {
                    this.off(eventName, listener.callback);
                }
            } catch (error) {
                console.error(`EventBus: Error in listener for '${eventName}':`, error);
                results.push({
                    success: false,
                    error: error.message
                });
            }
        }

        return results;
    }

    /**
     * Get listener count for an event
     * @param {string} eventName - Event name
     * @returns {number} Listener count
     */
    listenerCount(eventName) {
        return this.listeners.get(eventName)?.length || 0;
    }

    /**
     * Get all event names with listeners
     * @returns {Array<string>} Event names
     */
    eventNames() {
        return Array.from(this.listeners.keys());
    }

    /**
     * Set maximum number of listeners per event
     * @param {number} maxListeners - Maximum listeners
     */
    setMaxListeners(maxListeners) {
        this.maxListeners = maxListeners;
    }

    /**
     * Enable or disable debug mode
     * @param {boolean} enabled - Debug mode enabled
     */
    setDebugMode(enabled) {
        this.debugMode = enabled;
    }

    /**
     * Create a namespaced event bus
     * @param {string} namespace - Namespace
     * @returns {Object} Namespaced event bus methods
     */
    namespace(namespace) {
        const namespacedBus = {
            on: (eventName, callback, options) => 
                this.on(`${namespace}:${eventName}`, callback, options),
            
            once: (eventName, callback, options) => 
                this.once(`${namespace}:${eventName}`, callback, options),
            
            off: (eventName, callback) => 
                this.off(`${namespace}:${eventName}`, callback),
            
            emit: (eventName, data) => 
                this.emit(`${namespace}:${eventName}`, data),
            
            emitSync: (eventName, data) => 
                this.emitSync(`${namespace}:${eventName}`, data),
            
            removeAllListeners: (eventName) => 
                this.removeAllListeners(eventName ? `${namespace}:${eventName}` : undefined)
        };

        return namespacedBus;
    }

    /**
     * Create event middleware
     * @param {Function} middleware - Middleware function
     */
    use(middleware) {
        if (typeof middleware !== 'function') {
            throw new Error('Middleware must be a function');
        }

        const originalEmit = this.emit.bind(this);
        
        this.emit = async function(eventName, data) {
            const processedData = await middleware(eventName, data);
            return originalEmit(eventName, processedData);
        };
    }

    /**
     * Wait for an event to be emitted
     * @param {string} eventName - Event name
     * @param {number} timeout - Timeout in milliseconds
     * @returns {Promise} Promise that resolves when event is emitted
     */
    waitFor(eventName, timeout = 5000) {
        return new Promise((resolve, reject) => {
            const timeoutId = setTimeout(() => {
                this.off(eventName, handler);
                reject(new Error(`Event '${eventName}' timeout after ${timeout}ms`));
            }, timeout);

            const handler = (data) => {
                clearTimeout(timeoutId);
                resolve(data);
            };

            this.once(eventName, handler);
        });
    }

    /**
     * Pipe events from one event to another
     * @param {string} fromEvent - Source event
     * @param {string} toEvent - Target event
     * @param {Function} transformer - Data transformer function
     * @returns {Function} Unpipe function
     */
    pipe(fromEvent, toEvent, transformer = null) {
        const handler = async (data) => {
            const transformedData = transformer ? await transformer(data) : data;
            await this.emit(toEvent, transformedData);
        };

        this.on(fromEvent, handler);
        
        // Return unpipe function
        return () => this.off(fromEvent, handler);
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { EventBus };
}