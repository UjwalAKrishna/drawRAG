# ⚙️ Configuration Reference

Complete configuration options for RAG Builder v2.0.

## 📁 Configuration Files

RAG Builder uses multiple configuration files for different aspects of the system:

```
ragbuilder/
├── ragbuilder.yaml          # Main framework configuration
├── security.yaml           # Security settings
├── plugins.yaml            # Plugin-specific configuration
├── logging.yaml            # Logging configuration
└── .env                    # Environment variables
```

## 🔧 Main Configuration (`ragbuilder.yaml`)

### Framework Settings

```yaml
# ragbuilder.yaml
framework:
  name: "RAG Builder"
  version: "2.0.0"
  environment: "development"  # development, staging, production
  debug: false
  
  # Server configuration
  server:
    host: "0.0.0.0"
    port: 8000
    workers: 4
    worker_class: "uvicorn.workers.UvicornWorker"
    timeout: 30
    keepalive: 2
    max_requests: 1000
    max_requests_jitter: 50
  
  # Plugin system
  plugins:
    directory: "plugins/"
    auto_discovery: true
    hot_reload: true
    validation: "strict"  # strict, standard, permissive
    sandbox: true
    
    # Plugin loading
    load_on_startup: true
    lazy_loading: false
    max_load_time: 30
    
    # Resource limits
    limits:
      memory_mb: 512
      cpu_percent: 50
      execution_time_sec: 30
      file_size_mb: 10
```

### Database Configuration

```yaml
database:
  # Primary database
  primary:
    url: "${DATABASE_URL}"
    pool_size: 20
    max_overflow: 30
    pool_timeout: 30
    pool_recycle: 3600
    echo: false  # Set to true for SQL debugging
  
  # Cache database (Redis)
  cache:
    url: "${REDIS_URL}"
    db: 0
    max_connections: 50
    retry_on_timeout: true
    socket_timeout: 5
    socket_connect_timeout: 5
    
    # Cache settings
    default_ttl: 3600
    max_memory_policy: "allkeys-lru"
    
  # Vector database (optional)
  vector:
    provider: "pinecone"  # pinecone, weaviate, qdrant, chroma
    config:
      api_key: "${PINECONE_API_KEY}"
      environment: "${PINECONE_ENVIRONMENT}"
      index_name: "ragbuilder-vectors"
      dimension: 1536
```

### Caching Configuration

```yaml
cache:
  # Multi-level caching
  levels:
    memory:
      enabled: true
      max_size_mb: 256
      ttl_default: 1800
      eviction_policy: "lru"
      compression: false
    
    redis:
      enabled: true
      ttl_default: 3600
      compression: true
      serializer: "pickle"  # pickle, json, msgpack
    
    disk:
      enabled: false
      directory: ".cache/"
      max_size_gb: 1
      ttl_default: 86400
  
  # Cache strategies
  strategies:
    capability_results:
      levels: ["memory", "redis"]
      ttl: 1800
      key_prefix: "cap:"
    
    plugin_metadata:
      levels: ["memory"]
      ttl: 3600
      key_prefix: "meta:"
    
    external_api:
      levels: ["redis", "disk"]
      ttl: 7200
      key_prefix: "api:"
```

### Performance Settings

```yaml
performance:
  # Load balancing
  load_balancing:
    enabled: true
    strategy: "round_robin"  # round_robin, least_busy, random, weighted
    health_check_interval: 30
    
    # Auto-scaling
    auto_scaling:
      enabled: true
      min_instances: 2
      max_instances: 10
      
      # Scale up triggers
      scale_up:
        cpu_threshold: 70
        memory_threshold: 80
        queue_length: 100
        response_time_ms: 5000
      
      # Scale down triggers  
      scale_down:
        cpu_threshold: 30
        memory_threshold: 40
        queue_length: 10
        response_time_ms: 1000
      
      cooldown_period: 300
  
  # Connection pooling
  connection_pools:
    http:
      max_connections: 100
      max_keepalive_connections: 20
      keepalive_expiry: 5
    
    database:
      pool_size: 20
      max_overflow: 30
      pool_timeout: 30
  
  # Request handling
  requests:
    max_concurrent: 1000
    timeout: 30
    rate_limiting:
      enabled: true
      requests_per_minute: 60
      burst_size: 10
```

### Monitoring Configuration

```yaml
monitoring:
  # Metrics collection
  metrics:
    enabled: true
    provider: "prometheus"  # prometheus, datadog, cloudwatch
    port: 9090
    endpoint: "/metrics"
    
    # Custom metrics
    custom_metrics:
      - name: "plugin_execution_time"
        type: "histogram"
        buckets: [0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
      
      - name: "active_connections"
        type: "gauge"
        
      - name: "error_rate"
        type: "counter"
        labels: ["plugin", "error_type"]
  
  # Health checks
  health:
    enabled: true
    endpoint: "/api/health"
    interval: 30
    timeout: 10
    
    checks:
      - name: "database"
        enabled: true
        timeout: 5
      
      - name: "redis"
        enabled: true
        timeout: 3
      
      - name: "plugins"
        enabled: true
        timeout: 10
      
      - name: "external_apis"
        enabled: false
        timeout: 15
  
  # Alerting
  alerts:
    enabled: true
    channels:
      email:
        enabled: true
        smtp_server: "${SMTP_SERVER}"
        from_address: "${ALERT_FROM_EMAIL}"
        to_addresses: ["${ALERT_TO_EMAIL}"]
      
      slack:
        enabled: true
        webhook_url: "${SLACK_WEBHOOK_URL}"
        channel: "#alerts"
      
      pagerduty:
        enabled: false
        routing_key: "${PAGERDUTY_ROUTING_KEY}"
    
    rules:
      - name: "high_error_rate"
        condition: "error_rate > 0.05"
        severity: "critical"
        cooldown: 300
      
      - name: "high_response_time"
        condition: "avg_response_time > 5000"
        severity: "warning"
        cooldown: 600
      
      - name: "low_disk_space"
        condition: "disk_usage > 0.9"
        severity: "warning"
        cooldown: 1800
```

## 🔒 Security Configuration (`security.yaml`)

```yaml
# security.yaml
security:
  # Authentication
  authentication:
    enabled: true
    required_for_all_endpoints: true
    methods: ["api_key", "jwt", "oauth2"]
    
    # API Key authentication
    api_key:
      header_name: "Authorization"
      prefix: "Bearer "
      key_length: 32
      expiry_days: 365
      
      # Rate limiting per API key
      rate_limits:
        default: 1000  # requests per hour
        premium: 10000
        enterprise: 100000
    
    # JWT authentication
    jwt:
      secret_key: "${JWT_SECRET_KEY}"
      algorithm: "HS256"
      expiry_hours: 24
      refresh_expiry_days: 30
      issuer: "ragbuilder"
      audience: "ragbuilder-api"
    
    # OAuth2 authentication
    oauth2:
      providers:
        google:
          client_id: "${GOOGLE_CLIENT_ID}"
          client_secret: "${GOOGLE_CLIENT_SECRET}"
          scope: ["openid", "email", "profile"]
        
        github:
          client_id: "${GITHUB_CLIENT_ID}"
          client_secret: "${GITHUB_CLIENT_SECRET}"
          scope: ["user:email"]
  
  # Authorization (RBAC)
  authorization:
    enabled: true
    default_role: "user"
    
    roles:
      admin:
        permissions: ["*"]
        description: "Full system access"
      
      developer:
        permissions:
          - "plugin.create"
          - "plugin.update"
          - "plugin.delete"
          - "plugin.test"
          - "capability.execute"
          - "metrics.read"
        description: "Plugin development access"
      
      user:
        permissions:
          - "capability.execute"
          - "capability.list"
          - "plugin.list"
        description: "Basic user access"
      
      readonly:
        permissions:
          - "capability.list"
          - "plugin.list"
          - "health.check"
        description: "Read-only access"
  
  # Plugin security
  plugins:
    sandbox:
      enabled: true
      network_isolation: true
      filesystem_isolation: true
      process_isolation: true
      
      # Resource limits
      limits:
        memory_mb: 256
        cpu_percent: 25
        execution_time_sec: 15
        file_descriptors: 100
        network_connections: 10
    
    # Code validation
    validation:
      syntax_check: true
      import_restrictions: true
      dangerous_functions: true
      
      # Allowed imports
      allowed_imports:
        standard: ["json", "math", "datetime", "re", "uuid"]
        scientific: ["numpy", "pandas", "scipy"]
        ml: ["torch", "tensorflow", "transformers", "sklearn"]
      
      # Blocked imports
      blocked_imports: ["os", "sys", "subprocess", "pickle", "eval", "exec"]
  
  # Data protection
  data:
    encryption:
      at_rest: true
      in_transit: true
      algorithm: "AES-256-GCM"
      key_rotation_days: 90
    
    # Data classification
    classification:
      public:
        encryption_required: false
        access_logging: false
      
      internal:
        encryption_required: true
        access_logging: true
      
      confidential:
        encryption_required: true
        access_logging: true
        audit_trail: true
      
      restricted:
        encryption_required: true
        access_logging: true
        audit_trail: true
        approval_required: true
  
  # Network security
  network:
    https_only: true
    allowed_hosts: ["*.yourcompany.com"]
    cors:
      enabled: true
      allowed_origins: ["https://app.yourcompany.com"]
      allowed_methods: ["GET", "POST", "PUT", "DELETE"]
      allowed_headers: ["Authorization", "Content-Type"]
      max_age: 3600
    
    # Rate limiting
    rate_limiting:
      global:
        requests_per_minute: 1000
        burst_size: 100
      
      per_ip:
        requests_per_minute: 60
        burst_size: 10
        whitelist: ["192.168.1.0/24", "10.0.0.0/8"]
```

## 🔌 Plugin Configuration (`plugins.yaml`)

```yaml
# plugins.yaml
plugins:
  # Global plugin settings
  global:
    timeout: 30
    retries: 3
    cache_enabled: true
    logging_enabled: true
    metrics_enabled: true
  
  # Plugin-specific configurations
  configurations:
    text_processor:
      enabled: true
      config:
        max_text_length: 10000
        default_language: "en"
        enable_spell_check: false
      
      resources:
        memory_mb: 128
        cpu_percent: 20
        execution_time_sec: 10
    
    smart_llm:
      enabled: true
      config:
        default_model: "gpt-3.5-turbo"
        max_tokens: 2048
        temperature: 0.7
        api_key: "${OPENAI_API_KEY}"
        
        # Model configurations
        models:
          gpt-3.5-turbo:
            max_tokens: 4096
            cost_per_token: 0.000002
          
          gpt-4:
            max_tokens: 8192
            cost_per_token: 0.00006
      
      resources:
        memory_mb: 512
        cpu_percent: 50
        execution_time_sec: 30
    
    database_connector:
      enabled: true
      config:
        connection_string: "${DATABASE_URL}"
        pool_size: 10
        query_timeout: 30
        enable_query_logging: false
        
        # Query limitations
        max_results: 10000
        max_query_length: 5000
        allowed_operations: ["SELECT", "INSERT", "UPDATE"]
      
      resources:
        memory_mb: 256
        cpu_percent: 30
        execution_time_sec: 60
  
  # Plugin dependencies
  dependencies:
    text_processor:
      - name: "nltk"
        version: ">=3.8"
      - name: "spacy"
        version: ">=3.4"
    
    smart_llm:
      - name: "openai"
        version: ">=1.0.0"
      - name: "tiktoken"
        version: ">=0.5.0"
    
    database_connector:
      - name: "sqlalchemy"
        version: ">=2.0.0"
      - name: "psycopg2"
        version: ">=2.9.0"
  
  # Plugin validation rules
  validation:
    text_processor:
      input_types: ["str"]
      output_types: ["str", "list", "dict"]
      required_methods: ["clean_text", "tokenize"]
    
    smart_llm:
      input_types: ["str"]
      output_types: ["str", "dict"]
      required_methods: ["generate_text"]
      required_config: ["api_key"]
```

## 📊 Logging Configuration (`logging.yaml`)

```yaml
# logging.yaml
version: 1
disable_existing_loggers: false

formatters:
  standard:
    format: "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    datefmt: "%Y-%m-%d %H:%M:%S"
  
  detailed:
    format: "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(funcName)s() - %(message)s"
    datefmt: "%Y-%m-%d %H:%M:%S"
  
  json:
    class: "pythonjsonlogger.jsonlogger.JsonFormatter"
    format: "%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d"

handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: standard
    stream: ext://sys.stdout
  
  file:
    class: logging.handlers.RotatingFileHandler
    level: DEBUG
    formatter: detailed
    filename: logs/ragbuilder.log
    maxBytes: 104857600  # 100MB
    backupCount: 5
    encoding: utf8
  
  error_file:
    class: logging.handlers.RotatingFileHandler
    level: ERROR
    formatter: detailed
    filename: logs/errors.log
    maxBytes: 104857600  # 100MB
    backupCount: 10
    encoding: utf8
  
  security_file:
    class: logging.handlers.RotatingFileHandler
    level: WARNING
    formatter: json
    filename: logs/security.log
    maxBytes: 104857600  # 100MB
    backupCount: 20
    encoding: utf8
  
  syslog:
    class: logging.handlers.SysLogHandler
    level: WARNING
    formatter: json
    address: ["localhost", 514]

loggers:
  "":
    level: INFO
    handlers: [console, file]
    propagate: false
  
  ragbuilder:
    level: DEBUG
    handlers: [file, error_file]
    propagate: false
  
  ragbuilder.plugins:
    level: DEBUG
    handlers: [file]
    propagate: false
  
  ragbuilder.security:
    level: WARNING
    handlers: [security_file, syslog]
    propagate: false
  
  ragbuilder.performance:
    level: INFO
    handlers: [file]
    propagate: false
  
  # Third-party libraries
  urllib3:
    level: WARNING
    handlers: [file]
    propagate: false
  
  sqlalchemy:
    level: WARNING
    handlers: [file]
    propagate: false
```

## 🌍 Environment Variables

### Core Environment Variables

```bash
# Core settings
RAGBUILDER_ENV=production
RAGBUILDER_DEBUG=false
RAGBUILDER_LOG_LEVEL=INFO
RAGBUILDER_CONFIG_PATH=./config/

# Server settings
RAGBUILDER_HOST=0.0.0.0
RAGBUILDER_PORT=8000
RAGBUILDER_WORKERS=4

# Security
RAGBUILDER_SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=jwt-signing-secret
API_KEY_SALT=api-key-salt

# Database
DATABASE_URL=postgresql://user:password@host:5432/ragbuilder
REDIS_URL=redis://localhost:6379/0

# External services
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
HUGGINGFACE_API_KEY=your-huggingface-api-key

# Vector databases
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_ENVIRONMENT=your-pinecone-environment
WEAVIATE_URL=http://localhost:8080

# Monitoring
SENTRY_DSN=your-sentry-dsn
DATADOG_API_KEY=your-datadog-api-key
PROMETHEUS_PORT=9090

# Email/Notifications
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SLACK_WEBHOOK_URL=your-slack-webhook-url

# Cloud services
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_DEFAULT_REGION=us-west-2

GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

### Environment-Specific Variables

```bash
# Development environment
RAGBUILDER_ENV=development
RAGBUILDER_DEBUG=true
RAGBUILDER_HOT_RELOAD=true
RAGBUILDER_AUTO_VALIDATE=true

# Staging environment  
RAGBUILDER_ENV=staging
RAGBUILDER_DEBUG=false
RAGBUILDER_LOG_LEVEL=DEBUG
DATABASE_URL=postgresql://user:password@staging-db:5432/ragbuilder

# Production environment
RAGBUILDER_ENV=production
RAGBUILDER_DEBUG=false
RAGBUILDER_LOG_LEVEL=INFO
RAGBUILDER_HTTPS_ONLY=true
RAGBUILDER_RATE_LIMITING=true
```

## 📋 Configuration Validation

### Validation Schema

```python
# config/validation.py
from marshmallow import Schema, fields, validate

class ServerConfigSchema(Schema):
    host = fields.Str(required=True, validate=validate.Length(min=1))
    port = fields.Int(required=True, validate=validate.Range(min=1, max=65535))
    workers = fields.Int(required=True, validate=validate.Range(min=1, max=64))
    timeout = fields.Int(validate=validate.Range(min=1, max=300))

class DatabaseConfigSchema(Schema):
    url = fields.Url(required=True)
    pool_size = fields.Int(validate=validate.Range(min=1, max=100))
    max_overflow = fields.Int(validate=validate.Range(min=0, max=100))

class SecurityConfigSchema(Schema):
    authentication_enabled = fields.Bool(required=True)
    methods = fields.List(fields.Str(), required=True)
    https_only = fields.Bool(missing=True)

class ConfigValidator:
    def __init__(self):
        self.schemas = {
            'server': ServerConfigSchema(),
            'database': DatabaseConfigSchema(),
            'security': SecurityConfigSchema()
        }
    
    def validate_config(self, config: dict) -> dict:
        """Validate configuration and return errors."""
        errors = {}
        
        for section, schema in self.schemas.items():
            if section in config:
                result = schema.load(config[section])
                if result.errors:
                    errors[section] = result.errors
        
        return errors
```

### Configuration Loading

```python
# config/loader.py
import os
import yaml
from typing import Dict, Any

class ConfigLoader:
    def __init__(self, config_dir: str = "./config"):
        self.config_dir = config_dir
        self.config = {}
    
    def load_all_configs(self) -> Dict[str, Any]:
        """Load all configuration files."""
        config_files = [
            'ragbuilder.yaml',
            'security.yaml', 
            'plugins.yaml',
            'logging.yaml'
        ]
        
        for config_file in config_files:
            file_path = os.path.join(self.config_dir, config_file)
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    config_data = yaml.safe_load(f)
                    self.config.update(config_data)
        
        # Override with environment variables
        self._apply_env_overrides()
        
        return self.config
    
    def _apply_env_overrides(self):
        """Apply environment variable overrides."""
        env_mappings = {
            'RAGBUILDER_HOST': 'framework.server.host',
            'RAGBUILDER_PORT': 'framework.server.port',
            'RAGBUILDER_DEBUG': 'framework.debug',
            'DATABASE_URL': 'database.primary.url',
            'REDIS_URL': 'database.cache.url'
        }
        
        for env_var, config_path in env_mappings.items():
            if env_var in os.environ:
                self._set_nested_config(config_path, os.environ[env_var])
    
    def _set_nested_config(self, path: str, value: str):
        """Set nested configuration value using dot notation."""
        keys = path.split('.')
        current = self.config
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Convert string values to appropriate types
        if value.lower() in ('true', 'false'):
            value = value.lower() == 'true'
        elif value.isdigit():
            value = int(value)
        
        current[keys[-1]] = value
```

This configuration reference provides comprehensive control over all aspects of RAG Builder v2.0, from basic server settings to advanced security and monitoring configurations.