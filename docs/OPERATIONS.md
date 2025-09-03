# SprintConnect Operations Guide

## Overview

This document provides comprehensive guidance for deploying, monitoring, maintaining, and operating SprintConnect in production environments. It covers infrastructure setup, deployment procedures, monitoring strategies, backup and recovery, and day-to-day operational tasks.

## SprintConnect Operational Components

- Frontend/UI: CDN, versioned static assets, CSP enforcement
- API Service: FastAPI deployments, HPA, readiness/liveness, canaries
- AuthGateway: JWKS cache warmers, key rotation schedules, PAR/JAR endpoints
- PDP: Policy bundles per tenant, version rollout/rollback
- Workers: Discovery/Health queues, outbox relay, DLQs, retriers
- Egress Proxy: Policy config, allowlist updates, DNS pinning checks
- Data Stores: PostgreSQL, Redis, Vault; backup, PITR, retention
- Observability: Prometheus/Alertmanager, Jaeger/OTEL, centralized logs
- CI/CD: Build, scan, SBOM, provenance, staged deploy, rollback

## Infrastructure Requirements

### Compute Resources

#### Production Environment
```yaml
# Minimum Production Requirements
compute:
  api_service:
    instances: 3
    cpu: 4 cores
    memory: 8 GB
    storage: 50 GB SSD
    
  websocket_gateway:
    instances: 2  
    cpu: 2 cores
    memory: 4 GB
    storage: 20 GB SSD
    
  worker_service:
    instances: 4
    cpu: 8 cores
    memory: 16 GB
    storage: 100 GB SSD
    
  database:
    instance_type: "db.r6i.2xlarge"
    cpu: 8 vCPUs
    memory: 64 GB
    storage: 1 TB SSD (gp3)
    iops: 3000
    backup_retention: 30 days
    
  redis:
    instance_type: "cache.r6g.xlarge"
    cpu: 4 vCPUs
    memory: 32 GB
    cluster_mode: enabled
    
  load_balancer:
    type: "Application Load Balancer"
    instances: 2
    zones: 3
```

#### Staging Environment
```yaml
# Staging Environment (Production-like but smaller)
staging:
  api_service:
    instances: 2
    cpu: 2 cores
    memory: 4 GB
    
  websocket_gateway:
    instances: 1
    cpu: 2 cores
    memory: 4 GB
    
  worker_service:
    instances: 2
    cpu: 4 cores
    memory: 8 GB
    
  database:
    instance_type: "db.r6i.large"
    cpu: 2 vCPUs
    memory: 16 GB
    storage: 200 GB SSD
```

### Network Architecture

#### VPC Configuration
```yaml
# AWS VPC Setup Example
vpc:
  cidr_block: "10.0.0.0/16"
  
  subnets:
    public:
      - cidr: "10.0.1.0/24"
        az: "us-east-1a"
      - cidr: "10.0.2.0/24"
        az: "us-east-1b"
      - cidr: "10.0.3.0/24"
        az: "us-east-1c"
        
    private:
      - cidr: "10.0.4.0/24"
        az: "us-east-1a"
      - cidr: "10.0.5.0/24"
        az: "us-east-1b"
      - cidr: "10.0.6.0/24"
        az: "us-east-1c"
        
    database:
      - cidr: "10.0.7.0/24"
        az: "us-east-1a"
      - cidr: "10.0.8.0/24"
        az: "us-east-1b"
      - cidr: "10.0.9.0/24"
        az: "us-east-1c"
  
  nat_gateways: 3  # One per AZ for HA
  internet_gateway: true
  
  security_groups:
    alb:
      ingress:
        - port: 443
          source: "0.0.0.0/0"
        - port: 80
          source: "0.0.0.0/0"
    
    api:
      ingress:
        - port: 8000
          source: "sg-alb"
        - port: 9090
          source: "sg-monitoring"
    
    database:
      ingress:
        - port: 5432
          source: "sg-api"
        - port: 6379
          source: "sg-api"
```

## Deployment Architecture

### Container Orchestration

#### Kubernetes Deployment
```yaml
# Kubernetes namespace configuration
apiVersion: v1
kind: Namespace
metadata:
  name: sprintconnect
  labels:
    name: sprintconnect
    environment: production

---
# API Service Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sprintconnect-api
  namespace: sprintconnect
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: sprintconnect-api
  template:
    metadata:
      labels:
        app: sprintconnect-api
    spec:
      serviceAccountName: sprintconnect-api
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: api
        image: sprintconnect/api:v1.2.3
        ports:
        - containerPort: 8000
          name: http
        - containerPort: 9090
          name: metrics
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: sprintconnect-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: sprintconnect-secrets
              key: redis-url
        - name: VAULT_TOKEN
          valueFrom:
            secretKeyRef:
              name: sprintconnect-secrets
              key: vault-token
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 2000m
            memory: 4Gi
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: config
          mountPath: /app/config
          readOnly: true
      volumes:
      - name: config
        configMap:
          name: sprintconnect-config

---
# Horizontal Pod Autoscaler
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: sprintconnect-api-hpa
  namespace: sprintconnect
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: sprintconnect-api
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
```

#### Service Configuration
```yaml
# Load Balancer Service
apiVersion: v1
kind: Service
metadata:
  name: sprintconnect-api-service
  namespace: sprintconnect
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
    service.beta.kubernetes.io/aws-load-balancer-ssl-cert: "arn:aws:acm:..."
    service.beta.kubernetes.io/aws-load-balancer-ssl-ports: "https"
spec:
  type: LoadBalancer
  ports:
  - port: 443
    targetPort: 8000
    protocol: TCP
    name: https
  - port: 80
    targetPort: 8000
    protocol: TCP
    name: http
  selector:
    app: sprintconnect-api

---
# Internal Service for monitoring
apiVersion: v1
kind: Service
metadata:
  name: sprintconnect-api-internal
  namespace: sprintconnect
spec:
  type: ClusterIP
  ports:
  - port: 8000
    targetPort: 8000
    name: api
  - port: 9090
    targetPort: 9090
    name: metrics
  selector:
    app: sprintconnect-api
```

### Helm Charts

#### Values Configuration
```yaml
# values.yaml for Helm deployment
global:
  environment: production
  region: us-east-1
  domain: sprintconnect.com
  
image:
  repository: sprintconnect
  tag: v1.2.3
  pullPolicy: IfNotPresent

api:
  replicaCount: 3
  resources:
    requests:
      cpu: 500m
      memory: 1Gi
    limits:
      cpu: 2000m
      memory: 4Gi
  
  autoscaling:
    enabled: true
    minReplicas: 3
    maxReplicas: 20
    targetCPUUtilizationPercentage: 70
    targetMemoryUtilizationPercentage: 80

workers:
  discovery:
    replicaCount: 2
    resources:
      requests:
        cpu: 1000m
        memory: 2Gi
      limits:
        cpu: 4000m
        memory: 8Gi
  
  chat:
    replicaCount: 2
    resources:
      requests:
        cpu: 1000m
        memory: 2Gi
      limits:
        cpu: 4000m
        memory: 8Gi

database:
  enabled: false  # Use external RDS
  host: sprintconnect-prod.cluster-xxx.us-east-1.rds.amazonaws.com
  port: 5432
  name: sprintconnect
  
redis:
  enabled: false  # Use external ElastiCache
  host: sprintconnect-prod.xxx.cache.amazonaws.com
  port: 6379

secrets:
  vault:
    enabled: true
    address: https://vault.sprintconnect.com
    role: sprintconnect-prod
    
monitoring:
  prometheus:
    enabled: true
    serviceMonitor: true
  
  jaeger:
    enabled: true
    endpoint: http://jaeger-collector:14268/api/traces

ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
  hosts:
  - host: api.sprintconnect.com
    paths:
    - path: /
      pathType: Prefix
  tls:
  - secretName: sprintconnect-api-tls
    hosts:
    - api.sprintconnect.com
```

### CI/CD Pipeline

#### GitHub Actions Workflow
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]
    tags: ['v*']

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: sprintconnect

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:6
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install Poetry
      uses: snok/install-poetry@v1
    
    - name: Install dependencies
      run: |
        cd backend
        poetry install --with dev,test
    
    - name: Run tests
      run: |
        cd backend
        poetry run pytest tests/ -v --cov=app --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./backend/coverage.xml

  security-scan:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        scan-type: 'fs'
        scan-ref: '.'
        format: 'sarif'
        output: 'trivy-results.sarif'
    
    - name: Upload Trivy scan results to GitHub Security tab
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: 'trivy-results.sarif'

  build-and-push:
    needs: [test, security-scan]
    runs-on: ubuntu-latest
    outputs:
      image-tag: ${{ steps.meta.outputs.tags }}
      image-digest: ${{ steps.build.outputs.digest }}
    
    steps:
    - name: Checkout
      uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Log in to Container Registry
      uses: docker/login-action@v2
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v4
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=semver,pattern={{version}}
          type=semver,pattern={{major}}.{{minor}}
          type=sha,prefix={{branch}}-
    
    - name: Build and push Docker image
      id: build
      uses: docker/build-push-action@v4
      with:
        context: .
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
        provenance: true
        sbom: true

  deploy-staging:
    needs: build-and-push
    runs-on: ubuntu-latest
    environment: staging
    steps:
    - name: Deploy to Staging
      run: |
        # Deploy to staging environment
        helm upgrade --install sprintconnect-staging ./helm/sprintconnect \
          --namespace sprintconnect-staging \
          --create-namespace \
          --set image.tag=${{ needs.build-and-push.outputs.image-tag }} \
          --set global.environment=staging \
          --values ./helm/values-staging.yaml

  deploy-production:
    needs: [build-and-push, deploy-staging]
    runs-on: ubuntu-latest
    environment: production
    if: startsWith(github.ref, 'refs/tags/v')
    steps:
    - name: Deploy to Production
      run: |
        # Deploy to production environment
        helm upgrade --install sprintconnect ./helm/sprintconnect \
          --namespace sprintconnect \
          --create-namespace \
          --set image.tag=${{ needs.build-and-push.outputs.image-tag }} \
          --set global.environment=production \
          --values ./helm/values-production.yaml \
          --wait --timeout 600s
```

## Monitoring and Observability

### Prometheus Monitoring

#### Metrics Configuration
```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "sprintconnect_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'sprintconnect-api'
    static_configs:
      - targets: ['sprintconnect-api:9090']
    metrics_path: /metrics
    scrape_interval: 15s
    
  - job_name: 'sprintconnect-workers'
    static_configs:
      - targets: ['sprintconnect-workers:9090']
    metrics_path: /metrics
    scrape_interval: 30s
    
  - job_name: 'postgres-exporter'
    static_configs:
      - targets: ['postgres-exporter:9187']
    
  - job_name: 'redis-exporter'
    static_configs:
      - targets: ['redis-exporter:9121']
```

#### Alerting Rules
```yaml
# sprintconnect_rules.yml
groups:
- name: sprintconnect.rules
  rules:
  # API Service Alerts
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.01
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "High error rate detected"
      description: "Error rate is {{ $value }} errors per second"
  
  - alert: HighLatency
    expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.5
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High API latency"
      description: "95th percentile latency is {{ $value }} seconds"
  
  - alert: DatabaseConnectionExhaustion
    expr: pg_stat_activity_count / pg_settings_max_connections > 0.8
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Database connection pool nearly exhausted"
      description: "{{ $value }}% of database connections in use"
  
  # Worker Service Alerts
  - alert: HighQueueDepth
    expr: celery_queue_depth > 1000
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High worker queue depth"
      description: "Queue depth is {{ $value }} tasks"
  
  - alert: WorkerFailureRate
    expr: rate(celery_task_failed_total[5m]) / rate(celery_task_total[5m]) > 0.1
    for: 3m
    labels:
      severity: warning
    annotations:
      summary: "High worker task failure rate"
      description: "{{ $value }}% of tasks are failing"
  
  # MCP Server Health
  - alert: MCPServerDown
    expr: mcp_server_health_status == 0
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "MCP server is unhealthy"
      description: "Server {{ $labels.server_id }} ({{ $labels.server_name }}) is down"
  
  # Chat Service Alerts
  - alert: HighWebSocketDisconnectRate
    expr: rate(websocket_disconnections_total[5m]) > 0.1
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "High WebSocket disconnect rate"
      description: "{{ $value }} disconnections per second"
  
  # Resource Alerts
  - alert: HighCPUUsage
    expr: rate(process_cpu_seconds_total[5m]) * 100 > 80
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "High CPU usage"
      description: "CPU usage is {{ $value }}%"
  
  - alert: HighMemoryUsage
    expr: process_resident_memory_bytes / (1024^3) > 6
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High memory usage"
      description: "Memory usage is {{ $value }}GB"
```

### Grafana Dashboards

#### System Overview Dashboard
```json
{
  "dashboard": {
    "id": null,
    "title": "SprintConnect - System Overview",
    "tags": ["sprintconnect"],
    "timezone": "UTC",
    "panels": [
      {
        "id": 1,
        "title": "Request Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total[5m]))",
            "legendFormat": "Requests/sec"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "reqps"
          }
        }
      },
      {
        "id": 2,
        "title": "Error Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{status=~\"5..\"}[5m])) / sum(rate(http_requests_total[5m]))",
            "legendFormat": "Error Rate"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percentunit",
            "max": 1,
            "thresholds": {
              "steps": [
                {"color": "green", "value": 0},
                {"color": "yellow", "value": 0.01},
                {"color": "red", "value": 0.05}
              ]
            }
          }
        }
      },
      {
        "id": 3,
        "title": "Response Time (95th percentile)",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "50th percentile"
          }
        ]
      },
      {
        "id": 4,
        "title": "Active Chat Sessions",
        "type": "stat",
        "targets": [
          {
            "expr": "active_chat_sessions",
            "legendFormat": "Active Sessions"
          }
        ]
      }
    ]
  }
}
```

### Distributed Tracing

#### Jaeger Configuration
```yaml
# jaeger-deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jaeger
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: jaeger
  template:
    metadata:
      labels:
        app: jaeger
    spec:
      containers:
      - name: jaeger
        image: jaegertracing/all-in-one:1.45
        ports:
        - containerPort: 16686
          name: ui
        - containerPort: 14268
          name: collector
        env:
        - name: COLLECTOR_ZIPKIN_HOST_PORT
          value: ":9411"
        - name: SPAN_STORAGE_TYPE
          value: "elasticsearch"
        - name: ES_SERVER_URLS
          value: "http://elasticsearch:9200"
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 1Gi
```

### Log Aggregation

#### ELK Stack Configuration
```yaml
# elasticsearch.yml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: elasticsearch
  namespace: logging
spec:
  serviceName: elasticsearch
  replicas: 3
  selector:
    matchLabels:
      app: elasticsearch
  template:
    metadata:
      labels:
        app: elasticsearch
    spec:
      containers:
      - name: elasticsearch
        image: docker.elastic.co/elasticsearch/elasticsearch:8.8.0
        ports:
        - containerPort: 9200
          name: rest
        - containerPort: 9300
          name: inter-node
        env:
        - name: cluster.name
          value: sprintconnect-logs
        - name: node.name
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: discovery.seed_hosts
          value: "elasticsearch-0.elasticsearch,elasticsearch-1.elasticsearch,elasticsearch-2.elasticsearch"
        - name: cluster.initial_master_nodes
          value: "elasticsearch-0,elasticsearch-1,elasticsearch-2"
        - name: ES_JAVA_OPTS
          value: "-Xms2g -Xmx2g"
        volumeMounts:
        - name: data
          mountPath: /usr/share/elasticsearch/data
        resources:
          requests:
            cpu: 1000m
            memory: 4Gi
          limits:
            cpu: 2000m
            memory: 4Gi
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 100Gi
```

## Backup and Recovery

### Database Backup Strategy

#### Automated Backup Script
```bash
#!/bin/bash
# backup-database.sh

set -euo pipefail

# Configuration
BACKUP_DIR="/backups/postgres"
RETENTION_DAYS=30
S3_BUCKET="sprintconnect-backups"
DATABASE_URL="${DATABASE_URL}"

# Create backup directory
mkdir -p "${BACKUP_DIR}"

# Generate backup filename
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/sprintconnect_${TIMESTAMP}.sql.gz"

echo "Starting database backup..."

# Create compressed backup
pg_dump "${DATABASE_URL}" | gzip > "${BACKUP_FILE}"

# Verify backup integrity
if ! gunzip -t "${BACKUP_FILE}"; then
    echo "ERROR: Backup file is corrupted"
    exit 1
fi

echo "Backup created: ${BACKUP_FILE}"

# Upload to S3
aws s3 cp "${BACKUP_FILE}" "s3://${S3_BUCKET}/postgres/"

# Cleanup old local backups
find "${BACKUP_DIR}" -name "*.sql.gz" -mtime +${RETENTION_DAYS} -delete

echo "Database backup completed successfully"
```

#### Point-in-Time Recovery Setup
```yaml
# PostgreSQL configuration for PITR
postgresql_config:
  wal_level: replica
  archive_mode: on
  archive_command: 'aws s3 cp %p s3://sprintconnect-wal-archive/%f'
  max_wal_senders: 3
  wal_keep_segments: 64
  checkpoint_completion_target: 0.9
  
  # Backup configuration
  backup:
    base_backup_schedule: "0 2 * * *"  # Daily at 2 AM
    wal_archive_retention: "7 days"
    full_backup_retention: "30 days"
```

### Object Storage Backup
```bash
#!/bin/bash
# backup-object-storage.sh

set -euo pipefail

SOURCE_BUCKET="sprintconnect-data"
BACKUP_BUCKET="sprintconnect-backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "Starting object storage backup..."

# Sync to backup bucket with versioning
aws s3 sync "s3://${SOURCE_BUCKET}/" "s3://${BACKUP_BUCKET}/object-storage/${TIMESTAMP}/" \
    --storage-class STANDARD_IA

# Create manifest of backed up files
aws s3 ls "s3://${BACKUP_BUCKET}/object-storage/${TIMESTAMP}/" --recursive > \
    "/tmp/backup_manifest_${TIMESTAMP}.txt"

aws s3 cp "/tmp/backup_manifest_${TIMESTAMP}.txt" \
    "s3://${BACKUP_BUCKET}/manifests/"

echo "Object storage backup completed"
```

### Disaster Recovery Procedures

#### Recovery Runbook
```markdown
# Disaster Recovery Runbook

## Database Recovery

### Full Database Restore
1. Stop application services
2. Create new database instance
3. Restore from latest backup:
   ```bash
   # Download backup
   aws s3 cp s3://sprintconnect-backups/postgres/latest.sql.gz ./
   
   # Restore database
   gunzip -c latest.sql.gz | psql $NEW_DATABASE_URL
   ```
4. Update application configuration
5. Start services and verify

### Point-in-Time Recovery
1. Identify target recovery time
2. Restore base backup:
   ```bash
   # Restore base backup
   pg_basebackup -D /var/lib/postgresql/data -Ft -z -P -h $DB_HOST
   ```
3. Apply WAL files up to target time:
   ```bash
   # Configure recovery
   echo "restore_command = 'aws s3 cp s3://wal-archive/%f %p'" > recovery.conf
   echo "recovery_target_time = '2024-01-15 10:30:00'" >> recovery.conf
   ```
4. Start PostgreSQL and verify recovery

## Application Recovery

### Rolling Back Deployment
1. Identify last known good version
2. Roll back using Helm:
   ```bash
   helm rollback sprintconnect --namespace sprintconnect
   ```
3. Verify application health
4. Monitor for issues

### Scaling Up During Incident
1. Increase replica count:
   ```bash
   kubectl scale deployment sprintconnect-api --replicas=10
   ```
2. Monitor resource usage
3. Scale back after incident resolution
```

## Security Operations

### Certificate Management

#### Automated Certificate Renewal
```yaml
# cert-manager ClusterIssuer
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: ops@sprintconnect.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
    - dns01:
        route53:
          region: us-east-1
          accessKeyID: AKIAIOSFODNN7EXAMPLE
          secretAccessKeySecretRef:
            name: route53-credentials
            key: secret-access-key

---
# Certificate resource
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: sprintconnect-tls
  namespace: sprintconnect
spec:
  secretName: sprintconnect-tls
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
  - api.sprintconnect.com
  - app.sprintconnect.com
  - "*.sprintconnect.com"
```

#### Certificate Monitoring
```bash
#!/bin/bash
# check-certificates.sh

set -euo pipefail

DOMAINS=(
    "api.sprintconnect.com"
    "app.sprintconnect.com"
    "vault.sprintconnect.com"
)

WARNING_DAYS=30
CRITICAL_DAYS=7

for domain in "${DOMAINS[@]}"; do
    echo "Checking certificate for ${domain}..."
    
    # Get certificate expiration date
    expiry=$(openssl s_client -servername "${domain}" -connect "${domain}:443" < /dev/null 2>/dev/null | \
             openssl x509 -noout -dates | grep notAfter | cut -d= -f2)
    
    # Convert to epoch time
    expiry_epoch=$(date -d "${expiry}" +%s)
    current_epoch=$(date +%s)
    days_until_expiry=$(( (expiry_epoch - current_epoch) / 86400 ))
    
    echo "Certificate for ${domain} expires in ${days_until_expiry} days"
    
    if [ "${days_until_expiry}" -le "${CRITICAL_DAYS}" ]; then
        echo "CRITICAL: Certificate for ${domain} expires in ${days_until_expiry} days!"
        # Send alert
        curl -X POST "${SLACK_WEBHOOK_URL}" \
             -H 'Content-type: application/json' \
             --data "{\"text\":\"🚨 CRITICAL: Certificate for ${domain} expires in ${days_until_expiry} days!\"}"
    elif [ "${days_until_expiry}" -le "${WARNING_DAYS}" ]; then
        echo "WARNING: Certificate for ${domain} expires in ${days_until_expiry} days"
        # Send warning
        curl -X POST "${SLACK_WEBHOOK_URL}" \
             -H 'Content-type: application/json' \
             --data "{\"text\":\"⚠️ WARNING: Certificate for ${domain} expires in ${days_until_expiry} days\"}"
    fi
done
```

### Secret Rotation

#### Vault Secret Rotation
```bash
#!/bin/bash
# rotate-secrets.sh

set -euo pipefail

# Configuration
VAULT_ADDR="${VAULT_ADDR}"
VAULT_TOKEN="${VAULT_TOKEN}"

# Rotate database password
echo "Rotating database password..."
NEW_DB_PASSWORD=$(openssl rand -base64 32)

# Update password in database
psql "${DATABASE_URL}" -c "ALTER USER sprintconnect PASSWORD '${NEW_DB_PASSWORD}';"

# Store new password in Vault
vault kv put secret/sprintconnect/database password="${NEW_DB_PASSWORD}"

# Restart application pods to pick up new secret
kubectl rollout restart deployment/sprintconnect-api -n sprintconnect

echo "Database password rotation completed"

# Rotate API keys (example for external service)
echo "Rotating external API keys..."

# Generate new API key (implementation depends on service)
NEW_API_KEY=$(curl -X POST https://api.external-service.com/keys \
              -H "Authorization: Bearer ${CURRENT_API_KEY}" \
              -H "Content-Type: application/json" \
              -d '{"name":"sprintconnect-prod-rotation"}' | jq -r '.api_key')

# Store in Vault
vault kv put secret/sprintconnect/external-api api_key="${NEW_API_KEY}"

# Test new key
if curl -f -H "Authorization: Bearer ${NEW_API_KEY}" \
        https://api.external-service.com/health; then
    echo "New API key validated successfully"
    
    # Revoke old key
    curl -X DELETE https://api.external-service.com/keys/${OLD_KEY_ID} \
         -H "Authorization: Bearer ${CURRENT_API_KEY}"
    
    # Restart services
    kubectl rollout restart deployment/sprintconnect-workers -n sprintconnect
else
    echo "ERROR: New API key validation failed"
    exit 1
fi

echo "Secret rotation completed successfully"
```

## Performance Optimization

### Database Optimization

#### Query Performance Monitoring
```sql
-- Monitor slow queries
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    rows,
    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
FROM pg_stat_statements 
WHERE mean_time > 100  -- queries taking more than 100ms on average
ORDER BY mean_time DESC 
LIMIT 20;

-- Monitor table sizes and bloat
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    pg_stat_user_tables.n_tup_ins,
    pg_stat_user_tables.n_tup_upd,
    pg_stat_user_tables.n_tup_del
FROM pg_tables
LEFT JOIN pg_stat_user_tables ON pg_tables.tablename = pg_stat_user_tables.relname
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

#### Index Optimization
```sql
-- Find missing indexes
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats
WHERE schemaname = 'public'
AND n_distinct > 100
AND correlation < 0.1;

-- Monitor index usage
SELECT 
    indexrelname,
    idx_tup_read,
    idx_tup_fetch,
    idx_scan,
    idx_tup_read / GREATEST(idx_scan, 1) AS avg_tuples_per_scan
FROM pg_stat_user_indexes
WHERE idx_scan > 0
ORDER BY idx_scan DESC;
```

### Application Performance

#### Cache Optimization
```python
# Redis cache optimization configuration
REDIS_CONFIG = {
    # Memory optimization
    'maxmemory-policy': 'allkeys-lru',
    'maxmemory': '2gb',
    
    # Persistence settings
    'save': '900 1 300 10 60 10000',  # RDB snapshots
    'appendonly': 'yes',              # AOF logging
    'appendfsync': 'everysec',        # AOF sync frequency
    
    # Network optimization
    'tcp-keepalive': '300',
    'timeout': '300',
    
    # Memory usage optimization
    'hash-max-ziplist-entries': '512',
    'hash-max-ziplist-value': '64',
    'list-max-ziplist-size': '-2',
    'set-max-intset-entries': '512',
    'zset-max-ziplist-entries': '128',
    'zset-max-ziplist-value': '64'
}

# Cache warming script
async def warm_cache():
    """Pre-populate cache with frequently accessed data"""
    
    # Warm server list cache
    servers = await db.query(McpServer).filter(
        McpServer.status == "active"
    ).all()
    
    for server in servers:
        cache_key = f"server:{server.id}"
        await redis.set(cache_key, server.json(), ex=3600)
    
    # Warm capability cache
    capabilities = await db.query(McpCapability).filter(
        McpCapability.enabled == True
    ).all()
    
    capability_map = {}
    for cap in capabilities:
        if cap.server_id not in capability_map:
            capability_map[cap.server_id] = []
        capability_map[cap.server_id].append(cap.dict())
    
    for server_id, caps in capability_map.items():
        cache_key = f"capabilities:{server_id}"
        await redis.set(cache_key, json.dumps(caps), ex=3600)
```

## Capacity Planning

### Resource Monitoring
```bash
#!/bin/bash
# capacity-report.sh

set -euo pipefail

echo "=== SprintConnect Capacity Report ==="
echo "Generated: $(date)"
echo

# CPU usage across all pods
echo "=== CPU Usage ==="
kubectl top pods -n sprintconnect --sort-by=cpu | head -20

echo
echo "=== Memory Usage ==="
kubectl top pods -n sprintconnect --sort-by=memory | head -20

echo
echo "=== Node Resource Usage ==="
kubectl top nodes

echo
echo "=== Database Metrics ==="
psql $DATABASE_URL -c "
SELECT 
    datname,
    pg_size_pretty(pg_database_size(datname)) as size,
    numbackends as connections
FROM pg_stat_database 
WHERE datname = 'sprintconnect';
"

echo
echo "=== Redis Memory Usage ==="
redis-cli info memory | grep used_memory_human

echo
echo "=== Queue Depths ==="
# Get queue depths from Redis
redis-cli llen discovery_queue
redis-cli llen health_check_queue
redis-cli llen chat_queue

echo
echo "=== Request Rate (Last Hour) ==="
# This would typically come from Prometheus
curl -s 'http://prometheus:9090/api/v1/query?query=rate(http_requests_total[1h])' | \
    jq -r '.data.result[0].value[1]'
```

### Scaling Recommendations
```python
# Auto-scaling recommendations based on metrics
import asyncio
from datetime import datetime, timedelta

class CapacityPlanner:
    def __init__(self):
        self.metrics_client = PrometheusClient()
        self.k8s_client = KubernetesClient()
    
    async def analyze_capacity(self):
        """Analyze current capacity and provide scaling recommendations"""
        
        # Get current metrics
        cpu_usage = await self.metrics_client.query(
            'avg(rate(container_cpu_usage_seconds_total[5m])) by (pod)'
        )
        
        memory_usage = await self.metrics_client.query(
            'avg(container_memory_working_set_bytes) by (pod)'
        )
        
        request_rate = await self.metrics_client.query(
            'sum(rate(http_requests_total[5m]))'
        )
        
        # Analyze patterns
        recommendations = []
        
        # CPU analysis
        if cpu_usage > 0.7:  # 70% CPU usage
            recommendations.append({
                'type': 'scale_up',
                'component': 'api',
                'reason': f'High CPU usage: {cpu_usage:.2%}',
                'action': 'Increase replica count'
            })
        
        # Request rate analysis
        current_hour = datetime.now().hour
        if 9 <= current_hour <= 17:  # Business hours
            if request_rate > 100:  # requests per second
                recommendations.append({
                    'type': 'scale_up',
                    'component': 'api',
                    'reason': f'High request rate: {request_rate:.1f} req/s',
                    'action': 'Scale up for business hours traffic'
                })
        
        # Queue depth analysis
        queue_depth = await self.metrics_client.query('celery_queue_depth')
        if queue_depth > 500:
            recommendations.append({
                'type': 'scale_up',
                'component': 'workers',
                'reason': f'High queue depth: {queue_depth}',
                'action': 'Add more worker instances'
            })
        
        return recommendations
    
    async def auto_scale(self, recommendations):
        """Automatically apply scaling recommendations"""
        for rec in recommendations:
            if rec['type'] == 'scale_up':
                if rec['component'] == 'api':
                    await self.k8s_client.scale_deployment(
                        'sprintconnect-api',
                        target_replicas=self._calculate_target_replicas('api')
                    )
                elif rec['component'] == 'workers':
                    await self.k8s_client.scale_deployment(
                        'sprintconnect-workers',
                        target_replicas=self._calculate_target_replicas('workers')
                    )
```

## Troubleshooting

### Common Issues and Solutions

#### High Database Connection Count
```bash
# Diagnosis
psql $DATABASE_URL -c "
SELECT 
    state,
    count(*) 
FROM pg_stat_activity 
WHERE datname = 'sprintconnect' 
GROUP BY state;
"

# Solution 1: Check for connection leaks
psql $DATABASE_URL -c "
SELECT 
    query,
    state,
    state_change,
    backend_start
FROM pg_stat_activity 
WHERE datname = 'sprintconnect' 
AND state = 'idle in transaction'
ORDER BY backend_start;
"

# Solution 2: Restart application with connection pool tuning
kubectl set env deployment/sprintconnect-api \
    DATABASE_POOL_SIZE=10 \
    DATABASE_MAX_OVERFLOW=20
```

#### High Memory Usage
```bash
# Check memory usage by container
kubectl top pods -n sprintconnect --containers

# Get detailed memory breakdown
kubectl exec -it sprintconnect-api-xxx -- ps aux --sort=-%mem

# Check for memory leaks
kubectl exec -it sprintconnect-api-xxx -- python -c "
import psutil
import gc
print(f'Memory usage: {psutil.virtual_memory().percent}%')
print(f'Objects in memory: {len(gc.get_objects())}')
"

# Solution: Restart pods with memory limits
kubectl delete pod -l app=sprintconnect-api -n sprintconnect
```

#### WebSocket Connection Issues
```bash
# Check WebSocket connections
kubectl logs -l app=sprintconnect-api -n sprintconnect | grep "websocket"

# Check load balancer configuration
kubectl describe ingress sprintconnect-ingress -n sprintconnect

# Test WebSocket connectivity
wscat -c wss://api.sprintconnect.com/chat/sessions/test/stream \
      -H "Authorization: Bearer $TOKEN"
```

### Debug Tools and Scripts

#### Health Check Script
```bash
#!/bin/bash
# health-check.sh

set -euo pipefail

NAMESPACE="sprintconnect"
TIMEOUT=30

echo "=== SprintConnect Health Check ==="
echo "Timestamp: $(date)"
echo

# Check pod status
echo "=== Pod Status ==="
kubectl get pods -n $NAMESPACE

echo
echo "=== Service Status ==="
kubectl get services -n $NAMESPACE

# Test API endpoints
echo
echo "=== API Health Checks ==="
API_URL="https://api.sprintconnect.com"

for endpoint in "/health" "/ready" "/metrics"; do
    echo -n "Testing ${API_URL}${endpoint}: "
    if curl -sf --max-time $TIMEOUT "${API_URL}${endpoint}" > /dev/null; then
        echo "✅ OK"
    else
        echo "❌ FAILED"
    fi
done

# Test database connectivity
echo
echo "=== Database Connectivity ==="
if psql $DATABASE_URL -c "SELECT 1;" > /dev/null 2>&1; then
    echo "✅ Database: OK"
else
    echo "❌ Database: FAILED"
fi

# Test Redis connectivity
echo
echo "=== Redis Connectivity ==="
if redis-cli -u $REDIS_URL ping > /dev/null 2>&1; then
    echo "✅ Redis: OK"
else
    echo "❌ Redis: FAILED"
fi

echo
echo "Health check completed"
```

This comprehensive operations guide provides everything needed to successfully deploy, monitor, and maintain SprintConnect in production environments. Regular review and updates of these procedures ensure optimal system performance and reliability.

---

## Addendums: Key Rotation, JWKS, SLOs, Incident Playbooks

### Key and JWKS Rotation
```yaml
jwks_rotation:
  schedule: "@weekly"
  steps:
    - generate_new_keypair
    - publish_to_vault_and_jwks
    - add_new_kid_with_overlap
    - wait_propagation: 24h
    - retire_old_kid
  monitoring:
    - stale_kid_alert: 48h
```

### OAuth Token Lifecycle Ops
```yaml
token_ops:
  refresh_rotation_reuse_detection: enabled
  revocation_endpoint_checks: hourly
  introspection_latency_slo_ms: 150
```

### SLOs
```yaml
slos:
  auth_decision_latency_p95_ms: 50
  discovery_completion_p95_s: 120
  health_staleness_max_s: 300
  api_error_rate_budget: 0.5%
  tool_invoke_latency_p95_ms: 500
```

### Incident Playbooks (Additions)
```yaml
playbooks:
  token_replay_suspected:
    detect: dpop_jti_reuse_or_mtls_mismatch
    contain: revoke_token, block_ip, require_step_up
    eradicate: rotate_keys_if_compromised
    recover: resume_traffic_with_monitoring
  manifest_verification_failure:
    detect: spike_in_jws_verify_errors
    contain: quarantine_server_registration
    eradicate: update_trust_roots_or_inform_provider
    recover: resume_registration_after_pass
  ssrf_attempts:
    detect: egress_proxy_denied_events
    contain: tighten_tenant_allowlist, alert_sec
    eradicate: patch_validation_rules
    recover: monitor_and_report
```
