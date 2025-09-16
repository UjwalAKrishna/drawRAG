# 🔗 Integration Patterns

Common patterns for integrating RAG Builder with existing systems and external services.

## 🌐 External API Integration

### 1. **REST API Client Plugin**

```python
# plugins/api_client.py

import requests
import time
from typing import Dict, Any, Optional
from sdk.base_plugin import BasePlugin

class APIClient(BasePlugin):
    """Generic REST API client with retry and error handling."""
    
    def __init__(self):
        super().__init__()
        self.base_url = self.config.get('base_url', '')
        self.api_key = self.config.get('api_key', '')
        self.timeout = self.config.get('timeout', 30)
        self.max_retries = self.config.get('max_retries', 3)
        self.retry_delay = self.config.get('retry_delay', 1)
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request with retry logic."""
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        headers = kwargs.get('headers', {})
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        kwargs['headers'] = headers
        
        kwargs['timeout'] = self.timeout
        
        for attempt in range(self.max_retries):
            try:
                response = requests.request(method, url, **kwargs)
                response.raise_for_status()
                
                return {
                    'success': True,
                    'data': response.json() if response.content else {},
                    'status_code': response.status_code,
                    'headers': dict(response.headers)
                }
                
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    return {
                        'success': False,
                        'error': str(e),
                        'status_code': getattr(e.response, 'status_code', None)
                    }
                
                time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
        
        return {'success': False, 'error': 'Max retries exceeded'}
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make GET request."""
        return self._make_request('GET', endpoint, params=params)
    
    def post(self, endpoint: str, data: Optional[Dict] = None, json: Optional[Dict] = None) -> Dict[str, Any]:
        """Make POST request."""
        return self._make_request('POST', endpoint, data=data, json=json)
    
    def put(self, endpoint: str, data: Optional[Dict] = None, json: Optional[Dict] = None) -> Dict[str, Any]:
        """Make PUT request."""
        return self._make_request('PUT', endpoint, data=data, json=json)
    
    def delete(self, endpoint: str) -> Dict[str, Any]:
        """Make DELETE request."""
        return self._make_request('DELETE', endpoint)

# Specific API integrations
class SlackIntegration(APIClient):
    """Slack API integration plugin."""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://slack.com/api"
    
    def send_message(self, channel: str, text: str, blocks: Optional[list] = None) -> Dict[str, Any]:
        """Send message to Slack channel."""
        payload = {
            'channel': channel,
            'text': text
        }
        
        if blocks:
            payload['blocks'] = blocks
        
        return self.post('chat.postMessage', json=payload)
    
    def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """Get user information."""
        return self.get('users.info', params={'user': user_id})

class JiraIntegration(APIClient):
    """Jira API integration plugin."""
    
    def create_issue(self, project_key: str, summary: str, description: str, 
                    issue_type: str = "Task") -> Dict[str, Any]:
        """Create Jira issue."""
        payload = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "description": description,
                "issuetype": {"name": issue_type}
            }
        }
        
        return self.post('rest/api/2/issue', json=payload)
    
    def get_issue(self, issue_key: str) -> Dict[str, Any]:
        """Get Jira issue details."""
        return self.get(f'rest/api/2/issue/{issue_key}')
```

### 2. **Database Integration Plugin**

```python
# plugins/database_integration.py

import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from typing import List, Dict, Any, Optional
from sdk.data_source_plugin import DataSourcePlugin

class DatabaseIntegration(DataSourcePlugin):
    """Database integration with connection pooling."""
    
    def __init__(self):
        super().__init__()
        self.connection_string = self.config.get('connection_string')
        self.engine = None
        self.SessionLocal = None
        
    def connect(self):
        """Create database engine and session factory."""
        try:
            self.engine = sa.create_engine(
                self.connection_string,
                pool_size=10,
                max_overflow=20,
                pool_timeout=30,
                pool_recycle=3600
            )
            
            self.SessionLocal = sessionmaker(bind=self.engine)
            
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(sa.text("SELECT 1"))
            
            return self.engine
            
        except Exception as e:
            raise Exception(f"Database connection failed: {str(e)}")
    
    def execute_query(self, query: str, params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Execute SQL query and return results."""
        if self.engine is None:
            self.connect()
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(sa.text(query), params or {})
                
                # Convert to list of dictionaries
                columns = result.keys()
                rows = result.fetchall()
                
                return [dict(zip(columns, row)) for row in rows]
                
        except Exception as e:
            raise Exception(f"Query execution failed: {str(e)}")
    
    def execute_update(self, query: str, params: Optional[Dict] = None) -> int:
        """Execute UPDATE/INSERT/DELETE query."""
        if self.engine is None:
            self.connect()
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(sa.text(query), params or {})
                conn.commit()
                return result.rowcount
                
        except Exception as e:
            raise Exception(f"Update execution failed: {str(e)}")
    
    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Get table schema information."""
        if self.engine is None:
            self.connect()
        
        try:
            inspector = sa.inspect(self.engine)
            columns = inspector.get_columns(table_name)
            
            return [
                {
                    'name': col['name'],
                    'type': str(col['type']),
                    'nullable': col['nullable'],
                    'primary_key': col.get('primary_key', False)
                }
                for col in columns
            ]
            
        except Exception as e:
            raise Exception(f"Schema retrieval failed: {str(e)}")
    
    def list_tables(self) -> List[str]:
        """List all tables in the database."""
        if self.engine is None:
            self.connect()
        
        try:
            inspector = sa.inspect(self.engine)
            return inspector.get_table_names()
            
        except Exception as e:
            raise Exception(f"Table listing failed: {str(e)}")
```

## 🔄 Webhook Integration

### 3. **Webhook Handler Plugin**

```python
# plugins/webhook_handler.py

import hmac
import hashlib
import json
from typing import Dict, Any, Callable, Optional
from flask import Flask, request, jsonify
from sdk.base_plugin import BasePlugin

class WebhookHandler(BasePlugin):
    """Handle incoming webhooks from external services."""
    
    def __init__(self):
        super().__init__()
        self.app = Flask(__name__)
        self.handlers = {}
        self.setup_routes()
    
    def setup_routes(self):
        """Setup webhook routes."""
        @self.app.route('/webhook/<service>', methods=['POST'])
        def handle_webhook(service):
            return self.process_webhook(service, request)
    
    def register_handler(self, service: str, handler: Callable, secret: Optional[str] = None):
        """Register a webhook handler for a service."""
        self.handlers[service] = {
            'handler': handler,
            'secret': secret
        }
    
    def verify_signature(self, payload: bytes, signature: str, secret: str) -> bool:
        """Verify webhook signature."""
        if not secret:
            return True
        
        expected_signature = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(f"sha256={expected_signature}", signature)
    
    def process_webhook(self, service: str, request) -> Dict[str, Any]:
        """Process incoming webhook."""
        if service not in self.handlers:
            return jsonify({'error': 'Service not supported'}), 404
        
        handler_info = self.handlers[service]
        handler = handler_info['handler']
        secret = handler_info.get('secret')
        
        # Verify signature if secret is provided
        if secret:
            signature = request.headers.get('X-Hub-Signature-256', '')
            if not self.verify_signature(request.data, signature, secret):
                return jsonify({'error': 'Invalid signature'}), 401
        
        try:
            # Parse webhook data
            webhook_data = request.get_json()
            
            # Call handler
            result = handler(webhook_data)
            
            return jsonify({
                'success': True,
                'result': result
            })
            
        except Exception as e:
            self.logger.error(f"Webhook processing error: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    def start_server(self, host: str = '0.0.0.0', port: int = 5000):
        """Start webhook server."""
        self.app.run(host=host, port=port)

# Specific webhook integrations
class GitHubWebhooks(WebhookHandler):
    """GitHub webhook integration."""
    
    def __init__(self):
        super().__init__()
        self.register_handler('github', self.handle_github_webhook)
    
    def handle_github_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle GitHub webhook events."""
        event_type = data.get('action', 'unknown')
        
        if 'pull_request' in data:
            return self.handle_pull_request(data)
        elif 'push' in data:
            return self.handle_push(data)
        elif 'issues' in data:
            return self.handle_issue(data)
        
        return {'message': f'Handled {event_type} event'}
    
    def handle_pull_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle pull request events."""
        pr = data['pull_request']
        action = data['action']
        
        return {
            'type': 'pull_request',
            'action': action,
            'pr_number': pr['number'],
            'title': pr['title'],
            'author': pr['user']['login']
        }
    
    def handle_push(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle push events."""
        return {
            'type': 'push',
            'ref': data['ref'],
            'commits': len(data['commits']),
            'author': data['pusher']['name']
        }
```

## 📬 Message Queue Integration

### 4. **Message Queue Plugin**

```python
# plugins/message_queue.py

import json
import pika
import redis
from typing import Dict, Any, Callable, Optional
from sdk.base_plugin import BasePlugin

class MessageQueuePlugin(BasePlugin):
    """Message queue integration plugin."""
    
    def __init__(self):
        super().__init__()
        self.connection = None
        self.channel = None
        
    def connect_rabbitmq(self, host: str = 'localhost', port: int = 5672, 
                        username: str = 'guest', password: str = 'guest'):
        """Connect to RabbitMQ."""
        try:
            credentials = pika.PlainCredentials(username, password)
            parameters = pika.ConnectionParameters(host, port, '/', credentials)
            
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            return True
        except Exception as e:
            raise Exception(f"RabbitMQ connection failed: {str(e)}")
    
    def publish_message(self, queue_name: str, message: Dict[str, Any], 
                       exchange: str = '', routing_key: Optional[str] = None) -> bool:
        """Publish message to queue."""
        if not self.channel:
            raise Exception("Not connected to message queue")
        
        try:
            # Declare queue
            self.channel.queue_declare(queue=queue_name, durable=True)
            
            # Serialize message
            message_body = json.dumps(message)
            
            # Publish message
            self.channel.basic_publish(
                exchange=exchange,
                routing_key=routing_key or queue_name,
                body=message_body,
                properties=pika.BasicProperties(delivery_mode=2)  # Make message persistent
            )
            
            return True
        except Exception as e:
            raise Exception(f"Message publishing failed: {str(e)}")
    
    def consume_messages(self, queue_name: str, callback: Callable):
        """Consume messages from queue."""
        if not self.channel:
            raise Exception("Not connected to message queue")
        
        try:
            # Declare queue
            self.channel.queue_declare(queue=queue_name, durable=True)
            
            def wrapper(ch, method, properties, body):
                try:
                    message = json.loads(body)
                    result = callback(message)
                    
                    # Acknowledge message
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    
                    return result
                except Exception as e:
                    self.logger.error(f"Message processing error: {str(e)}")
                    # Reject message
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            
            # Set up consumer
            self.channel.basic_qos(prefetch_count=1)
            self.channel.basic_consume(queue=queue_name, on_message_callback=wrapper)
            
            # Start consuming
            self.channel.start_consuming()
            
        except Exception as e:
            raise Exception(f"Message consumption failed: {str(e)}")

class RedisQueue(BasePlugin):
    """Redis-based message queue."""
    
    def __init__(self):
        super().__init__()
        self.redis_client = None
        
    def connect(self, host: str = 'localhost', port: int = 6379, db: int = 0):
        """Connect to Redis."""
        try:
            self.redis_client = redis.Redis(host=host, port=port, db=db)
            self.redis_client.ping()  # Test connection
            return True
        except Exception as e:
            raise Exception(f"Redis connection failed: {str(e)}")
    
    def enqueue(self, queue_name: str, message: Dict[str, Any]) -> bool:
        """Add message to queue."""
        if not self.redis_client:
            raise Exception("Not connected to Redis")
        
        try:
            message_json = json.dumps(message)
            self.redis_client.lpush(queue_name, message_json)
            return True
        except Exception as e:
            raise Exception(f"Enqueue failed: {str(e)}")
    
    def dequeue(self, queue_name: str, timeout: int = 0) -> Optional[Dict[str, Any]]:
        """Remove and return message from queue."""
        if not self.redis_client:
            raise Exception("Not connected to Redis")
        
        try:
            if timeout > 0:
                result = self.redis_client.brpop(queue_name, timeout=timeout)
            else:
                result = self.redis_client.rpop(queue_name)
            
            if result:
                if timeout > 0:
                    _, message_json = result
                else:
                    message_json = result
                
                return json.loads(message_json)
            
            return None
        except Exception as e:
            raise Exception(f"Dequeue failed: {str(e)}")
```

## 🔐 Authentication Integration

### 5. **OAuth Integration Plugin**

```python
# plugins/oauth_integration.py

import requests
import jwt
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sdk.base_plugin import BasePlugin

class OAuthProvider(BasePlugin):
    """OAuth 2.0 provider integration."""
    
    def __init__(self):
        super().__init__()
        self.client_id = self.config.get('client_id')
        self.client_secret = self.config.get('client_secret')
        self.redirect_uri = self.config.get('redirect_uri')
        
    def get_authorization_url(self, state: Optional[str] = None, scope: Optional[str] = None) -> str:
        """Generate OAuth authorization URL."""
        raise NotImplementedError("Subclasses must implement this method")
    
    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token."""
        raise NotImplementedError("Subclasses must implement this method")
    
    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information using access token."""
        raise NotImplementedError("Subclasses must implement this method")

class GoogleOAuth(OAuthProvider):
    """Google OAuth integration."""
    
    def __init__(self):
        super().__init__()
        self.auth_base_url = "https://accounts.google.com/o/oauth2/auth"
        self.token_url = "https://oauth2.googleapis.com/token"
        self.user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
    
    def get_authorization_url(self, state: Optional[str] = None, scope: Optional[str] = None) -> str:
        """Generate Google OAuth URL."""
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': scope or 'openid email profile',
            'access_type': 'offline',
            'prompt': 'consent'
        }
        
        if state:
            params['state'] = state
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{self.auth_base_url}?{query_string}"
    
    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchange code for Google tokens."""
        data = {
            'code': code,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': self.redirect_uri,
            'grant_type': 'authorization_code'
        }
        
        response = requests.post(self.token_url, data=data)
        response.raise_for_status()
        
        return response.json()
    
    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get Google user information."""
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(self.user_info_url, headers=headers)
        response.raise_for_status()
        
        return response.json()

class JWTManager(BasePlugin):
    """JWT token management."""
    
    def __init__(self):
        super().__init__()
        self.secret_key = self.config.get('jwt_secret_key')
        self.algorithm = self.config.get('jwt_algorithm', 'HS256')
        self.expiry_hours = self.config.get('jwt_expiry_hours', 24)
    
    def generate_token(self, user_data: Dict[str, Any]) -> str:
        """Generate JWT token."""
        payload = {
            'user_id': user_data['id'],
            'email': user_data['email'],
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=self.expiry_hours)
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return {'valid': True, 'payload': payload}
        except jwt.ExpiredSignatureError:
            return {'valid': False, 'error': 'Token expired'}
        except jwt.InvalidTokenError:
            return {'valid': False, 'error': 'Invalid token'}
    
    def refresh_token(self, token: str) -> Optional[str]:
        """Refresh an existing token."""
        verification = self.verify_token(token)
        if verification['valid']:
            payload = verification['payload']
            # Remove timing claims
            payload.pop('iat', None)
            payload.pop('exp', None)
            
            # Generate new token
            return self.generate_token({
                'id': payload['user_id'],
                'email': payload['email']
            })
        
        return None
```

## 🔄 Event-Driven Integration

### 6. **Event Bus Plugin**

```python
# plugins/event_bus.py

import asyncio
from typing import Dict, Any, Callable, List
from datetime import datetime
from sdk.base_plugin import BasePlugin

class EventBus(BasePlugin):
    """Event-driven integration bus."""
    
    def __init__(self):
        super().__init__()
        self.subscribers = {}
        self.event_history = []
        self.max_history = 1000
    
    def subscribe(self, event_type: str, handler: Callable, filter_func: Optional[Callable] = None):
        """Subscribe to events of a specific type."""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        
        self.subscribers[event_type].append({
            'handler': handler,
            'filter': filter_func
        })
    
    def publish(self, event_type: str, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Publish an event to all subscribers."""
        event = {
            'type': event_type,
            'data': data,
            'timestamp': datetime.utcnow().isoformat(),
            'id': len(self.event_history)
        }
        
        # Store in history
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)
        
        # Notify subscribers
        results = []
        if event_type in self.subscribers:
            for subscriber in self.subscribers[event_type]:
                handler = subscriber['handler']
                filter_func = subscriber.get('filter')
                
                # Apply filter if provided
                if filter_func and not filter_func(event):
                    continue
                
                try:
                    result = handler(event)
                    results.append({
                        'handler': handler.__name__,
                        'success': True,
                        'result': result
                    })
                except Exception as e:
                    results.append({
                        'handler': handler.__name__,
                        'success': False,
                        'error': str(e)
                    })
        
        return results
    
    def get_event_history(self, event_type: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get event history."""
        events = self.event_history
        
        if event_type:
            events = [e for e in events if e['type'] == event_type]
        
        return events[-limit:] if limit else events

# Integration orchestrator
class IntegrationOrchestrator(BasePlugin):
    """Orchestrate integrations using event-driven patterns."""
    
    def __init__(self):
        super().__init__()
        self.event_bus = EventBus()
        self.integrations = {}
        
    def register_integration(self, name: str, integration: BasePlugin):
        """Register an integration plugin."""
        self.integrations[name] = integration
        
        # Subscribe to relevant events
        if hasattr(integration, 'handle_events'):
            for event_type in integration.handle_events:
                self.event_bus.subscribe(event_type, integration.handle_event)
    
    def trigger_workflow(self, workflow_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger a workflow across multiple integrations."""
        workflow_event = f"workflow.{workflow_name}"
        results = self.event_bus.publish(workflow_event, data)
        
        return {
            'workflow': workflow_name,
            'triggered_at': datetime.utcnow().isoformat(),
            'results': results
        }

# Example usage
class CRMIntegration(BasePlugin):
    """CRM system integration example."""
    
    def __init__(self):
        super().__init__()
        self.handle_events = ['user.created', 'user.updated']
    
    def handle_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle user events."""
        event_type = event['type']
        user_data = event['data']
        
        if event_type == 'user.created':
            return self.create_crm_contact(user_data)
        elif event_type == 'user.updated':
            return self.update_crm_contact(user_data)
    
    def create_crm_contact(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create contact in CRM."""
        # Implementation would call CRM API
        return {'action': 'created', 'contact_id': '12345'}
    
    def update_crm_contact(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update contact in CRM."""
        # Implementation would call CRM API
        return {'action': 'updated', 'contact_id': '12345'}
```

These integration patterns provide robust, reusable solutions for connecting RAG Builder with external systems, enabling seamless data flow and automation across your technology stack.