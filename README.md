# MASX AI Proxy Service

A high-performance FastAPI service for managing and validating free proxies with automatic refresh, rate limiting, and comprehensive testing.

## Features

- **🔄 Automatic Proxy Management**: Maintains a pool of working proxies with automatic refresh every 5 minutes
- **⚡ High Performance**: Async operations with concurrent proxy testing using thread pools
- **🛡️ Rate Limiting**: Built-in rate limiting to prevent abuse of refresh endpoints
- **📊 Health Monitoring**: Comprehensive health checks and statistics endpoints
- **🔍 Multi-Source Fetching**: Fetches proxies from HTML scraping and JSON CDN with fallback
- **✅ Proxy Validation**: Tests proxies against configurable URLs with timeout control
- **📝 Structured Logging**: JSON logging with structlog for production monitoring
- **🐳 Docker Ready**: Production-ready Docker container with health checks

## 🏗️ Architecture

```
proxy_service/
├── app/
│   ├── __init__.py          # Package initialization
│   ├── main.py              # FastAPI application entrypoint
│   ├── config.py            # Pydantic settings configuration
│   ├── proxy_manager.py     # Singleton proxy manager
│   ├── routes.py            # API endpoints and routing
│   ├── logging_config.py    # Structured logging setup
│   └── core/
│       └── concurrency.py   # CPU executor utilities
├── tests/                   # Comprehensive test suite
├── requirements.txt         # Python dependencies
├── Dockerfile              # Production Docker image
├── Makefile                # Development and deployment commands
└── README.md               # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- pip
- Docker (optional)

### Local Development

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd masx-ai-proxy-service
   ```

2. **Install dependencies**:
   ```bash
   make install
   # or
   pip install -r requirements.txt
   ```

3. **Run the service**:
   ```bash
   make run
   # or
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Access the service**:
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Docker Deployment

1. **Build and run**:
   ```bash
   make docker-deploy
   ```

2. **Or step by step**:
   ```bash
   make docker-build
   make docker-run
   ```

## 📚 API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Service information and available endpoints |
| `GET` | `/docs` | Interactive API documentation (Swagger UI) |
| `GET` | `/redoc` | Alternative API documentation |

### Proxy Management

| Method | Endpoint | Description | Response |
|--------|----------|-------------|----------|
| `GET` | `/api/v1/proxies` | Get all valid proxies | `{"success": true, "data": ["ip:port"], "message": "..."}` |
| `GET` | `/api/v1/proxy/random` | Get a random valid proxy | `{"success": true, "data": "ip:port", "message": "..."}` |
| `POST` | `/api/v1/refresh` | Force refresh proxy list | `{"success": true, "proxy_count": 5, "message": "..."}` |
| `GET` | `/api/v1/stats` | Get proxy manager statistics | `{"success": true, "data": {...}, "message": "..."}` |
| `GET` | `/api/v1/health` | Service health check | `{"success": true, "data": {"status": "healthy"}, "message": "..."}` |

### Example API Usage

```bash
# Get all proxies
curl http://localhost:8000/api/v1/proxies

# Get a random proxy
curl http://localhost:8000/api/v1/proxy/random

# Force refresh
curl -X POST http://localhost:8000/api/v1/refresh

# Check health
curl http://localhost:8000/api/v1/health

# Get statistics
curl http://localhost:8000/api/v1/stats
```

## ⚙️ Configuration

The service uses Pydantic settings with environment variable support. Create a `.env` file to override defaults:

```env
# Proxy Configuration
PROXY_WEBPAGE=https://free-proxy-list.net/
PROXY_TESTING_URL=https://httpbin.org/ip
REFRESH_INTERVAL_MINUTES=5
PROXY_TEST_TIMEOUT=3
BATCH_SIZE=20

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=false

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Rate Limiting
MAX_REFRESH_REQUESTS_PER_MINUTE=10
```

### Configuration Options

| Setting | Default | Description |
|---------|---------|-------------|
| `PROXY_WEBPAGE` | `https://free-proxy-list.net/` | URL to scrape proxies from |
| `PROXY_TESTING_URL` | `https://httpbin.org/ip` | URL to test proxy connectivity |
| `REFRESH_INTERVAL_MINUTES` | `5` | Automatic refresh interval |
| `PROXY_TEST_TIMEOUT` | `3` | Proxy test timeout in seconds |
| `BATCH_SIZE` | `20` | Number of proxies to test concurrently |
| `MAX_REFRESH_REQUESTS_PER_MINUTE` | `10` | Rate limit for manual refresh |

## 🧪 Testing

### Run All Tests

```bash
make test
# or
pytest tests/ -v
```

### Run Specific Test Categories

```bash
# Unit tests only
make test-unit

# Integration tests only
make test-integration
```

### Test Coverage

The test suite covers:
- ✅ ProxyManager singleton pattern
- ✅ Async proxy fetching and testing
- ✅ Rate limiting and error handling
- ✅ FastAPI endpoint responses
- ✅ Concurrent request handling
- ✅ Error scenarios and edge cases

## 🐳 Docker

### Build Image

```bash
make docker-build
```

### Run Container

```bash
make docker-run
```

### Stop and Clean

```bash
make docker-stop
make docker-clean
```

### Docker Compose (Optional)

Create a `docker-compose.yml` for more complex deployments:

```yaml
version: '3.8'
services:
  proxy-service:
    build: .
    ports:
      - "8000:8000"
    environment:
      - LOG_LEVEL=INFO
      - DEBUG=false
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## 📊 Monitoring & Logging

### Structured Logging

The service uses structlog for JSON-structured logging:

```json
{
  "timestamp": "2024-01-01T12:00:00.000Z",
  "level": "info",
  "logger": "ProxyManager",
  "service": "ProxyManager",
  "event": "Proxy refresh completed",
  "valid_count": 15,
  "total_fetched": 50
}
```

### Health Monitoring

- **Health Check**: `/api/v1/health` endpoint for load balancers
- **Statistics**: `/api/v1/stats` for monitoring proxy pool status
- **Metrics**: Built-in rate limiting and refresh tracking

## 🔧 Development

### Code Quality

```bash
# Format code
make format

# Run linting
make lint

# Clean up
make clean
```

### Development Commands

```bash
# Setup development environment
make dev-setup

# Run with auto-reload
make run

# Run tests with coverage
make test
```

## 🚨 Error Handling

The service implements comprehensive error handling:

- **HTTP Exceptions**: Proper HTTP status codes and error messages
- **Validation Errors**: Detailed validation error responses
- **Rate Limiting**: Graceful handling of exceeded limits
- **Proxy Failures**: Fallback mechanisms for failed proxy sources
- **Connection Timeouts**: Configurable timeouts for all network operations

## 🔒 Security Features

- **Rate Limiting**: Prevents abuse of refresh endpoints
- **Input Validation**: Pydantic models for request/response validation
- **CORS Configuration**: Configurable CORS policies
- **Error Sanitization**: No sensitive information in error responses

## 📈 Performance

- **Async Operations**: Non-blocking I/O for all operations
- **Batch Processing**: Concurrent proxy testing in configurable batches
- **Connection Pooling**: Efficient HTTP connection management
- **Memory Management**: Automatic cleanup of expired proxies

## 🤝 Contributing

1. Follow the existing code style and architecture
2. Add comprehensive tests for new features
3. Update documentation for API changes
4. Ensure all tests pass before submitting

## 📄 License

Copyright (c) 2025 Ateet Vatan Bahmani - MASX AI Project. All rights reserved.

## 🆘 Support

- **Documentation**: Check `/docs` endpoint for interactive API docs
- **Issues**: Report bugs and feature requests through the project repository
- **Contact**: ab@masxai.com | [MASXAI.com](https://masxai.com)

---

**Built with ❤️ by the MASX AI Team**
