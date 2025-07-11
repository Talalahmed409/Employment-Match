# Docker Compose Quick Reference

## Quick Start Commands

### Basic Usage

```bash
# Start main API with database
docker-compose up api db

# Start in background
docker-compose up -d api db

# Stop all services
docker-compose down

# View logs
docker-compose logs -f
```

### Service Profiles

#### Chat-Optimized Deployment

```bash
# Start chat-optimized API
docker-compose --profile chat up api-chat db

# Access at http://localhost:8083
```

#### Development Environment

```bash
# Start development with hot reload
docker-compose --profile dev up api-dev db

# Access at http://localhost:8082
```

#### Full Stack (with admin tools)

```bash
# Start everything
docker-compose --profile admin --profile cache up

# Services:
# - API: http://localhost:8080
# - PgAdmin: http://localhost:8081 (admin/admin)
# - Redis: localhost:6379
```

## Service Ports

| Service    | Port | Description         |
| ---------- | ---- | ------------------- |
| `api`      | 8080 | Main API service    |
| `api-chat` | 8083 | Chat-optimized API  |
| `api-dev`  | 8082 | Development API     |
| `db`       | 5432 | PostgreSQL database |
| `pgadmin`  | 8081 | Database admin      |
| `redis`    | 6379 | Cache (optional)    |

## Environment Variables

### Required (.env file)

```env
GEMINI_API_KEY=your_key_here
GOOGLE_CLIENT_ID=your_client_id_here
```

### Optional Overrides

```env
SECRET_KEY=your_secret_key
DATABASE_URL=postgresql://user:pass@host:port/db
```

## Common Commands

### Service Management

```bash
# Start specific service
docker-compose up api

# Stop specific service
docker-compose stop api

# Restart service
docker-compose restart api

# Rebuild service
docker-compose build api

# View service status
docker-compose ps
```

### Logs and Debugging

```bash
# View all logs
docker-compose logs

# Follow logs
docker-compose logs -f

# View specific service logs
docker-compose logs api

# Access service shell
docker-compose exec api bash

# Check database connection
docker-compose exec db pg_isready -U employment_user
```

### Data Management

```bash
# Backup database
docker-compose exec db pg_dump -U employment_user employment_match > backup.sql

# Restore database
docker-compose exec -T db psql -U employment_user employment_match < backup.sql

# View volumes
docker volume ls

# Clean up volumes
docker-compose down -v
```

### Health Checks

```bash
# Check API health
curl http://localhost:8080/health

# Check database health
docker-compose exec db pg_isready -U employment_user

# View health status
docker-compose ps
```

## Troubleshooting

### Port Conflicts

```bash
# Check what's using port 8080
netstat -tulpn | grep :8080

# Use different port
docker-compose up -p 8084 api
```

### Memory Issues

```bash
# Monitor resources
docker stats

# Increase memory limit
docker-compose up --scale api=1 --memory=2g
```

### Database Issues

```bash
# Reset database
docker-compose down -v
docker-compose up db

# Check database logs
docker-compose logs db
```

### Build Issues

```bash
# Clean build
docker-compose build --no-cache api

# Rebuild all services
docker-compose build --no-cache
```

## Production Commands

### Secure Deployment

```bash
# Use production environment
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Scale services
docker-compose up --scale api=3

# Update services
docker-compose pull
docker-compose up -d
```

### Monitoring

```bash
# View resource usage
docker stats

# Check service health
docker-compose ps

# View recent logs
docker-compose logs --tail=100
```

## Development Workflow

### Daily Development

```bash
# Start development environment
docker-compose --profile dev up api-dev db

# Make code changes (auto-reload)

# View logs for debugging
docker-compose logs -f api-dev

# Stop when done
docker-compose down
```

### Testing

```bash
# Run tests
docker-compose exec api-dev python -m pytest

# Run specific test
docker-compose exec api-dev python -m pytest test_chat_integration.py
```

### Database Migrations

```bash
# Run migrations
docker-compose exec api-dev alembic upgrade head

# Create new migration
docker-compose exec api-dev alembic revision --autogenerate -m "description"
```

## Configuration Files

### docker-compose.yml

- Main configuration file
- Defines all services and their relationships
- Includes health checks and optimizations

### .env

- Environment variables
- API keys and secrets
- Database configuration

### docker/Dockerfile

- Main production build
- Optimized for performance

### docker/Dockerfile.chat

- Chat-optimized build
- Enhanced ML library support
- Security hardening

## Best Practices

### Security

- Use environment variables for secrets
- Don't commit .env files
- Use non-root users in containers
- Regular security updates

### Performance

- Use appropriate resource limits
- Monitor memory and CPU usage
- Optimize image sizes
- Use health checks

### Data Management

- Regular backups
- Version control for migrations
- Monitor storage usage
- Clean up old volumes

### Development

- Use profiles for different environments
- Hot reload for development
- Separate test databases
- Consistent environment across team
