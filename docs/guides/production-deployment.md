# 🚀 Production Deployment Guide

Comprehensive guide for deploying RAG Builder v2.0 in production environments.

## 🎯 Deployment Overview

### Production Readiness Checklist

- [ ] **Security Configuration** - Authentication, encryption, access controls
- [ ] **Performance Optimization** - Caching, load balancing, resource limits
- [ ] **Monitoring & Logging** - Metrics, alerts, audit trails
- [ ] **High Availability** - Redundancy, failover, disaster recovery
- [ ] **Scalability** - Auto-scaling, load distribution
- [ ] **Maintenance** - Updates, backups, health checks

## 🛡️ Security Configuration

### 1. **Authentication Setup**

```yaml
# production-config.yaml
security:
  authentication:
    enabled: true
    methods: ["api_key", "jwt"]
    require_https: true
    
  api_keys:
    admin_key: "${ADMIN_API_KEY}"
    service_keys:
      - name: "frontend_service"
        key: "${FRONTEND_API_KEY}"
        permissions: ["capability.execute", "capability.list"]
      - name: "analytics_service"
        key: "${ANALYTICS_API_KEY}"
        permissions: ["metrics.read", "logs.read"]

  jwt:
    secret_key: "${JWT_SECRET_KEY}"
    algorithm: "HS256"
    expiry_hours: 24
```

### 2. **Environment Variables**

```bash
# .env.production
# Core Settings
RAGBUILDER_ENV=production
RAGBUILDER_DEBUG=false
RAGBUILDER_LOG_LEVEL=INFO

# Security
RAGBUILDER_SECRET_KEY=your-super-secret-key-here
ADMIN_API_KEY=admin-key-with-high-entropy
FRONTEND_API_KEY=frontend-service-key
ANALYTICS_API_KEY=analytics-service-key
JWT_SECRET_KEY=jwt-signing-secret

# Database
DATABASE_URL=postgresql://user:pass@host:5432/ragbuilder
REDIS_URL=redis://redis-host:6379/0

# External Services
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

# Monitoring
SENTRY_DSN=your-sentry-dsn
DATADOG_API_KEY=your-datadog-key
```

### 3. **SSL/TLS Configuration**

```nginx
# nginx.conf
server {
    listen 443 ssl http2;
    server_name api.yourcompany.com;
    
    ssl_certificate /path/to/ssl/cert.pem;
    ssl_certificate_key /path/to/ssl/private.key;
    
    # SSL Security
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    
    location / {
        proxy_pass http://ragbuilder_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

upstream ragbuilder_backend {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}
```

## 🐳 Docker Deployment

### 1. **Production Dockerfile**

```dockerfile
# Dockerfile.production
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash ragbuilder

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set ownership and permissions
RUN chown -R ragbuilder:ragbuilder /app
USER ragbuilder

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Expose port
EXPOSE 8000

# Start command
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "run_server:app"]
```

### 2. **Docker Compose for Production**

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  ragbuilder:
    build:
      context: .
      dockerfile: Dockerfile.production
    restart: unless-stopped
    ports:
      - "8000-8002:8000"
    environment:
      - RAGBUILDER_ENV=production
      - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@db:5432/ragbuilder
      - REDIS_URL=redis://redis:6379/0
    env_file:
      - .env.production
    volumes:
      - ./plugins:/app/plugins:ro
      - ./logs:/app/logs
    depends_on:
      - db
      - redis
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
        reservations:
          memory: 512M
          cpus: '0.25'

  db:
    image: postgres:15
    restart: unless-stopped
    environment:
      POSTGRES_DB: ragbuilder
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"

  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/ssl:ro
    depends_on:
      - ragbuilder

volumes:
  postgres_data:
  redis_data:
```

## ☁️ Cloud Deployment

### 1. **AWS Deployment with ECS**

```yaml
# ecs-task-definition.json
{
  "family": "ragbuilder-production",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::account:role/ragbuilder-task-role",
  "containerDefinitions": [
    {
      "name": "ragbuilder",
      "image": "your-ecr-repo/ragbuilder:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "RAGBUILDER_ENV",
          "value": "production"
        }
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:ragbuilder/db-url"
        },
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:ragbuilder/openai-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/ragbuilder",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/api/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3
      }
    }
  ]
}
```

### 2. **Kubernetes Deployment**

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ragbuilder
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ragbuilder
  template:
    metadata:
      labels:
        app: ragbuilder
    spec:
      containers:
      - name: ragbuilder
        image: your-registry/ragbuilder:v2.0
        ports:
        - containerPort: 8000
        env:
        - name: RAGBUILDER_ENV
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: ragbuilder-secrets
              key: database-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /api/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: plugins-volume
          mountPath: /app/plugins
          readOnly: true
      volumes:
      - name: plugins-volume
        configMap:
          name: ragbuilder-plugins
---
apiVersion: v1
kind: Service
metadata:
  name: ragbuilder-service
  namespace: production
spec:
  selector:
    app: ragbuilder
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ragbuilder-ingress
  namespace: production
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - api.yourcompany.com
    secretName: ragbuilder-tls
  rules:
  - host: api.yourcompany.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: ragbuilder-service
            port:
              number: 80
```

## 📊 Monitoring & Observability

### 1. **Prometheus Metrics**

```python
# monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Metrics definitions
REQUEST_COUNT = Counter('ragbuilder_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('ragbuilder_request_duration_seconds', 'Request duration')
ACTIVE_PLUGINS = Gauge('ragbuilder_active_plugins', 'Number of active plugins')
PLUGIN_EXECUTIONS = Counter('ragbuilder_plugin_executions_total', 'Plugin executions', ['plugin', 'capability'])

class MetricsMiddleware:
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            start_time = time.time()
            
            # Process request
            await self.app(scope, receive, send)
            
            # Record metrics
            duration = time.time() - start_time
            REQUEST_DURATION.observe(duration)
            REQUEST_COUNT.labels(
                method=scope["method"],
                endpoint=scope["path"],
                status="200"  # Simplified
            ).inc()
```

### 2. **Logging Configuration**

```python
# logging.conf
[loggers]
keys=root,ragbuilder,plugins,security

[handlers]
keys=console,file,syslog

[formatters]
keys=detailed,simple

[logger_root]
level=INFO
handlers=console,file

[logger_ragbuilder]
level=INFO
handlers=file,syslog
qualname=ragbuilder
propagate=0

[logger_plugins]
level=DEBUG
handlers=file
qualname=plugins
propagate=0

[logger_security]
level=WARNING
handlers=file,syslog
qualname=security
propagate=0

[handler_console]
class=StreamHandler
level=INFO
formatter=simple
args=(sys.stdout,)

[handler_file]
class=handlers.RotatingFileHandler
level=DEBUG
formatter=detailed
args=('/var/log/ragbuilder/app.log', 'a', 100*1024*1024, 5)

[handler_syslog]
class=handlers.SysLogHandler
level=WARNING
formatter=detailed
args=('/dev/log',)

[formatter_detailed]
format=%(asctime)s - %(name)s - %(levelname)s - %(message)s - [%(filename)s:%(lineno)d]

[formatter_simple]
format=%(levelname)s - %(message)s
```

### 3. **Health Checks**

```python
# health.py
from typing import Dict, Any
import psutil
import redis
import asyncpg

class HealthChecker:
    def __init__(self):
        self.checks = {
            'database': self.check_database,
            'redis': self.check_redis,
            'plugins': self.check_plugins,
            'system': self.check_system_resources
        }
    
    async def run_health_checks(self) -> Dict[str, Any]:
        results = {}
        overall_status = "healthy"
        
        for check_name, check_func in self.checks.items():
            try:
                result = await check_func()
                results[check_name] = result
                
                if result['status'] != 'healthy':
                    overall_status = "unhealthy"
                    
            except Exception as e:
                results[check_name] = {
                    'status': 'error',
                    'error': str(e)
                }
                overall_status = "unhealthy"
        
        return {
            'status': overall_status,
            'timestamp': datetime.utcnow().isoformat(),
            'checks': results
        }
    
    async def check_database(self) -> Dict[str, Any]:
        try:
            conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
            await conn.fetchval('SELECT 1')
            await conn.close()
            
            return {'status': 'healthy', 'message': 'Database connection OK'}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}
    
    async def check_redis(self) -> Dict[str, Any]:
        try:
            r = redis.from_url(os.getenv('REDIS_URL'))
            r.ping()
            
            return {'status': 'healthy', 'message': 'Redis connection OK'}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}
    
    async def check_plugins(self) -> Dict[str, Any]:
        # Check if plugins are loaded and responsive
        from backend.core.manager import PluginManager
        
        manager = PluginManager()
        plugin_count = len(manager.plugins)
        failed_plugins = [name for name, plugin in manager.plugins.items() 
                         if not plugin.is_healthy()]
        
        if failed_plugins:
            return {
                'status': 'degraded',
                'message': f'{len(failed_plugins)} plugins unhealthy',
                'failed_plugins': failed_plugins
            }
        
        return {
            'status': 'healthy',
            'plugin_count': plugin_count,
            'message': 'All plugins healthy'
        }
    
    async def check_system_resources(self) -> Dict[str, Any]:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        status = 'healthy'
        warnings = []
        
        if cpu_percent > 90:
            status = 'degraded'
            warnings.append(f'High CPU usage: {cpu_percent}%')
        
        if memory.percent > 90:
            status = 'degraded'
            warnings.append(f'High memory usage: {memory.percent}%')
        
        if disk.percent > 90:
            status = 'degraded'
            warnings.append(f'High disk usage: {disk.percent}%')
        
        return {
            'status': status,
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'disk_percent': disk.percent,
            'warnings': warnings
        }
```

## 🔄 Continuous Deployment

### 1. **GitHub Actions Workflow**

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]
    tags: ['v*']

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run tests
      run: |
        pytest tests/ --cov=backend --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v1
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: us-west-2
    
    - name: Login to Amazon ECR
      id: login-ecr
      uses: aws-actions/amazon-ecr-login@v1
    
    - name: Build and push Docker image
      env:
        ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        ECR_REPOSITORY: ragbuilder
        IMAGE_TAG: ${{ github.sha }}
      run: |
        docker build -f Dockerfile.production -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
        docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY:latest
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment: production
    steps:
    - name: Deploy to ECS
      run: |
        aws ecs update-service \
          --cluster ragbuilder-prod \
          --service ragbuilder-service \
          --force-new-deployment
```

### 2. **Blue-Green Deployment Script**

```bash
#!/bin/bash
# deploy.sh

set -e

# Configuration
CLUSTER_NAME="ragbuilder-prod"
SERVICE_NAME="ragbuilder-service"
NEW_IMAGE="$1"

if [ -z "$NEW_IMAGE" ]; then
    echo "Usage: $0 <new-image-uri>"
    exit 1
fi

echo "Starting blue-green deployment..."

# Get current task definition
CURRENT_TASK_DEF=$(aws ecs describe-services \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --query 'services[0].taskDefinition' \
    --output text)

echo "Current task definition: $CURRENT_TASK_DEF"

# Create new task definition with new image
NEW_TASK_DEF=$(aws ecs describe-task-definition \
    --task-definition $CURRENT_TASK_DEF \
    --query 'taskDefinition' \
    --output json | \
    jq --arg IMAGE "$NEW_IMAGE" '.containerDefinitions[0].image = $IMAGE' | \
    jq 'del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .placementConstraints, .compatibilities, .registeredAt, .registeredBy)')

# Register new task definition
NEW_TASK_DEF_ARN=$(echo $NEW_TASK_DEF | \
    aws ecs register-task-definition \
    --cli-input-json file:///dev/stdin \
    --query 'taskDefinition.taskDefinitionArn' \
    --output text)

echo "New task definition: $NEW_TASK_DEF_ARN"

# Update service to use new task definition
aws ecs update-service \
    --cluster $CLUSTER_NAME \
    --service $SERVICE_NAME \
    --task-definition $NEW_TASK_DEF_ARN

# Wait for deployment to complete
echo "Waiting for deployment to complete..."
aws ecs wait services-stable \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME

echo "Deployment completed successfully!"

# Health check
echo "Running health check..."
LOAD_BALANCER_DNS=$(aws elbv2 describe-load-balancers \
    --names ragbuilder-alb \
    --query 'LoadBalancers[0].DNSName' \
    --output text)

if curl -f "https://$LOAD_BALANCER_DNS/api/health"; then
    echo "Health check passed!"
else
    echo "Health check failed! Rolling back..."
    
    # Rollback to previous task definition
    aws ecs update-service \
        --cluster $CLUSTER_NAME \
        --service $SERVICE_NAME \
        --task-definition $CURRENT_TASK_DEF
    
    aws ecs wait services-stable \
        --cluster $CLUSTER_NAME \
        --services $SERVICE_NAME
    
    echo "Rollback completed."
    exit 1
fi
```

This production deployment guide provides a comprehensive foundation for deploying RAG Builder v2.0 in enterprise environments with proper security, monitoring, and scalability considerations.