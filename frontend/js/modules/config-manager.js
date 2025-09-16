// Config Manager - Handles application configuration
export class ConfigManager {
    constructor(eventBus) {
        this.eventBus = eventBus;
        this.config = {};
        this.defaultConfig = {
            theme: 'light',
            autoSave: true,
            showTooltips: true,
            gridSnap: false,
            notifications: true
        };
    }
    
    loadConfig() {
        try {
            const saved = localStorage.getItem('ragbuilder_config');
            this.config = saved ? JSON.parse(saved) : { ...this.defaultConfig };
        } catch (error) {
            this.config = { ...this.defaultConfig };
        }
        
        this.eventBus.emit('config:loaded', this.config);
        return this.config;
    }
    
    saveConfig() {
        try {
            localStorage.setItem('ragbuilder_config', JSON.stringify(this.config));
            this.eventBus.emit('config:saved', this.config);
            return true;
        } catch (error) {
            this.eventBus.emit('error', error);
            return false;
        }
    }
    
    updateConfig(updates) {
        this.config = { ...this.config, ...updates };
        this.saveConfig();
        this.eventBus.emit('config:updated', updates);
    }
    
    getConfig(key = null) {
        return key ? this.config[key] : this.config;
    }
    
    resetConfig() {
        this.config = { ...this.defaultConfig };
        this.saveConfig();
        this.eventBus.emit('config:reset');
    }
}