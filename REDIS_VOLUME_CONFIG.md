# Redis Volume Configuration Guide

This document describes the Redis data storage setup with volume configuration for the Rummikub backend API.

## Overview

The Rummikub backend now uses Redis as its primary data store instead of in-memory storage. This provides:
- **Data Persistence**: Game data survives container restarts
- **Improved Performance**: Redis provides optimized data structures and caching
- **Scalability**: Foundation for future horizontal scaling
- **Reliability**: Redis provides durability guarantees and crash recovery

## Docker Compose Configuration

### Redis Service
```yaml
redis:
  image: redis:7-alpine
  ports:
    - "6379:6379"
  volumes:
    - redis_data:/data
  command: redis-server --appendonly yes --dir /data
  restart: unless-stopped
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 10s
    timeout: 5s
    retries: 3
```

### Volume Configuration
```yaml
volumes:
  redis_data:
    driver: local
```

## Redis Configuration Details

### Persistence Settings
- **AOF (Append Only File)**: `--appendonly yes` ensures all write operations are logged
- **Data Directory**: `/data` is the persistence directory inside the container
- **Volume Mapping**: `redis_data:/data` maps the Docker volume to Redis data directory

### Connection Settings
The application connects to Redis using these environment variables:
- `REDIS_HOST=redis` (Docker service name)
- `REDIS_PORT=6379` (standard Redis port)
- `REDIS_DB=0` (database index)

### Health Checks
The Redis service includes health checks to ensure:
- Redis is accepting connections
- The service is ready before the API starts
- Automatic restart if Redis becomes unhealthy

## Data Storage Structure

### Keys Pattern
The Redis storage uses the following key patterns:
- `game:{game_id}` - Complete game state including players, tiles, and board
- `session:{session_id}` - Session mappings (if used by legacy code)

### Data Format
- All data is stored as JSON strings for easy serialization/deserialization
- Pydantic models are automatically converted to/from JSON
- UTF-8 encoding is used throughout

## Volume Management

### Creating the Volume
The volume is automatically created when running `docker-compose up`. To manually create:
```bash
docker volume create rummikub-backend_redis_data
```

### Volume Location
On Linux systems, the volume data is typically stored at:
```
/var/lib/docker/volumes/rummikub-backend_redis_data/_data
```

### Backup and Restore

#### Creating a Backup
```bash
# Stop the services
docker-compose down

# Create backup of volume
docker run --rm -v rummikub-backend_redis_data:/data -v $(pwd):/backup alpine tar czf /backup/redis_backup.tar.gz -C /data .

# Restart services
docker-compose up -d
```

#### Restoring from Backup
```bash
# Stop services
docker-compose down

# Remove existing volume (WARNING: This deletes all data!)
docker volume rm rummikub-backend_redis_data

# Recreate volume
docker volume create rummikub-backend_redis_data

# Restore data
docker run --rm -v rummikub-backend_redis_data:/data -v $(pwd):/backup alpine tar xzf /backup/redis_backup.tar.gz -C /data

# Restart services
docker-compose up -d
```

## Development and Testing

### Local Redis Setup
For local development without Docker:
```bash
# Install Redis
apt-get install redis-server  # Ubuntu/Debian
brew install redis            # macOS

# Start Redis
redis-server

# Set environment variables
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_DB=0
```

### Fallback Behavior
If Redis is unavailable, the application automatically falls back to an in-memory mock Redis implementation:
- **Warning logged**: "Using mock Redis storage (data will not persist)"
- **Functionality maintained**: All game operations continue to work
- **Data loss**: Game data is lost on application restart

### Testing Redis Connection
Use the Redis CLI to verify the connection:
```bash
# Connect to Redis in Docker
docker-compose exec redis redis-cli

# List all keys
KEYS *

# View a specific game
GET game:some-game-id

# Monitor Redis operations
MONITOR
```

## Production Considerations

### Performance
- Redis AOF provides durability but has some performance overhead
- For high-performance scenarios, consider RDB snapshots with AOF disabled
- Monitor Redis memory usage and configure appropriate limits

### Security
- Redis runs without authentication in the current setup
- For production, consider enabling Redis AUTH and TLS encryption
- Restrict Redis port access using Docker network policies

### Monitoring
- Monitor Redis memory usage: `docker-compose exec redis redis-cli info memory`
- Check persistence status: `docker-compose exec redis redis-cli lastsave`
- Monitor connection count: `docker-compose exec redis redis-cli info clients`

### Scaling
- Current setup uses a single Redis instance
- For high availability, consider Redis Sentinel or Redis Cluster
- For read scaling, consider Redis replicas

## Troubleshooting

### Common Issues

#### Redis Connection Failed
```
Error: Failed to connect to Redis
```
**Solution**: Check if Redis service is running and healthy
```bash
docker-compose logs redis
docker-compose exec redis redis-cli ping
```

#### Volume Mount Issues
```
Error: cannot mount volume
```
**Solution**: Check Docker daemon and volume permissions
```bash
docker volume ls
docker volume inspect rummikub-backend_redis_data
```

#### Data Corruption
```
Error: Redis data corruption detected
```
**Solution**: Stop Redis, check AOF file, and potentially restore from backup
```bash
docker-compose exec redis redis-check-aof --fix /data/appendonly.aof
```

### Maintenance Commands

#### Clear All Game Data
```bash
docker-compose exec redis redis-cli FLUSHDB
```

#### Check Database Size
```bash
docker-compose exec redis redis-cli DBSIZE
```

#### View Redis Configuration
```bash
docker-compose exec redis redis-cli CONFIG GET "*"
```

## Migration from In-Memory Storage

The migration from in-memory to Redis storage is transparent to the API users. Key changes:

1. **Data Persistence**: Games now survive server restarts
2. **Performance**: Slightly higher latency due to Redis network calls
3. **Memory Usage**: Lower API server memory usage, Redis handles data storage
4. **Concurrency**: Better handling of concurrent requests through Redis atomic operations

The application maintains full backward compatibility with existing API endpoints and data structures.