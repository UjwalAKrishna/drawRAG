# 🔒 Security Model

RAG Builder v2.0 implements a comprehensive security framework to ensure safe plugin execution, data protection, and system integrity in production environments.

## 🛡️ Security Overview

### Security Principles

- **Defense in Depth**: Multiple security layers for comprehensive protection
- **Least Privilege**: Minimal permissions for plugin execution
- **Secure by Default**: Security features enabled out-of-the-box
- **Zero Trust**: No implicit trust between components
- **Audit Trail**: Complete logging of security-relevant events

### Threat Model

RAG Builder protects against:

- **Malicious Plugins**: Code injection, system access, data exfiltration
- **Data Breaches**: Unauthorized access to sensitive data
- **Resource Abuse**: CPU/memory exhaustion, disk space abuse
- **Network Attacks**: Unauthorized external connections
- **Privilege Escalation**: Unauthorized system access
- **Code Injection**: Dynamic code execution vulnerabilities

## 🔐 Plugin Security

### 1. **Plugin Isolation**

#### Sandboxed Execution
```python
# Plugins run in isolated environments
class SecurePluginRunner:
    def __init__(self, plugin_path: str):
        self.sandbox = create_sandbox(
            memory_limit="100MB",
            cpu_limit=0.5,
            network_access=False,
            filesystem_access="read-only"
        )
    
    def execute(self, capability: str, args: list):
        # Execute in isolated sandbox
        return self.sandbox.run(capability, args)
```

#### Resource Limits
```yaml
# Security configuration
security:
  plugin_limits:
    max_memory_mb: 512
    max_cpu_percent: 50
    max_execution_time_sec: 30
    max_file_size_mb: 10
    max_network_requests: 100
    
  sandbox:
    enabled: true
    network_isolation: true
    filesystem_isolation: true
    process_isolation: true
```

### 2. **Code Validation**

#### Static Analysis
```python
# Automatic security scanning
class SecurityScanner:
    DANGEROUS_PATTERNS = [
        r'import\s+os',
        r'import\s+subprocess',
        r'eval\s*\(',
        r'exec\s*\(',
        r'__import__',
        r'open\s*\(',
        r'file\s*\(',
    ]
    
    def scan_plugin(self, plugin_code: str) -> SecurityReport:
        violations = []
        
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, plugin_code):
                violations.append({
                    'type': 'dangerous_function',
                    'pattern': pattern,
                    'severity': 'high'
                })
        
        return SecurityReport(violations)
```

#### Import Restrictions
```python
# Whitelist allowed imports
ALLOWED_IMPORTS = {
    'standard': [
        'json', 'math', 'datetime', 'collections',
        'itertools', 'functools', 'typing'
    ],
    'scientific': [
        'numpy', 'pandas', 'scipy', 'sklearn'
    ],
    'ml': [
        'torch', 'tensorflow', 'transformers'
    ]
}

BLOCKED_IMPORTS = [
    'os', 'sys', 'subprocess', 'pickle',
    'marshal', 'importlib', '__builtins__'
]
```

#### Dynamic Validation
```python
# Runtime security checks
class RuntimeSecurityMonitor:
    def __init__(self):
        self.file_access_log = []
        self.network_access_log = []
    
    def monitor_plugin_execution(self, plugin_name: str):
        # Hook into system calls
        with self.security_context(plugin_name):
            # Monitor file access
            self.monitor_file_access()
            # Monitor network access  
            self.monitor_network_access()
            # Monitor memory allocation
            self.monitor_memory_usage()
```

### 3. **Permission System**

#### Capability-Based Permissions
```python
# Plugin permissions manifest
class PluginManifest:
    def __init__(self, plugin_name: str):
        self.name = plugin_name
        self.permissions = PermissionSet()
    
    def request_permission(self, permission: str, justification: str):
        """Request specific permission with justification."""
        self.permissions.add(Permission(
            type=permission,
            justification=justification,
            granted=False  # Requires explicit approval
        ))

# Example plugin with permissions
class NetworkPlugin(BasePlugin):
    REQUIRED_PERMISSIONS = [
        Permission('network.http_client', 'Need to fetch external data'),
        Permission('cache.write', 'Need to cache API responses')
    ]
    
    def fetch_data(self, url: str) -> dict:
        # Permission checked at runtime
        if not self.has_permission('network.http_client'):
            raise PermissionDenied("HTTP client access not granted")
        
        return requests.get(url).json()
```

#### Permission Types
```python
PERMISSION_TYPES = {
    'network.http_client': 'Make HTTP requests',
    'network.http_server': 'Accept HTTP connections',
    'filesystem.read': 'Read files from disk',
    'filesystem.write': 'Write files to disk',
    'database.read': 'Read from databases',
    'database.write': 'Write to databases',
    'cache.read': 'Read from cache',
    'cache.write': 'Write to cache',
    'system.environment': 'Access environment variables',
    'external.api': 'Call external APIs'
}
```

## 🔑 Authentication & Authorization

### 1. **API Authentication**

#### API Key Authentication
```python
# API key validation
class APIKeyAuthenticator:
    def __init__(self):
        self.keys = load_api_keys()
    
    def authenticate(self, request: Request) -> AuthResult:
        api_key = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not api_key:
            return AuthResult(authenticated=False, error="API key required")
        
        key_info = self.keys.get(api_key)
        if not key_info:
            return AuthResult(authenticated=False, error="Invalid API key")
        
        if key_info.expired:
            return AuthResult(authenticated=False, error="API key expired")
        
        return AuthResult(
            authenticated=True,
            user_id=key_info.user_id,
            permissions=key_info.permissions
        )
```

#### JWT Token Authentication
```python
import jwt
from datetime import datetime, timedelta

class JWTAuthenticator:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
    
    def generate_token(self, user_id: str, permissions: list) -> str:
        payload = {
            'user_id': user_id,
            'permissions': permissions,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def validate_token(self, token: str) -> TokenResult:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return TokenResult(valid=True, payload=payload)
        except jwt.ExpiredSignatureError:
            return TokenResult(valid=False, error="Token expired")
        except jwt.InvalidTokenError:
            return TokenResult(valid=False, error="Invalid token")
```

### 2. **Role-Based Access Control (RBAC)**

#### User Roles
```python
class Role:
    def __init__(self, name: str, permissions: list):
        self.name = name
        self.permissions = set(permissions)

# Default roles
ROLES = {
    'admin': Role('admin', [
        'plugin.create', 'plugin.update', 'plugin.delete',
        'system.config', 'system.logs', 'user.manage'
    ]),
    'developer': Role('developer', [
        'plugin.create', 'plugin.update', 'plugin.test',
        'capability.execute', 'logs.view'
    ]),
    'user': Role('user', [
        'capability.execute', 'capability.list'
    ]),
    'readonly': Role('readonly', [
        'capability.list', 'plugin.list'
    ])
}
```

#### Permission Checking
```python
class PermissionChecker:
    def __init__(self, user_roles: list):
        self.permissions = set()
        for role_name in user_roles:
            role = ROLES.get(role_name)
            if role:
                self.permissions.update(role.permissions)
    
    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions
    
    def require_permission(self, permission: str):
        if not self.has_permission(permission):
            raise PermissionDenied(f"Permission '{permission}' required")

# Usage in API endpoints
@require_permission('plugin.create')
def create_plugin(request: Request):
    # Only users with plugin.create permission can access
    pass
```

## 🛡️ Data Protection

### 1. **Data Encryption**

#### Encryption at Rest
```python
from cryptography.fernet import Fernet

class DataEncryption:
    def __init__(self, key: bytes = None):
        self.key = key or Fernet.generate_key()
        self.cipher = Fernet(self.key)
    
    def encrypt_data(self, data: str) -> bytes:
        """Encrypt sensitive data before storage."""
        return self.cipher.encrypt(data.encode())
    
    def decrypt_data(self, encrypted_data: bytes) -> str:
        """Decrypt data when retrieved."""
        return self.cipher.decrypt(encrypted_data).decode()

# Encrypt sensitive plugin data
class SecureDataPlugin(BasePlugin):
    def __init__(self):
        self.encryption = DataEncryption()
    
    def store_sensitive_data(self, data: str):
        encrypted = self.encryption.encrypt_data(data)
        # Store encrypted data
        self.storage.save(encrypted)
```

#### Encryption in Transit
```python
# Force HTTPS for all API communications
SECURITY_CONFIG = {
    'force_https': True,
    'ssl_cert_path': '/path/to/cert.pem',
    'ssl_key_path': '/path/to/key.pem',
    'min_tls_version': '1.2',
    'cipher_suites': [
        'ECDHE-RSA-AES256-GCM-SHA384',
        'ECDHE-RSA-AES128-GCM-SHA256'
    ]
}
```

### 2. **Secrets Management**

#### Environment-Based Secrets
```python
import os
from typing import Optional

class SecretManager:
    def __init__(self):
        self.secrets = {}
        self.load_secrets()
    
    def load_secrets(self):
        """Load secrets from environment variables."""
        secret_prefix = "RAGBUILDER_SECRET_"
        for key, value in os.environ.items():
            if key.startswith(secret_prefix):
                secret_name = key[len(secret_prefix):].lower()
                self.secrets[secret_name] = value
    
    def get_secret(self, name: str) -> Optional[str]:
        """Retrieve secret by name."""
        return self.secrets.get(name)
    
    def set_secret(self, name: str, value: str):
        """Set secret (runtime only, not persisted)."""
        self.secrets[name] = value

# Usage in plugins
class APIPlugin(BasePlugin):
    def __init__(self):
        self.secrets = SecretManager()
        self.api_key = self.secrets.get_secret('api_key')
    
    def call_external_api(self, data: str):
        headers = {'Authorization': f'Bearer {self.api_key}'}
        # Make secure API call
```

#### Integration with External Secret Stores
```python
# HashiCorp Vault integration
class VaultSecretManager(SecretManager):
    def __init__(self, vault_url: str, vault_token: str):
        self.vault_client = hvac.Client(url=vault_url, token=vault_token)
    
    def get_secret(self, path: str) -> Optional[str]:
        try:
            response = self.vault_client.secrets.kv.v2.read_secret_version(path=path)
            return response['data']['data']['value']
        except Exception:
            return None
```

## 🔍 Security Monitoring

### 1. **Audit Logging**

#### Security Event Logging
```python
import logging
from enum import Enum

class SecurityEventType(Enum):
    AUTHENTICATION_SUCCESS = "auth_success"
    AUTHENTICATION_FAILURE = "auth_failure"
    PERMISSION_DENIED = "permission_denied"
    PLUGIN_LOADED = "plugin_loaded"
    PLUGIN_EXECUTION = "plugin_execution"
    SECURITY_VIOLATION = "security_violation"

class SecurityAuditor:
    def __init__(self):
        self.logger = logging.getLogger('security')
        self.setup_logging()
    
    def log_event(self, event_type: SecurityEventType, details: dict):
        """Log security-relevant events."""
        event_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type.value,
            'user_id': details.get('user_id'),
            'source_ip': details.get('source_ip'),
            'user_agent': details.get('user_agent'),
            'details': details
        }
        
        self.logger.info(json.dumps(event_data))
    
    def log_security_violation(self, violation_type: str, details: dict):
        """Log security violations with high priority."""
        self.log_event(SecurityEventType.SECURITY_VIOLATION, {
            'violation_type': violation_type,
            **details
        })
        
        # Send immediate alert for critical violations
        if violation_type in ['code_injection', 'privilege_escalation']:
            self.send_security_alert(violation_type, details)
```

#### Audit Trail
```python
# Comprehensive audit trail
class AuditTrail:
    def __init__(self):
        self.events = []
    
    def record_plugin_execution(self, plugin_name: str, capability: str, 
                               user_id: str, success: bool):
        event = {
            'timestamp': datetime.utcnow(),
            'type': 'plugin_execution',
            'plugin': plugin_name,
            'capability': capability,
            'user_id': user_id,
            'success': success
        }
        self.events.append(event)
        self.persist_event(event)
    
    def record_permission_check(self, user_id: str, permission: str, granted: bool):
        event = {
            'timestamp': datetime.utcnow(),
            'type': 'permission_check',
            'user_id': user_id,
            'permission': permission,
            'granted': granted
        }
        self.events.append(event)
        self.persist_event(event)
```

### 2. **Intrusion Detection**

#### Anomaly Detection
```python
class SecurityMonitor:
    def __init__(self):
        self.baseline_metrics = self.load_baseline()
        self.current_metrics = {}
    
    def detect_anomalies(self):
        """Detect unusual patterns in system behavior."""
        anomalies = []
        
        # Check for unusual plugin execution patterns
        if self.current_metrics.get('plugin_executions_per_minute', 0) > \
           self.baseline_metrics.get('max_executions_per_minute', 100):
            anomalies.append({
                'type': 'high_execution_rate',
                'severity': 'medium'
            })
        
        # Check for suspicious API calls
        if self.current_metrics.get('failed_auth_attempts', 0) > 10:
            anomalies.append({
                'type': 'brute_force_attack',
                'severity': 'high'
            })
        
        return anomalies
    
    def monitor_plugin_behavior(self, plugin_name: str):
        """Monitor individual plugin behavior for anomalies."""
        plugin_metrics = self.get_plugin_metrics(plugin_name)
        
        # Check for resource abuse
        if plugin_metrics.memory_usage > 500:  # MB
            self.alert_resource_abuse(plugin_name, 'memory')
        
        if plugin_metrics.cpu_usage > 80:  # Percent
            self.alert_resource_abuse(plugin_name, 'cpu')
```

### 3. **Security Alerts**

#### Real-time Alerting
```python
class SecurityAlertManager:
    def __init__(self):
        self.alert_channels = [
            EmailAlertChannel('security@company.com'),
            SlackAlertChannel('security-alerts'),
            SyslogAlertChannel()
        ]
    
    def send_security_alert(self, alert_type: str, details: dict):
        """Send immediate security alerts."""
        alert = SecurityAlert(
            type=alert_type,
            severity=self.get_severity(alert_type),
            timestamp=datetime.utcnow(),
            details=details
        )
        
        for channel in self.alert_channels:
            channel.send_alert(alert)
    
    def get_severity(self, alert_type: str) -> str:
        severity_map = {
            'code_injection': 'critical',
            'privilege_escalation': 'critical',
            'brute_force_attack': 'high',
            'resource_abuse': 'medium',
            'permission_denied': 'low'
        }
        return severity_map.get(alert_type, 'medium')
```

## ⚙️ Security Configuration

### Production Security Settings

```yaml
# security.yaml - Production configuration
security:
  # Authentication
  authentication:
    required: true
    methods: ['api_key', 'jwt']
    session_timeout: 3600
    max_failed_attempts: 5
    lockout_duration: 300
  
  # Plugin security
  plugins:
    sandbox_enabled: true
    code_validation: strict
    resource_limits:
      memory_mb: 256
      cpu_percent: 25
      execution_time_sec: 15
    
    allowed_imports:
      - json
      - math
      - datetime
      - numpy
      - pandas
    
    blocked_imports:
      - os
      - sys
      - subprocess
      - pickle
  
  # Network security
  network:
    force_https: true
    allowed_hosts: ['api.company.com']
    rate_limiting:
      requests_per_minute: 60
      burst_size: 10
  
  # Data protection
  data:
    encryption_at_rest: true
    encryption_algorithm: 'AES-256-GCM'
    key_rotation_days: 90
  
  # Monitoring
  monitoring:
    audit_logging: true
    security_events: true
    anomaly_detection: true
    alert_channels:
      - email: 'security@company.com'
      - slack: '#security-alerts'
```

### Security Best Practices

#### For Plugin Developers
```python
# ✅ Good - Secure plugin example
class SecurePlugin(BasePlugin):
    def process_text(self, text: str) -> str:
        # Validate input
        if not isinstance(text, str):
            raise ValueError("Input must be string")
        
        if len(text) > 10000:  # Prevent memory abuse
            raise ValueError("Input too large")
        
        # Safe processing
        result = text.strip().lower()
        return result

# ❌ Bad - Insecure plugin example
class InsecurePlugin(BasePlugin):
    def dangerous_eval(self, code: str):
        # Never use eval with user input!
        return eval(code)
    
    def file_access(self, filename: str):
        # Uncontrolled file access
        with open(filename, 'r') as f:
            return f.read()
```

#### For Deployment
```bash
# Secure deployment checklist
export RAGBUILDER_FORCE_HTTPS=true
export RAGBUILDER_AUTH_REQUIRED=true
export RAGBUILDER_SANDBOX_ENABLED=true
export RAGBUILDER_LOG_SECURITY_EVENTS=true

# Restrict file permissions
chmod 600 /path/to/secrets.env
chmod 700 /path/to/plugin/directory

# Use dedicated user account
useradd --system --shell /bin/false ragbuilder
chown -R ragbuilder:ragbuilder /path/to/ragbuilder
```

---

RAG Builder v2.0's security model provides enterprise-grade protection while maintaining ease of use for developers. The layered security approach ensures safe plugin execution and data protection in production environments.