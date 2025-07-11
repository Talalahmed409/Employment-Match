# Docker Compose Configuration Guide

This guide explains the updated docker-compose.yml configuration for the Employment Match API with chat integration.

## Overview

The docker-compose.yml file provides multiple service configurations for different deployment scenarios:

- **Production-like API** (`api`): Main service using the optimized Dockerfile
- **Chat-optimized API** (`api-chat`): Service optimized for HR Assistant chat functionality
- **Development API** (`api-dev`): Development service with hot reload
- **Database** (`db`): PostgreSQL database
- **Admin tools** (`pgadmin`, `redis`): Optional services for administration and caching

## Services

### 1. Database Service (`db`)

```yaml
db:
  image: postgres:15
  environment:
    POSTGRES_USER: employment_user
    POSTGRES_PASSWORD: password123
    POSTGRES_DB: employment_match
  ports:
    - "5432:5432"
```

**Features:**

- PostgreSQL 15 with health checks
- Persistent data storage
- Ready for production use

### 2. Main API Service (`api`)

```yaml
api:
  build:
    dockerfile: docker/Dockerfile
  ports:
    - "8080:8080"
```

**Features:**

- Production-optimized build
- Health checks included
- All chat functionality enabled
- Optimized for performance

### 3. Chat-Optimized API Service (`api-chat`)

```yaml
api-chat:
  build:
    dockerfile: docker/Dockerfile.chat
  ports:
    - "8083:8080"
  profiles:
    - chat
```

**Features:**

- Specifically optimized for chat functionality
- ChromaDB persistence
- Enhanced ML library support
- Non-root user for security
- CPU optimization settings

### 4. Development Service (`api-dev`)

```yaml
api-dev:
  command: uvicorn employment_match.API:app --host 0.0.0.0 --port 8080 --reload
  volumes:
    - .:/app
  profiles:
    - dev
```

**Features:**

- Hot reload for development
- Source code mounted for live editing
- Debug-friendly configuration

## Usage Scenarios

### 1. Basic Production Setup

```bash
# Start main API with database
docker-compose up api db

# Access API at http://localhost:8080
```

### 2. Chat-Focused Deployment

```bash
# Start chat-optimized API
docker-compose --profile chat up api-chat db

# Access chat API at http://localhost:8083
```

### 3. Development Environment

```bash
# Start development environment
docker-compose --profile dev up api-dev db

# Access dev API at http://localhost:8082
```

### 4. Full Stack with Admin Tools

```bash
# Start everything including admin tools
docker-compose --profile admin --profile cache up

# Services available:
# - API: http://localhost:8080
# - PgAdmin: http://localhost:8081
# - Redis: localhost:6379
```

## Environment Variables

### Required Environment Variables

Create a `.env` file in the project root:

```env
# API Keys
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_CLIENT_ID=your_google_client_id_here

# Optional: Override defaults
SECRET_KEY=your_custom_secret_key
DATABASE_URL=postgresql://user:pass@host:port/db
```

### Default Environment Variables

- `DATABASE_URL`: Automatically configured for local PostgreSQL
- `SECRET_KEY`: Default development key (change for production)
- `HOST`: 0.0.0.0
- `PORT`: 8080
- `UPLOAD_DIR`: uploads
- `MAX_FILE_SIZE`: 10485760 (10MB)
- `CHROMA_PERSIST_DIRECTORY`: /tmp/chroma_data

## Performance Optimizations

### Thread Configuration

The services include optimized thread settings for ML libraries:

```yaml
environment:
  OMP_NUM_THREADS: 2
  MKL_NUM_THREADS: 2
  NUMEXPR_NUM_THREADS: 2
  OPENBLAS_NUM_THREADS: 2
```

### Volume Mounts

- `./data:/app/data`: ESCO skills data
- `./uploads:/app/uploads`: CV uploads
- `chroma_data:/tmp/chroma_data`: ChromaDB persistence

## Health Checks

All services include health checks:

- **Database**: PostgreSQL readiness check
- **API Services**: HTTP health endpoint check
- **Intervals**: 30s with 10s timeout

## Security Features

### Chat Service Security

- Non-root user execution
- Proper file permissions
- Isolated ChromaDB storage
- Secure environment variable handling

### Network Isolation

- Bridge network configuration
- Service-to-service communication
- Port exposure only where needed

## Monitoring and Logging

### Health Endpoints

- API Health: `GET /health`
- Database Health: PostgreSQL readiness
- Service Dependencies: Proper startup order

### Logging

- Structured logging via FastAPI
- Docker log aggregation
- Health check logging

## Troubleshooting

### Common Issues

1. **Port Conflicts**

   ```bash
   # Check port usage
   netstat -tulpn | grep :8080

   # Use different ports
   docker-compose up -p 8084 api
   ```

2. **Database Connection Issues**

   ```bash
   # Check database health
   docker-compose exec db pg_isready -U employment_user

   # View database logs
   docker-compose logs db
   ```

3. **Memory Issues**

   ```bash
   # Monitor resource usage
   docker stats

   # Increase memory limits
   docker-compose up --scale api=1 --memory=2g
   ```

### Debug Commands

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f api

# Access service shell
docker-compose exec api bash

# Check service status
docker-compose ps

# Restart specific service
docker-compose restart api
```

## Production Considerations

### Security

1. Change default passwords
2. Use environment variables for secrets
3. Enable SSL/TLS
4. Configure proper firewall rules

### Performance

1. Use production database (not local PostgreSQL)
2. Configure proper resource limits
3. Set up monitoring and alerting
4. Use load balancing for high traffic

### Data Persistence

1. Configure proper backup strategies
2. Use managed database services
3. Set up data retention policies
4. Monitor storage usage

## Migration from Previous Versions

### Breaking Changes

1. Added health checks
2. Updated environment variables
3. New chat service profile
4. Enhanced security features

### Migration Steps

1. Backup existing data
2. Update environment variables
3. Test with new configuration
4. Deploy gradually

## Support

For issues and questions:

- Check the troubleshooting section
- Review service logs
- Consult the API documentation
- Check the chat integration guide

## Related Documentation

- [API Quick Reference](CHAT_QUICK_REFERENCE.md)
- [Chat Integration Guide](CHAT_INTEGRATION.md)
- [Cloud Deployment Guide](CLOUD_DEPLOYMENT_CHAT.md)
- [Database Guide](DATABASE_GUIDE.md)
