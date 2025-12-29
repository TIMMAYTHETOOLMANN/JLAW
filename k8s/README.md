# Kubernetes Manifests for JLAW

This directory contains Kubernetes manifests for deploying JLAW SEC Forensic Analysis Platform to production clusters.

## Files Overview

- **namespace.yaml**: Creates the `jlaw-forensics` namespace
- **configmap.yaml**: Configuration for SEC EDGAR settings and system parameters
- **secrets.yaml.example**: Template for sensitive credentials (API keys, passwords)
- **pvc.yaml**: PersistentVolumeClaims for evidence (50GB) and reports (100GB)
- **deployment.yaml**: JLAW forensics engine deployment with 2 replicas
- **service.yaml**: ClusterIP service for internal communication
- **hpa.yaml**: HorizontalPodAutoscaler for automatic scaling (2-10 replicas)

## Quick Deployment

### Prerequisites

- Kubernetes cluster (v1.24+)
- `kubectl` configured
- Storage provisioner
- Metrics server (for autoscaling)

### Deploy All Resources

```bash
# 1. Create namespace
kubectl apply -f namespace.yaml

# 2. Configure secrets (IMPORTANT: Edit secrets.yaml first!)
cp secrets.yaml.example secrets.yaml
# Edit secrets.yaml with your actual credentials
kubectl apply -f secrets.yaml

# 3. Apply configuration
kubectl apply -f configmap.yaml

# 4. Create storage
kubectl apply -f pvc.yaml

# 5. Deploy application
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml

# 6. Enable autoscaling
kubectl apply -f hpa.yaml
```

### Verify Deployment

```bash
# Check pods
kubectl get pods -n jlaw-forensics

# Check services
kubectl get svc -n jlaw-forensics

# Check HPA
kubectl get hpa -n jlaw-forensics

# View logs
kubectl logs -n jlaw-forensics -l app=jlaw --tail=50
```

## Configuration

### Secrets Management

**⚠️ CRITICAL**: Never commit `secrets.yaml` to version control!

Edit `secrets.yaml` with your actual credentials:

```yaml
stringData:
  polygon_api_key: "pk_live_your_actual_key"
  neo4j_password: "strong_password_here"
  timescale_password: "strong_password_here"
  openai_api_key: "sk-your_actual_key"
  anthropic_api_key: "sk-ant-your_actual_key"
```

### ConfigMap Customization

Edit `configmap.yaml` to adjust:

- **sec_user_agent**: Your organization's contact info (required by SEC)
- **sec_rate_limit**: API rate limit (default: 6.0 req/s, max: 10.0)
- **rfc3161_timestamp_url**: Timestamp authority URL

### Resource Limits

Default per-pod allocation:

| Resource | Request | Limit |
|----------|---------|-------|
| CPU      | 1 core  | 2 cores |
| Memory   | 2GB     | 4GB   |

Adjust in `deployment.yaml`:

```yaml
resources:
  requests:
    memory: "4Gi"
    cpu: "2000m"
  limits:
    memory: "8Gi"
    cpu: "4000m"
```

### Autoscaling

HPA configuration (in `hpa.yaml`):

- **Min replicas**: 2
- **Max replicas**: 10
- **CPU target**: 70%
- **Memory target**: 80%

Adjust thresholds:

```yaml
metrics:
- type: Resource
  resource:
    name: cpu
    target:
      type: Utilization
      averageUtilization: 70  # Adjust this
```

## Storage

### Evidence Storage (50GB)

Stores SEC filings and raw data. Adjust size in `pvc.yaml`:

```yaml
resources:
  requests:
    storage: 100Gi  # Increase if needed
```

### Reports Storage (100GB)

Stores generated forensic dossiers. Adjust size in `pvc.yaml`:

```yaml
resources:
  requests:
    storage: 200Gi  # Increase if needed
```

### Storage Class

Default: `standard`

For high-performance workloads, use SSD-backed storage:

```yaml
spec:
  storageClassName: ssd  # or fast, premium, etc.
```

## Security

### Non-Root Execution

JLAW runs as user ID 1000 with:

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 1000
  allowPrivilegeEscalation: false
```

### Network Policies

To restrict network access, create a NetworkPolicy:

```bash
kubectl apply -f - <<EOF
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
  egress:
  - to:
    - podSelector: {}
  - ports:  # Allow external HTTPS
    - protocol: TCP
      port: 443
EOF
```

### RBAC

Create a ServiceAccount with minimal permissions:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: jlaw-sa
  namespace: jlaw-forensics
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: jlaw-role
  namespace: jlaw-forensics
rules:
- apiGroups: [""]
  resources: ["configmaps", "secrets"]
  verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: jlaw-rolebinding
  namespace: jlaw-forensics
subjects:
- kind: ServiceAccount
  name: jlaw-sa
roleRef:
  kind: Role
  name: jlaw-role
  apiGroup: rbac.authorization.k8s.io
```

## Monitoring

### Health Checks

The deployment includes liveness and readiness probes:

```yaml
livenessProbe:
  exec:
    command: [python, scripts/health_check.py]
  initialDelaySeconds: 30
  periodSeconds: 30

readinessProbe:
  exec:
    command: [python, scripts/health_check.py]
  initialDelaySeconds: 10
  periodSeconds: 10
```

### Metrics

View resource usage:

```bash
# Pod metrics
kubectl top pods -n jlaw-forensics

# HPA status
kubectl get hpa -n jlaw-forensics -w

# Events
kubectl get events -n jlaw-forensics --sort-by='.lastTimestamp'
```

## Troubleshooting

### Pods Not Starting

```bash
# Check events
kubectl describe pod -n jlaw-forensics <pod-name>

# Check logs
kubectl logs -n jlaw-forensics <pod-name>

# Check previous instance
kubectl logs -n jlaw-forensics <pod-name> --previous
```

### Storage Issues

```bash
# Check PVC status
kubectl get pvc -n jlaw-forensics

# Describe PVC
kubectl describe pvc jlaw-evidence-pvc -n jlaw-forensics

# Check available storage classes
kubectl get storageclass
```

### HPA Not Scaling

```bash
# Check metrics server
kubectl get apiservice v1beta1.metrics.k8s.io

# Describe HPA
kubectl describe hpa jlaw-forensics-hpa -n jlaw-forensics

# Check pod resource requests
kubectl get pod -n jlaw-forensics -o yaml | grep -A 5 resources
```

## Updating

### Rolling Update

```bash
# Update image tag
kubectl set image deployment/jlaw-forensics \
  jlaw-forensics=ghcr.io/timmaythetoolmann/jlaw:v4.1.0 \
  -n jlaw-forensics

# Monitor rollout
kubectl rollout status deployment/jlaw-forensics -n jlaw-forensics
```

### Rollback

```bash
# Rollback to previous version
kubectl rollout undo deployment/jlaw-forensics -n jlaw-forensics

# Check rollout history
kubectl rollout history deployment/jlaw-forensics -n jlaw-forensics
```

## Cleanup

Remove all JLAW resources:

```bash
kubectl delete -f hpa.yaml
kubectl delete -f service.yaml
kubectl delete -f deployment.yaml
kubectl delete -f pvc.yaml
kubectl delete -f configmap.yaml
kubectl delete -f secrets.yaml
kubectl delete -f namespace.yaml
```

**⚠️ WARNING**: This will delete all evidence and reports stored in PVCs!

## Production Considerations

### High Availability

- Deploy across multiple availability zones
- Use pod anti-affinity rules
- Configure pod disruption budgets

### Backup Strategy

- Regular PVC snapshots
- Database backups (Neo4j, TimescaleDB)
- Document restore procedures

### Cost Optimization

- Use spot instances for non-critical workloads
- Configure cluster autoscaler
- Monitor and right-size resources

## Support

- Full Guide: [docs/deployment/kubernetes.md](../../docs/deployment/kubernetes.md)
- GitHub Issues: https://github.com/TIMMAYTHETOOLMANN/JLAW/issues
- Documentation: https://github.com/TIMMAYTHETOOLMANN/JLAW/docs
