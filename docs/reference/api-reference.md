# 📖 API Reference

Complete REST API documentation for RAG Builder v2.0.

## 🌐 Base URL

```
http://localhost:8000/api
```

## 🔧 Core Endpoints

### 1. Execute Capability

Execute any plugin capability by name.

```http
POST /api/call/{capability_name}
```

#### Parameters

| Parameter | Type | Location | Description |
|-----------|------|----------|-------------|
| `capability_name` | string | path | Name of the capability to execute |
| `args` | array | body | Positional arguments for the capability |
| `kwargs` | object | body | Keyword arguments for the capability |

#### Request Example

```bash
curl -X POST http://localhost:8000/api/call/clean_text \
  -H "Content-Type: application/json" \
  -d '{
    "args": ["  Hello World  "],
    "kwargs": {}
  }'
```

#### Response Format

```json
{
  "success": true,
  "result": "hello world",
  "execution_time": 0.001,
  "plugin_name": "text_processor",
  "capability": "clean_text"
}
```

#### Error Response

```json
{
  "success": false,
  "error": "Capability 'invalid_function' not found",
  "error_type": "CapabilityNotFound",
  "execution_time": 0.0
}
```

### 2. List Capabilities

Get all available capabilities across all plugins.

```http
GET /api/capabilities
```

#### Response Example

```json
{
  "success": true,
  "capabilities": [
    {
      "name": "clean_text",
      "plugin": "text_processor",
      "description": "Clean and normalize text",
      "parameters": [
        {
          "name": "text",
          "type": "str",
          "required": true,
          "description": "Text to clean"
        }
      ],
      "return_type": "str"
    },
    {
      "name": "count_words",
      "plugin": "text_processor", 
      "description": "Count words in text",
      "parameters": [
        {
          "name": "text",
          "type": "str",
          "required": true
        }
      ],
      "return_type": "int"
    }
  ],
  "total_count": 15
}
```

### 3. List Plugins

Get information about all loaded plugins.

```http
GET /api/plugins
```

#### Response Example

```json
{
  "success": true,
  "plugins": [
    {
      "name": "text_processor",
      "file_path": "/plugins/text_processor.py",
      "status": "loaded",
      "capabilities": ["clean_text", "count_words", "reverse_text"],
      "load_time": "2024-01-15T10:30:00Z",
      "error": null
    },
    {
      "name": "smart_llm",
      "file_path": "/plugins/smart_llm.py", 
      "status": "loaded",
      "capabilities": ["generate_text", "analyze_sentiment"],
      "load_time": "2024-01-15T10:30:01Z",
      "error": null
    }
  ],
  "total_count": 8,
  "loaded_count": 7,
  "error_count": 1
}
```

### 4. Get Plugin Details

Get detailed information about a specific plugin.

```http
GET /api/plugins/{plugin_name}
```

#### Response Example

```json
{
  "success": true,
  "plugin": {
    "name": "text_processor",
    "file_path": "/plugins/text_processor.py",
    "status": "loaded",
    "capabilities": [
      {
        "name": "clean_text",
        "description": "Clean and normalize text",
        "parameters": [
          {
            "name": "text",
            "type": "str",
            "required": true,
            "description": "Text to clean"
          }
        ],
        "return_type": "str",
        "source_code": "def clean_text(text: str) -> str:\n    return text.strip().lower()"
      }
    ],
    "metadata": {
      "author": "RAG Builder Team",
      "version": "1.0.0",
      "description": "Basic text processing utilities"
    },
    "dependencies": [],
    "load_time": "2024-01-15T10:30:00Z"
  }
}
```

### 5. Health Check

Check framework health and status.

```http
GET /api/health
```

#### Response Example

```json
{
  "success": true,
  "status": "healthy",
  "version": "2.0.0",
  "uptime": 3600,
  "plugins": {
    "total": 8,
    "loaded": 7,
    "failed": 1
  },
  "capabilities": {
    "total": 23
  },
  "memory_usage": {
    "used_mb": 156,
    "available_mb": 7844
  },
  "timestamp": "2024-01-15T14:30:00Z"
}
```

### 6. Reload Plugins

Force reload all plugins (useful for development).

```http
POST /api/reload
```

#### Response Example

```json
{
  "success": true,
  "message": "All plugins reloaded successfully",
  "plugins_reloaded": 8,
  "capabilities_loaded": 23,
  "reload_time": 0.15
}
```

## 🚀 Advanced Endpoints

### 7. Execute with Metadata

Execute capability with additional metadata and options.

```http
POST /api/execute
```

#### Request Body

```json
{
  "capability": "generate_text",
  "args": ["Write a summary"],
  "kwargs": {
    "max_length": 100,
    "temperature": 0.7
  },
  "options": {
    "timeout": 30,
    "cache": true,
    "async": false
  },
  "metadata": {
    "user_id": "user123",
    "session_id": "session456"
  }
}
```

#### Response Example

```json
{
  "success": true,
  "result": "Generated summary text...",
  "execution_time": 1.25,
  "plugin_name": "smart_llm",
  "capability": "generate_text",
  "cached": false,
  "metadata": {
    "tokens_used": 150,
    "model": "gpt-3.5-turbo"
  }
}
```

### 8. Batch Execution

Execute multiple capabilities in a single request.

```http
POST /api/batch
```

#### Request Body

```json
{
  "requests": [
    {
      "id": "req1",
      "capability": "clean_text",
      "args": ["  Hello World  "]
    },
    {
      "id": "req2", 
      "capability": "count_words",
      "args": ["Hello beautiful world"]
    }
  ],
  "options": {
    "parallel": true,
    "fail_fast": false
  }
}
```

#### Response Example

```json
{
  "success": true,
  "results": [
    {
      "id": "req1",
      "success": true,
      "result": "hello world",
      "execution_time": 0.001
    },
    {
      "id": "req2",
      "success": true, 
      "result": 3,
      "execution_time": 0.002
    }
  ],
  "total_execution_time": 0.15,
  "successful_count": 2,
  "failed_count": 0
}
```

### 9. Plugin Validation

Validate plugin syntax and structure.

```http
POST /api/validate/{plugin_name}
```

#### Response Example

```json
{
  "success": true,
  "plugin": "text_processor",
  "validation": {
    "syntax_valid": true,
    "capabilities_valid": true,
    "dependencies_satisfied": true,
    "security_checks_passed": true
  },
  "warnings": [
    "Function 'helper_function' is not exported as capability"
  ],
  "errors": []
}
```

### 10. Performance Metrics

Get detailed performance metrics.

```http
GET /api/metrics
```

#### Response Example

```json
{
  "success": true,
  "metrics": {
    "requests": {
      "total": 1250,
      "successful": 1180,
      "failed": 70,
      "success_rate": 0.944
    },
    "capabilities": [
      {
        "name": "clean_text",
        "calls": 450,
        "avg_execution_time": 0.001,
        "success_rate": 0.998
      }
    ],
    "plugins": [
      {
        "name": "text_processor",
        "calls": 890,
        "avg_execution_time": 0.005,
        "memory_usage_mb": 12.5
      }
    ],
    "system": {
      "cpu_usage": 0.15,
      "memory_usage": 0.45,
      "disk_usage": 0.25
    }
  }
}
```

## 🔒 Authentication & Security

### API Key Authentication (Enterprise)

```http
GET /api/capabilities
Authorization: Bearer your-api-key-here
```

### Rate Limiting

Default rate limits:
- 1000 requests per minute per IP
- 100 requests per minute per capability
- Configurable via environment variables

## 📝 Request/Response Format

### Content Types

- **Request**: `application/json`
- **Response**: `application/json`

### Common Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `timeout` | integer | Request timeout in seconds (default: 30) |
| `cache` | boolean | Enable response caching (default: true) |
| `async` | boolean | Execute asynchronously (default: false) |

### Error Codes

| HTTP Code | Error Type | Description |
|-----------|------------|-------------|
| 200 | Success | Request completed successfully |
| 400 | BadRequest | Invalid request format or parameters |
| 404 | NotFound | Capability or plugin not found |
| 422 | ValidationError | Invalid parameter types or values |
| 500 | InternalError | Framework or plugin execution error |
| 503 | ServiceUnavailable | Framework overloaded or maintenance |

## 🧪 Testing the API

### Using curl

```bash
# Test basic capability
curl -X POST http://localhost:8000/api/call/clean_text \
  -H "Content-Type: application/json" \
  -d '{"args": ["  Test  "]}'

# List all capabilities
curl http://localhost:8000/api/capabilities

# Health check
curl http://localhost:8000/api/health
```

### Using Python

```python
import requests

# Execute capability
response = requests.post(
    'http://localhost:8000/api/call/clean_text',
    json={'args': ['  Hello World  ']}
)
result = response.json()
print(result['result'])  # "hello world"

# Get capabilities
response = requests.get('http://localhost:8000/api/capabilities')
capabilities = response.json()['capabilities']
```

### Using JavaScript

```javascript
// Execute capability
const response = await fetch('http://localhost:8000/api/call/clean_text', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({args: ['  Hello World  ']})
});
const result = await response.json();
console.log(result.result); // "hello world"
```

## 📊 WebSocket API (Real-time)

For real-time plugin execution and monitoring:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.send(JSON.stringify({
  type: 'execute',
  capability: 'process_stream',
  args: ['streaming data']
}));

ws.onmessage = (event) => {
  const result = JSON.parse(event.data);
  console.log('Real-time result:', result);
};
```

---

This API reference covers all available endpoints in RAG Builder v2.0. For more examples and advanced usage patterns, see the [Examples documentation](../examples/).