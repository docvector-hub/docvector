# Deployment Guide

## Overview

This guide covers deploying DocVector in various environments, from local development to production-ready self-hosted setups.

## Deployment Options

1. **Docker Compose** (Recommended for self-hosting)
2. **Kubernetes** (For scale and high availability)
3. **Manual Installation** (For development)
4. **Cloud Platforms** (AWS, GCP, Azure)

## Prerequisites

### Minimum Requirements

- **CPU**: 2+ cores
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 20GB+ (depends on document volume)
- **OS**: Linux (Ubuntu 22.04+, Debian 11+), macOS, Windows (WSL2)

### Recommended Requirements

- **CPU**: 4+ cores
- **RAM**: 16GB (for better embedding performance)
- **Storage**: SSD with 50GB+
- **Network**: Stable internet connection for initial model downloads

### Software Requirements

- Docker 24.0+
- Docker Compose 2.20+
- (Optional) Kubernetes 1.28+
- (Optional) Python 3.11+ for local development

## Quick Start: Docker Compose

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/docvector.git
cd docvector
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:

```bash
# PostgreSQL
POSTGRES_USER=docvector
POSTGRES_PASSWORD=your-secure-password
POSTGRES_DB=docvector

# Redis
REDIS_PASSWORD=your-redis-password

# API
API_SECRET_KEY=your-secret-key-min-32-chars
API_HOST=0.0.0.0
API_PORT=8000

# Embedding Model
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Optional: OpenAI (if using OpenAI embeddings)
# OPENAI_API_KEY=sk-...
```

### 3. Start Services

```bash
docker-compose up -d
```

This starts:
- **API Server** (port 8000)
- **Celery Worker** (background jobs)
- **PostgreSQL** (port 5432)
- **Qdrant** (port 6333)
- **Redis** (port 6379)

### 4. Verify Deployment

```bash
# Check services
docker-compose ps

# Check API health
curl http://localhost:8000/api/v1/health

# View logs
docker-compose logs -f api
```

### 5. Access Services

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Qdrant UI**: http://localhost:6333/dashboard

## Docker Compose Configuration

### `docker-compose.yml`

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  qdrant:
    image: qdrant/qdrant:latest
    volumes:
      - qdrant_data:/qdrant/storage
    ports:
      - "6333:6333"
      - "6334:6334"  # gRPC
    environment:
      - QDRANT__SERVICE__HTTP_PORT=6333
      - QDRANT__SERVICE__GRPC_PORT=6334

  api:
    build:
      context: .
      dockerfile: deployment/docker/Dockerfile
    command: uvicorn docvector.api.main:app --host 0.0.0.0 --port 8000
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      qdrant:
        condition: service_started
    volumes:
      - ./config:/app/config:ro
      - uploads:/app/uploads
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  worker:
    build:
      context: .
      dockerfile: deployment/docker/Dockerfile.worker
    command: celery -A docvector.tasks.celery_app worker --loglevel=info
    env_file:
      - .env
    depends_on:
      - postgres
      - redis
      - qdrant
    volumes:
      - ./config:/app/config:ro
      - uploads:/app/uploads

  # Optional: Flower (Celery monitoring)
  flower:
    build:
      context: .
      dockerfile: deployment/docker/Dockerfile.worker
    command: celery -A docvector.tasks.celery_app flower
    ports:
      - "5555:5555"
    env_file:
      - .env
    depends_on:
      - redis
      - worker

volumes:
  postgres_data:
  redis_data:
  qdrant_data:
  uploads:
```

### `deployment/docker/Dockerfile`

```dockerfile
# Multi-stage build for smaller image

# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies (no dev dependencies)
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY src/ ./src/
COPY config/ ./config/
COPY alembic.ini ./

# Create non-root user
RUN useradd -m -u 1000 docvector && chown -R docvector:docvector /app
USER docvector

# Download embedding model at build time (optional, reduces startup time)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

EXPOSE 8000

CMD ["uvicorn", "docvector.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### `deployment/docker/Dockerfile.worker`

```dockerfile
FROM python:3.11-slim

# Same as main Dockerfile but with worker command
# ... (similar to above)

CMD ["celery", "-A", "docvector.tasks.celery_app", "worker", "--loglevel=info"]
```

## Production Deployment

### Production Compose Configuration

`docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./deployment/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./deployment/nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - api

  api:
    # ... (extend base config)
    restart: always
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '2'
          memory: 4G
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  worker:
    # ... (extend base config)
    restart: always
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 4G

  postgres:
    # ... (extend base config)
    restart: always
    volumes:
      - /data/postgres:/var/lib/postgresql/data  # Host path for persistence

  qdrant:
    # ... (extend base config)
    restart: always
    volumes:
      - /data/qdrant:/qdrant/storage

  # Monitoring
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./deployment/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    volumes:
      - grafana_data:/var/lib/grafana
      - ./deployment/grafana/dashboards:/etc/grafana/provisioning/dashboards
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}

volumes:
  prometheus_data:
  grafana_data:
```

### Nginx Configuration

`deployment/nginx/nginx.conf`:

```nginx
upstream api_backend {
    least_conn;
    server api:8000 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name docvector.example.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name docvector.example.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Request limits
    client_max_body_size 100M;

    # Logging
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    location /api {
        proxy_pass http://api_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /docs {
        proxy_pass http://api_backend;
        proxy_set_header Host $host;
    }

    location /ws {
        proxy_pass http://api_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster 1.28+
- kubectl configured
- Helm 3.0+ (optional)

### Kubernetes Manifests

`deployment/k8s/namespace.yaml`:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: docvector
```

`deployment/k8s/configmap.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: docvector-config
  namespace: docvector
data:
  config.yaml: |
    # DocVector configuration
    # ... (your config here)
```

`deployment/k8s/secrets.yaml`:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: docvector-secrets
  namespace: docvector
type: Opaque
stringData:
  POSTGRES_PASSWORD: "your-password"
  REDIS_PASSWORD: "your-password"
  API_SECRET_KEY: "your-secret-key"
```

`deployment/k8s/api-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: docvector-api
  namespace: docvector
spec:
  replicas: 3
  selector:
    matchLabels:
      app: docvector-api
  template:
    metadata:
      labels:
        app: docvector-api
    spec:
      containers:
      - name: api
        image: docvector/api:latest
        ports:
        - containerPort: 8000
        env:
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: docvector-secrets
              key: POSTGRES_PASSWORD
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
        livenessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: docvector-api
  namespace: docvector
spec:
  selector:
    app: docvector-api
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```

`deployment/k8s/worker-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: docvector-worker
  namespace: docvector
spec:
  replicas: 3
  selector:
    matchLabels:
      app: docvector-worker
  template:
    metadata:
      labels:
        app: docvector-worker
    spec:
      containers:
      - name: worker
        image: docvector/worker:latest
        env:
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: docvector-secrets
              key: POSTGRES_PASSWORD
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
```

`deployment/k8s/ingress.yaml`:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: docvector-ingress
  namespace: docvector
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - docvector.example.com
    secretName: docvector-tls
  rules:
  - host: docvector.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: docvector-api
            port:
              number: 80
```

### Deploy to Kubernetes

```bash
# Create namespace
kubectl apply -f deployment/k8s/namespace.yaml

# Create secrets (edit first!)
kubectl apply -f deployment/k8s/secrets.yaml

# Deploy services
kubectl apply -f deployment/k8s/postgres.yaml
kubectl apply -f deployment/k8s/redis.yaml
kubectl apply -f deployment/k8s/qdrant.yaml

# Deploy application
kubectl apply -f deployment/k8s/api-deployment.yaml
kubectl apply -f deployment/k8s/worker-deployment.yaml

# Create ingress
kubectl apply -f deployment/k8s/ingress.yaml

# Check status
kubectl get pods -n docvector
kubectl logs -f deployment/docvector-api -n docvector
```

## Database Migrations

### Initial Setup

```bash
# In Docker container
docker-compose exec api alembic upgrade head

# Or locally
poetry run alembic upgrade head
```

### Create Migration

```bash
# Auto-generate from model changes
docker-compose exec api alembic revision --autogenerate -m "Add new field"

# Manual migration
docker-compose exec api alembic revision -m "Custom migration"
```

## Backup and Restore

### PostgreSQL Backup

```bash
# Backup
docker-compose exec postgres pg_dump -U docvector docvector > backup.sql

# Restore
docker-compose exec -T postgres psql -U docvector docvector < backup.sql
```

### Qdrant Backup

```bash
# Create snapshot via API
curl -X POST http://localhost:6333/collections/documents/snapshots

# Download snapshot
curl http://localhost:6333/collections/documents/snapshots/snapshot_name -o snapshot.tar
```

### Automated Backups

```bash
# Cron job (daily at 2 AM)
0 2 * * * /path/to/backup-script.sh
```

`backup-script.sh`:

```bash
#!/bin/bash
DATE=$(date +%Y%m%d)
BACKUP_DIR=/backups

# PostgreSQL backup
docker-compose exec -T postgres pg_dump -U docvector docvector | gzip > $BACKUP_DIR/postgres_$DATE.sql.gz

# Qdrant snapshot
curl -X POST http://localhost:6333/collections/documents/snapshots

# Keep last 7 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete
```

## Monitoring

### Health Checks

```bash
# API health
curl http://localhost:8000/api/v1/health

# Qdrant health
curl http://localhost:6333/cluster

# PostgreSQL health
docker-compose exec postgres pg_isready
```

### Logs

```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f api

# View last 100 lines
docker-compose logs --tail=100 api
```

### Metrics (Prometheus)

Add to `api/main.py`:

```python
from prometheus_client import make_asgi_app

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
```

## Scaling

### Horizontal Scaling

```bash
# Scale API servers
docker-compose up -d --scale api=3

# Scale workers
docker-compose up -d --scale worker=5
```

### Vertical Scaling

Edit `docker-compose.yml`:

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
```

## Troubleshooting

### Common Issues

**Issue: API not starting**
```bash
# Check logs
docker-compose logs api

# Check dependencies
docker-compose ps

# Restart services
docker-compose restart
```

**Issue: Out of memory**
```bash
# Check memory usage
docker stats

# Increase memory limits in docker-compose.yml
# Or increase Docker Desktop memory allocation
```

**Issue: Slow embeddings**
```bash
# Use GPU acceleration (if available)
# Edit Dockerfile to install torch with CUDA support

# Or switch to smaller model
# In .env: EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

## Security Checklist

- [ ] Change default passwords
- [ ] Use strong API secret key
- [ ] Enable SSL/TLS in production
- [ ] Configure firewall rules
- [ ] Use secrets management (Vault, AWS Secrets Manager)
- [ ] Enable authentication
- [ ] Configure rate limiting
- [ ] Regular security updates
- [ ] Backup sensitive data
- [ ] Monitor access logs

## Performance Tuning

### PostgreSQL

```sql
-- Increase connection pool
ALTER SYSTEM SET max_connections = 200;

-- Increase shared buffers
ALTER SYSTEM SET shared_buffers = '2GB';

-- Enable query optimization
ALTER SYSTEM SET random_page_cost = 1.1;
```

### Qdrant

```yaml
# config.yaml
service:
  max_request_size_mb: 100

storage:
  # Use mmap for larger datasets
  on_disk_payload: true
```

### Redis

```conf
# redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
```

## Summary

This deployment guide covers:
1. **Quick Start**: Get running in minutes with Docker Compose
2. **Production Setup**: Nginx, SSL, monitoring
3. **Kubernetes**: Scalable cloud deployment
4. **Backup/Restore**: Data protection strategies
5. **Monitoring**: Health checks and metrics
6. **Scaling**: Horizontal and vertical scaling
7. **Security**: Best practices and checklist

For most self-hosting use cases, **Docker Compose** is recommended. For enterprise scale, use **Kubernetes**.
