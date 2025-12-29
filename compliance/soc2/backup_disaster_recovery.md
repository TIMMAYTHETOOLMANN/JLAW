# Backup and Disaster Recovery Plan

## SOC 2 Type II - Business Continuity and Availability

**Document Version:** 1.0  
**Effective Date:** December 2024  
**Review Cycle:** Annual  
**Plan Owner:** Chief Technology Officer (CTO)  
**Compliance Framework:** SOC 2 Trust Services Criteria - Availability (A1.2, A1.3)  

---

## I. Executive Summary

### 1.1 Purpose

This Backup and Disaster Recovery Plan ensures:
- **Availability:** JLAW systems remain operational during disasters
- **Recovery:** Systems can be restored within defined timeframes
- **Integrity:** Evidence and data are protected from loss
- **Compliance:** SOC 2, FRE 902, and regulatory requirements met

### 1.2 Recovery Objectives

| Metric | Target | Definition |
|--------|--------|------------|
| **RTO (Recovery Time Objective)** | < 4 hours | Maximum tolerable downtime |
| **RPO (Recovery Point Objective)** | < 1 hour | Maximum acceptable data loss |
| **MTTR (Mean Time To Repair)** | < 2 hours | Average time to restore service |

---

## II. Backup Strategy

### 2.1 Backup Types

#### 2.1.1 Full Backup

**Frequency:** Weekly (Sunday 00:00 AM UTC)  
**Retention:** 4 weeks (4 full backups retained)  
**Duration:** 2-4 hours  
**Storage:** On-site NAS + Off-site S3  

**Includes:**
- Complete database dump (PostgreSQL, Neo4j)
- All evidence files
- All dossiers and reports
- Application configuration
- System configuration

#### 2.1.2 Incremental Backup

**Frequency:** Hourly (every hour, 24/7)  
**Retention:** 7 days  
**Duration:** 5-15 minutes  
**Storage:** On-site NAS  

**Includes:**
- Changed evidence files (since last backup)
- New analysis results
- New audit logs
- Database transaction logs

#### 2.1.3 Continuous Backup (Transaction Log Shipping)

**Frequency:** Real-time (continuous)  
**Retention:** 24 hours  
**Lag:** < 5 minutes  
**Storage:** Hot standby database  

**Includes:**
- PostgreSQL Write-Ahead Logs (WAL)
- Database transactions (real-time replication)

### 2.2 Backup Schedule

**Daily Schedule:**
```
00:00 - 04:00 UTC  Sunday:    Full Backup (4 hours)
Every Hour        Mon-Sat:   Incremental Backup (15 min)
Continuous        24/7:      Transaction Log Shipping
```

**Monthly Schedule:**
```
First Sunday      00:00 AM:  Extended Full Backup (archived for 1 year)
Last Sunday       Verify:    Disaster Recovery Test
```

---

## III. Backup Infrastructure

### 3.1 Backup Storage Locations

#### 3.1.1 Primary Backup (On-Site)

**Technology:** Synology NAS with RAID-6  
**Location:** Primary data center (same building)  
**Capacity:** 50 TB usable  
**Access Time:** Immediate (< 1 minute)  

**Use Cases:**
- Quick restore (operational issues)
- Hourly incremental backups
- Transaction log shipping

#### 3.1.2 Secondary Backup (Off-Site)

**Technology:** AWS S3 Standard  
**Location:** AWS us-east-1 (separate from primary)  
**Capacity:** Unlimited  
**Access Time:** < 5 minutes  

**Use Cases:**
- Disaster recovery
- Weekly full backups
- Monthly archival backups

#### 3.1.3 Tertiary Backup (Cold Archive)

**Technology:** AWS S3 Glacier Deep Archive  
**Location:** AWS us-west-2 (cross-region)  
**Capacity:** Unlimited  
**Access Time:** 12-48 hours  

**Use Cases:**
- Long-term retention (7 years)
- Compliance archives
- Disaster recovery (catastrophic data center loss)

### 3.2 Backup Encryption

**At Rest:**
- AES-256-GCM encryption (all backups)
- Encryption keys: AWS KMS (rotated every 90 days)

**In Transit:**
- TLS 1.3 (backup data transfer)
- Secure delete after upload (source data wiped)

---

## IV. Disaster Recovery Scenarios

### 4.1 Scenario 1: Single Server Failure (RTO: 1 hour)

**Impact:** One application server fails (hardware failure, OS crash)

**Recovery Steps:**
```
1. Automatic failover to standby server (< 5 minutes)
2. Load balancer redirects traffic
3. Monitor standby server (ensure stability)
4. Schedule hardware replacement/repair
5. Restore failed server from backup
6. Return to normal operations
```

**Recovery Time:** < 1 hour (mostly automated)

### 4.2 Scenario 2: Database Corruption (RTO: 2 hours)

**Impact:** Database corruption detected (evidence data affected)

**Recovery Steps:**
```
1. Stop application (prevent further writes)
2. Assess corruption extent (which tables/evidence)
3. Restore database from last full backup
4. Apply incremental backups (hourly backups since full)
5. Apply transaction logs (WAL shipping)
6. Verify data integrity (hash verification)
7. Restart application
8. Notify users (evidence chain verification required)
```

**Recovery Time:** < 2 hours  
**Data Loss:** < 1 hour (last incremental backup)

### 4.3 Scenario 3: Ransomware Attack (RTO: 4 hours)

**Impact:** Ransomware encrypts primary systems and backups (if accessible)

**Recovery Steps:**
```
1. Isolate infected systems (network disconnect)
2. Assess infection extent (which systems compromised)
3. Activate off-site backup recovery (AWS S3)
4. Provision clean infrastructure (new VMs/containers)
5. Restore from off-site backup (last clean backup)
6. Apply incremental backups (if available and clean)
7. Verify system integrity (malware scan)
8. Restore network connectivity (firewalled)
9. Monitor for reinfection (24 hours enhanced monitoring)
10. Root cause analysis and remediation
```

**Recovery Time:** < 4 hours  
**Data Loss:** Variable (depends on last clean backup)

### 4.4 Scenario 4: Data Center Disaster (RTO: 8 hours)

**Impact:** Primary data center destroyed (fire, flood, earthquake)

**Recovery Steps:**
```
1. Declare disaster (activate DR plan)
2. Activate secondary data center (AWS cloud)
3. Restore from off-site backups (AWS S3)
4. Reconfigure DNS (point to DR site)
5. Restore all services (application, databases)
6. Verify functionality (full system test)
7. Notify users (service restored at DR site)
8. Operate from DR site until primary restored
```

**Recovery Time:** < 8 hours (full system rebuild)  
**Data Loss:** < 1 hour (last incremental backup replicated to S3)

---

## V. Recovery Procedures

### 5.1 File-Level Recovery (Individual Evidence File)

**Use Case:** Single evidence file corrupted or accidentally deleted

**Procedure:**
```bash
# Step 1: Identify file to restore
FILE_PATH="/evidence/case-123/E001_10K.pdf"
BACKUP_DATE="2024-12-29"

# Step 2: Locate backup
aws s3 ls s3://jlaw-backups/evidence/$BACKUP_DATE/

# Step 3: Download from backup
aws s3 cp s3://jlaw-backups/evidence/$BACKUP_DATE/E001_10K.pdf /tmp/

# Step 4: Verify hash
sha256sum /tmp/E001_10K.pdf
# Compare with hash in custody log

# Step 5: Restore file
sudo cp /tmp/E001_10K.pdf $FILE_PATH
sudo chown jlaw:jlaw_evidence $FILE_PATH
sudo chmod 640 $FILE_PATH

# Step 6: Log restoration
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) - File restored: $FILE_PATH from backup $BACKUP_DATE" >> /var/log/jlaw/evidence_restore.log
```

**Recovery Time:** < 15 minutes  
**Approval Required:** Evidence Custodian

### 5.2 Database Recovery (Full Restore)

**Use Case:** Database corruption or data loss

**Procedure:**
```bash
# Step 1: Stop JLAW application
sudo systemctl stop jlaw

# Step 2: Stop PostgreSQL
sudo systemctl stop postgresql

# Step 3: Backup current (corrupted) database
sudo pg_dump jlaw_evidence > /tmp/corrupted_db_$(date +%Y%m%d).sql

# Step 4: Drop and recreate database
sudo -u postgres psql -c "DROP DATABASE jlaw_evidence;"
sudo -u postgres psql -c "CREATE DATABASE jlaw_evidence;"

# Step 5: Restore from backup
BACKUP_FILE="/backups/postgresql/jlaw_evidence_20241229_full.sql.gz"
gunzip -c $BACKUP_FILE | sudo -u postgres psql jlaw_evidence

# Step 6: Apply incremental backups (if available)
for INCREMENTAL in /backups/postgresql/incremental/jlaw_evidence_*.sql.gz; do
  echo "Applying $INCREMENTAL"
  gunzip -c $INCREMENTAL | sudo -u postgres psql jlaw_evidence
done

# Step 7: Verify data integrity
sudo -u postgres psql jlaw_evidence -c "SELECT COUNT(*) FROM evidence;"
# Compare with expected count

# Step 8: Start PostgreSQL
sudo systemctl start postgresql

# Step 9: Start JLAW application
sudo systemctl start jlaw

# Step 10: Verify functionality
curl http://localhost:8080/health
```

**Recovery Time:** < 2 hours  
**Approval Required:** CTO + CISO (if evidence affected)

### 5.3 Disaster Recovery Failover (Full DR Site Activation)

**Use Case:** Primary data center unavailable

**Procedure:**
```
1. Activate DR runbook (manual or automated trigger)
2. Provision infrastructure at DR site:
   - Launch EC2 instances (application servers)
   - Launch RDS instances (PostgreSQL database)
   - Launch ElastiCache (Redis)
   - Launch EC2 instances (Neo4j)
3. Restore data from off-site backups:
   - S3 to application servers (evidence files)
   - S3 to RDS (database dump)
   - S3 to Neo4j (graph database)
4. Configure networking:
   - Update DNS (jlaw.forensics → DR site IP)
   - Configure load balancer
   - Update firewall rules
5. Start services:
   - Start PostgreSQL
   - Start Neo4j
   - Start Redis
   - Start JLAW application
6. Verify functionality:
   - Health checks (all services UP)
   - Smoke tests (login, evidence access)
   - Integration tests (run critical tests)
7. Monitor for 24 hours (enhanced monitoring)
8. Notify users (service restored at DR site)
```

**Recovery Time:** < 8 hours (manual) or < 2 hours (automated)  
**Approval Required:** CEO + CTO (major business decision)

---

## VI. Backup Verification

### 6.1 Automated Verification (Daily)

**Verification Tests:**
- Backup completion check (no errors in logs)
- File count verification (expected number of files)
- Backup size verification (within expected range)
- Encryption verification (encrypted flag set)

**Alerts:**
- Backup failure (immediate email + PagerDuty)
- Backup size anomaly (> 20% deviation)
- Backup duration exceeds SLA (> 6 hours for full backup)

### 6.2 Manual Verification (Weekly)

**Test Restore Procedure:**
```
1. Select random evidence file from backup
2. Restore file to test environment
3. Compute SHA-256 hash
4. Compare with hash in custody log
5. Verify file opens correctly (PDF, JSON, etc.)
6. Document verification (backup verification log)
```

**Frequency:** Weekly (every Sunday after full backup)  
**Responsibility:** DevOps Engineer

### 6.3 Full Disaster Recovery Test (Monthly)

**DR Test Procedure:**
```
1. Schedule DR test (last Sunday of month)
2. Notify team (war room activated)
3. Simulate disaster (shutdown primary systems)
4. Activate DR site (follow DR runbook)
5. Restore from off-site backups
6. Verify functionality (full integration test)
7. Measure recovery time (actual vs. RTO target)
8. Document lessons learned
9. Update DR runbook (if needed)
10. Return to normal operations
```

**Frequency:** Monthly  
**Duration:** 4-8 hours  
**Responsibility:** CTO (lead), entire IT team

---

## VII. Backup Retention Policy

### 7.1 Retention Schedule

| Backup Type | Retention Period | Storage Location |
|-------------|------------------|------------------|
| **Hourly Incremental** | 7 days | On-site NAS |
| **Weekly Full** | 4 weeks (4 backups) | On-site NAS + S3 |
| **Monthly Archive** | 1 year (12 backups) | S3 Standard |
| **Annual Archive** | 7 years | S3 Glacier Deep Archive |

### 7.2 Backup Deletion

**Automated Deletion:**
- Hourly incremental: 7 days (automatic rotation)
- Weekly full: 4 weeks (automatic rotation)

**Manual Deletion (with approval):**
- Monthly archive: After 1 year (CTO approval)
- Annual archive: After 7 years (CTO + Legal Counsel approval)

---

## VIII. Roles and Responsibilities

| Role | Responsibility |
|------|----------------|
| **CTO** | DR plan ownership, failover authorization, budget allocation |
| **CISO** | Security review, evidence integrity validation |
| **DevOps Team** | Backup execution, restore procedures, DR testing |
| **Database Administrator** | Database backup/restore, replication management |
| **Evidence Custodian** | Evidence integrity verification, custody log updates |
| **Internal Audit** | DR test observation, compliance validation |

---

## IX. Communication Plan

### 9.1 Disaster Declaration

**Authority to Declare Disaster:** CTO or CEO

**Notification Sequence:**
1. **Immediate:** IT team (PagerDuty, phone tree)
2. **Within 15 min:** Executive team (CEO, CFO, CISO)
3. **Within 30 min:** All employees (email, Slack)
4. **Within 1 hour:** Clients (affected by outage)
5. **Within 4 hours:** Regulatory authorities (if required)

### 9.2 Status Updates

**During DR Event:**
- **Internal:** Hourly updates (Slack #incident-response)
- **External:** Every 4 hours (email to clients)

**After DR Recovery:**
- Post-incident report (within 48 hours)
- Root cause analysis (within 7 days)

---

## X. Compliance and Testing

### 10.1 SOC 2 Requirements

**Required Evidence:**
- Backup configuration documentation (this document)
- Backup success logs (daily)
- Restore test results (weekly file restoration)
- DR test results (monthly full DR test)
- RTO/RPO compliance metrics (monthly)

### 10.2 Testing Schedule

| Test Type | Frequency | Duration | Next Test Date |
|-----------|-----------|----------|----------------|
| **File Restore** | Weekly | 30 min | Every Sunday |
| **Database Restore** | Monthly | 2 hours | Last Sunday |
| **Full DR Test** | Quarterly | 8 hours | Q1, Q2, Q3, Q4 |
| **DR Plan Review** | Annual | 4 hours | December |

---

## XI. Metrics and KPIs

| Metric | Target | Actual (Last Month) |
|--------|--------|---------------------|
| **RTO Compliance** | 100% (< 4 hours) | [To be measured] |
| **RPO Compliance** | 100% (< 1 hour) | [To be measured] |
| **Backup Success Rate** | ≥ 99% | [To be measured] |
| **Restore Success Rate** | 100% | [To be measured] |
| **DR Test Completion** | 100% (monthly) | [To be measured] |

---

## XII. References

1. **SOC 2 Trust Services Criteria:** A1.2, A1.3 (Backup and Recovery)
2. **NIST SP 800-34:** Contingency Planning Guide for IT Systems
3. **ISO 22301:2019:** Business Continuity Management
4. **ISO 27031:2011:** ICT Readiness for Business Continuity

---

## XIII. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-12-29 | CTO | Initial DR plan creation |

---

**Plan Owner:** Chief Technology Officer  
**Next Review Date:** December 2025  
**Next DR Test:** Last Sunday of each month  
**Compliance Framework:** SOC 2 Type II, ISO 22301, NIST SP 800-34  
