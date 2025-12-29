# JLAW Kubernetes Deployment Guide

This guide covers deploying JLAW SEC Forensic Analysis Platform to Kubernetes clusters for production use.

## Prerequisites

- Kubernetes cluster (v1.24+)
- `kubectl` CLI configured
- Storage provisioner for PersistentVolumeClaims
- Metrics server (for HPA)
- 50GB+ storage for evidence
- 100GB+ storage for reports

## Quick Start

### 1. Create Namespace

```bash
kubectl apply -f k8s/namespace.yaml
```

### 2. Configure Secrets

Copy the example secrets file and add your actual credentials:

```bash
cp k8s/secrets.yaml.example k8s/secrets.yaml
# Edit k8s/secrets.yaml with your actual API keys and passwords
kubectl apply -f k8s/secrets.yaml
```

**Required Secrets:**
- `polygon_api_key`: Polygon.io API key for market data
- `neo4j_password`: Neo4j graph database password
- `timescale_password`: TimescaleDB password
- `openai_api_key`: (Optional) OpenAI API key for AI validation
- `anthropic_api_key`: (Optional) Anthropic API key for AI validation

### 3. Apply Configuration

```bash
kubectl apply -f k8s/configmap.yaml
```

### 4. Provision Storage

```bash
kubectl apply -f k8s/pvc.yaml
```

Verify PVC creation:
```bash
kubectl get pvc -n jlaw-forensics
```

### 5. Deploy JLAW

```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

Verify deployment:
```bash
kubectl get pods -n jlaw-forensics
kubectl logs -n jlaw-forensics -l app=jlaw --tail=50
```

### 6. Enable Autoscaling

```bash
kubectl apply -f k8s/hpa.yaml
```

Check HPA status:
```bash
kubectl get hpa -n jlaw-forensics
```

## Deployment Verification

### Check Pod Health

```bash
# View pod status
kubectl get pods -n jlaw-forensics -o wide

# Check health probe results
kubectl describe pod -n jlaw-forensics -l app=jlaw

# View logs
kubectl logs -n jlaw-forensics -l app=jlaw --tail=100 -f
```

### Test Health Check

```bash
# Execute health check inside pod
kubectl exec -n jlaw-forensics deployment/jlaw-forensics -- python scripts/health_check.py
```

Expected output:
```
============================================================
JLAW FORENSIC SYSTEM HEALTH CHECK
============================================================

[1/5] Testing Core Engine Components...
  ✓ RecursiveProsecutorialEngine
  ✓ HashService (Triple-hash integrity)
  ✓ MerkleTree (RFC 6962 compliant)
...
✓ JLAW HEALTH CHECK PASSED
```

## Scaling Operations

### Manual Scaling

```bash
# Scale to 5 replicas
kubectl scale deployment/jlaw-forensics -n jlaw-forensics --replicas=5

# Verify
kubectl get pods -n jlaw-forensics
```

### Autoscaling Configuration

The HPA automatically scales based on:
- CPU utilization (target: 70%)
- Memory utilization (target: 80%)
- Min replicas: 2
- Max replicas: 10

View current metrics:
```bash
kubectl get hpa -n jlaw-forensics -w
kubectl top pods -n jlaw-forensics
```

## Resource Management

### Default Resource Allocation (per pod)

**Requests (guaranteed):**
- CPU: 1 core
- Memory: 2GB

**Limits (maximum):**
- CPU: 2 cores
- Memory: 4GB

### Adjust Resources

Edit `k8s/deployment.yaml`:
```yaml
resources:
  requests:
    memory: "4Gi"
    cpu: "2000m"
  limits:
    memory: "8Gi"
    cpu: "4000m"
```

Apply changes:
```bash
kubectl apply -f k8s/deployment.yaml
kubectl rollout status deployment/jlaw-forensics -n jlaw-forensics
```

## Storage Management

### Evidence Storage (50GB)

```bash
# Check usage
kubectl exec -n jlaw-forensics deployment/jlaw-forensics -- df -h /app/evidence

# Expand if needed (edit pvc.yaml and apply)
kubectl edit pvc jlaw-evidence-pvc -n jlaw-forensics
```

### Reports Storage (100GB)

```bash
# Check usage
kubectl exec -n jlaw-forensics deployment/jlaw-forensics -- df -h /app/reports
```

### Backup Strategy

```bash
# Create backup of evidence
kubectl exec -n jlaw-forensics deployment/jlaw-forensics -- tar -czf /tmp/evidence-backup.tar.gz /app/evidence

# Copy to local machine
kubectl cp jlaw-forensics/jlaw-forensics-<pod-id>:/tmp/evidence-backup.tar.gz ./evidence-backup.tar.gz
```

## Monitoring & Debugging

### View Real-time Logs

```bash
# All pods
kubectl logs -n jlaw-forensics -l app=jlaw -f

# Specific pod
kubectl logs -n jlaw-forensics <pod-name> -f

# Previous pod instance
kubectl logs -n jlaw-forensics <pod-name> --previous
```

### Interactive Shell

```bash
kubectl exec -it -n jlaw-forensics deployment/jlaw-forensics -- /bin/bash
```

### Resource Metrics

```bash
# CPU/Memory usage
kubectl top pods -n jlaw-forensics

# Node allocation
kubectl describe node | grep -A 5 "jlaw-forensics"
```

## Security Considerations

### Non-Root Execution

JLAW runs as user `jlaw` (UID 1000) with:
- `runAsNonRoot: true`
- `allowPrivilegeEscalation: false`
- All capabilities dropped

### Secrets Management

**Best Practices:**
1. Never commit `k8s/secrets.yaml` to version control
2. Use Kubernetes secrets or external secret managers (Vault, AWS Secrets Manager)
3. Rotate credentials regularly
4. Use RBAC to restrict secret access

### Network Policies (Optional)

Create network policies to restrict pod-to-pod communication:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: jlaw-network-policy
  namespace: jlaw-forensics
spec:
  podSelector:
    matchLabels:
      app: jlaw
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: jlaw-forensics
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: jlaw-forensics
  - to:  # Allow external SEC EDGAR API
    - podSelector: {}
    ports:
    - protocol: TCP
      port: 443
```

## Updating JLAW

### Rolling Update

```bash
# Update image
kubectl set image deployment/jlaw-forensics -n jlaw-forensics \
  jlaw-forensics=ghcr.io/timmaythetoolmann/jlaw:v4.1.0

# Monitor rollout
kubectl rollout status deployment/jlaw-forensics -n jlaw-forensics

# Verify
kubectl get pods -n jlaw-forensics
```

### Rollback

```bash
# View rollout history
kubectl rollout history deployment/jlaw-forensics -n jlaw-forensics

# Rollback to previous version
kubectl rollout undo deployment/jlaw-forensics -n jlaw-forensics

# Rollback to specific revision
kubectl rollout undo deployment/jlaw-forensics -n jlaw-forensics --to-revision=2
```

## Troubleshooting

### Pod Won't Start

```bash
# Check events
kubectl describe pod -n jlaw-forensics <pod-name>

# Check logs
kubectl logs -n jlaw-forensics <pod-name>

# Check resource constraints
kubectl top nodes
kubectl get pods -n jlaw-forensics -o wide
```

### Health Check Failing

```bash
# Manual health check
kubectl exec -n jlaw-forensics deployment/jlaw-forensics -- python scripts/health_check.py

# Check probe configuration
kubectl describe pod -n jlaw-forensics <pod-name> | grep -A 10 "Liveness\|Readiness"
```

### Storage Issues

```bash
# Check PVC status
kubectl get pvc -n jlaw-forensics

# Check PV status
kubectl get pv

# Describe PVC for events
kubectl describe pvc -n jlaw-forensics jlaw-evidence-pvc
```

### HPA Not Scaling

```bash
# Check metrics server
kubectl get apiservice v1beta1.metrics.k8s.io

# Check HPA events
kubectl describe hpa -n jlaw-forensics jlaw-forensics-hpa

# Verify resource requests are set
kubectl get deployment -n jlaw-forensics jlaw-forensics -o yaml | grep -A 5 resources
```

## Complete Teardown

```bash
# Delete all JLAW resources
kubectl delete -f k8s/hpa.yaml
kubectl delete -f k8s/service.yaml
kubectl delete -f k8s/deployment.yaml
kubectl delete -f k8s/pvc.yaml
kubectl delete -f k8s/configmap.yaml
kubectl delete -f k8s/secrets.yaml
kubectl delete -f k8s/namespace.yaml
```

## Production Considerations

### High Availability

- Deploy across multiple availability zones
- Use ReadWriteMany (RWX) PVCs for shared storage
- Configure pod anti-affinity rules

### Backup & Disaster Recovery

- Regular backups of evidence and reports volumes
- Database backups (Neo4j, TimescaleDB)
- Document restore procedures

### Monitoring Integration

- Prometheus metrics endpoint
- Grafana dashboards
- Alert manager for critical failures

### Cost Optimization

- Use node affinity for cost-effective node pools
- Configure cluster autoscaler
- Monitor resource utilization
- Right-size pod requests/limits

## Support

For issues or questions:
- GitHub Issues: https://github.com/TIMMAYTHETOOLMANN/JLAW/issues
- Documentation: https://github.com/TIMMAYTHETOOLMANN/JLAW/docs
