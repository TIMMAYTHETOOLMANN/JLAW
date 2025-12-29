# JLAW Deployment Checklist

## Pre-Deployment

### Environment Configuration
- [ ] Set `SEC_USER_AGENT` with your organization's contact info
- [ ] Obtain Polygon.io API key for market data
- [ ] (Optional) Obtain OpenAI API key for AI validation
- [ ] (Optional) Obtain Anthropic API key for AI validation
- [ ] Generate strong passwords for databases (Neo4j, TimescaleDB)

### Infrastructure Prerequisites
- [ ] Docker 20.10+ installed (for Docker deployment)
- [ ] Kubernetes 1.24+ cluster available (for K8s deployment)
- [ ] Storage provisioner configured (for K8s deployment)
- [ ] Metrics server installed (for HPA autoscaling)
- [ ] 8GB+ RAM available per instance
- [ ] 50GB+ storage for evidence
- [ ] 100GB+ storage for reports

## Docker Deployment

### Local/Single-Host Deployment

1. **Clone Repository**
   ```bash
   git clone https://github.com/TIMMAYTHETOOLMANN/JLAW.git
   cd JLAW
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Start Services**
   ```bash
   docker compose up -d
   ```

4. **Verify Health**
   ```bash
   docker compose exec jlaw python scripts/health_check.py
   ```

5. **Check Logs**
   ```bash
   docker compose logs -f jlaw
   ```

**Reference**: [docs/deployment/docker.md](docs/deployment/docker.md)

## Kubernetes Deployment

### Production Cluster Deployment

1. **Create Namespace**
   ```bash
   kubectl apply -f k8s/namespace.yaml
   ```

2. **Configure Secrets**
   ```bash
   cp k8s/secrets.yaml.example k8s/secrets.yaml
   # Edit k8s/secrets.yaml with actual credentials
   kubectl apply -f k8s/secrets.yaml
   ```

3. **Apply Configuration**
   ```bash
   kubectl apply -f k8s/configmap.yaml
   ```

4. **Provision Storage**
   ```bash
   kubectl apply -f k8s/pvc.yaml
   ```

5. **Deploy Application**
   ```bash
   kubectl apply -f k8s/deployment.yaml
   kubectl apply -f k8s/service.yaml
   ```

6. **Enable Autoscaling**
   ```bash
   kubectl apply -f k8s/hpa.yaml
   ```

7. **Verify Deployment**
   ```bash
   kubectl get pods -n jlaw-forensics
   kubectl logs -n jlaw-forensics -l app=jlaw --tail=50
   ```

8. **Test Health Check**
   ```bash
   kubectl exec -n jlaw-forensics deployment/jlaw-forensics -- python scripts/health_check.py
   ```

**Reference**: [docs/deployment/kubernetes.md](docs/deployment/kubernetes.md)

## Post-Deployment Verification

### Health Checks
- [ ] Health check script passes (exit code 0)
- [ ] All 15 nodes load successfully
- [ ] Evidence chain components available (HashService, MerkleTree)
- [ ] Detection algorithms loaded (23 patterns)

### Database Connectivity
- [ ] Neo4j connection established
- [ ] TimescaleDB connection established
- [ ] Redis connection established

### External APIs
- [ ] SEC EDGAR API accessible (test with sample CIK)
- [ ] Polygon.io API authenticated (if configured)
- [ ] RFC 3161 timestamp service reachable

### Resource Monitoring
- [ ] CPU usage within limits
- [ ] Memory usage within limits
- [ ] Storage usage tracked
- [ ] Network connectivity stable

## Security Validation

### Container Security
- [ ] Running as non-root user (UID 1000)
- [ ] No privilege escalation
- [ ] Minimal capabilities (all dropped)
- [ ] Read-only root filesystem (if applicable)

### Secrets Management
- [ ] Secrets stored in Kubernetes Secrets (not in code)
- [ ] `k8s/secrets.yaml` not committed to git
- [ ] Environment variables properly injected
- [ ] API keys not logged

### Network Security
- [ ] Network policies configured (if applicable)
- [ ] Only required ports exposed
- [ ] TLS/SSL for external communications
- [ ] Database connections encrypted

### Vulnerability Scanning
- [ ] Trivy scan completed (0 CRITICAL/HIGH vulnerabilities)
- [ ] Dependency audit passed (Safety/Bandit)
- [ ] SAST scanning completed

## Performance Validation

### Load Testing
- [ ] Single forensic analysis completes successfully
- [ ] Concurrent analyses handled properly
- [ ] Resource usage scales linearly
- [ ] HPA triggers at expected thresholds (K8s only)

### Caching
- [ ] SEC EDGAR cache functioning
- [ ] Redis cache operational
- [ ] Cache hit rate acceptable (>50% after warmup)

### Storage
- [ ] Evidence directory writable
- [ ] Reports directory writable
- [ ] Sufficient disk space available
- [ ] Backup strategy configured

## Monitoring & Alerting

### Metrics Collection
- [ ] Prometheus metrics endpoint (if configured)
- [ ] Resource utilization tracked
- [ ] Application logs centralized
- [ ] Error tracking configured (Sentry/etc)

### Alerting
- [ ] High memory usage alerts
- [ ] High CPU usage alerts
- [ ] Pod restart alerts (K8s)
- [ ] Health check failure alerts

## Operational Readiness

### Documentation
- [ ] Deployment guide reviewed
- [ ] Runbook prepared for common issues
- [ ] Escalation procedures documented
- [ ] Backup/restore procedures tested

### Team Training
- [ ] Team familiar with health check script
- [ ] Team can access logs (Docker/K8s)
- [ ] Team can scale deployment
- [ ] Team can rollback releases

### Backup Strategy
- [ ] Evidence volume backup configured
- [ ] Reports volume backup configured
- [ ] Database backups scheduled
- [ ] Backup restoration tested

## Troubleshooting Common Issues

### Container Won't Start
1. Check logs: `docker logs` or `kubectl logs`
2. Verify environment variables set
3. Check resource availability
4. Validate secrets/config

### Health Check Failing
1. Run health check manually
2. Check for missing dependencies
3. Verify PYTHONPATH set correctly
4. Ensure all node imports succeed

### Database Connection Failures
1. Verify database services running
2. Check network connectivity
3. Validate credentials in secrets
4. Test connection from within container

### Storage Issues
1. Check PVC status (K8s) or volume mounts (Docker)
2. Verify storage provisioner working
3. Check disk space availability
4. Validate permissions (UID 1000)

## Rollback Procedure

### Docker
```bash
# Stop current version
docker compose down

# Checkout previous version
git checkout <previous-commit>

# Rebuild and start
docker compose up -d --build
```

### Kubernetes
```bash
# View rollout history
kubectl rollout history deployment/jlaw-forensics -n jlaw-forensics

# Rollback to previous version
kubectl rollout undo deployment/jlaw-forensics -n jlaw-forensics

# Or rollback to specific revision
kubectl rollout undo deployment/jlaw-forensics -n jlaw-forensics --to-revision=2
```

## Support Resources

- **Documentation**: [GitHub Repo](https://github.com/TIMMAYTHETOOLMANN/JLAW)
- **Docker Guide**: [docs/deployment/docker.md](docs/deployment/docker.md)
- **Kubernetes Guide**: [docs/deployment/kubernetes.md](docs/deployment/kubernetes.md)
- **K8s Quick Start**: [k8s/README.md](k8s/README.md)
- **Issues**: [GitHub Issues](https://github.com/TIMMAYTHETOOLMANN/JLAW/issues)

## Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| DevOps Lead | | | |
| Security Lead | | | |
| Engineering Lead | | | |
| Operations Lead | | | |

---

**Deployment Status**: ☐ Pre-Production ☐ Production ☐ Verified

**Deployed By**: _________________

**Deployment Date**: _________________

**Version**: 4.0.0

**Environment**: ☐ Development ☐ Staging ☐ Production
