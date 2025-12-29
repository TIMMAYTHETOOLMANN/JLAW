# Audit Logging Specification

## SOC 2 Type II - Security and Availability Control

**Document Version:** 1.0  
**Effective Date:** December 2024  
**Review Cycle:** Annual  
**Policy Owner:** Chief Information Security Officer (CISO)  
**Compliance Framework:** SOC 2 Trust Services Criteria - Security (CC7.2), Availability (A1.2)  

---

## I. Purpose and Scope

### 1.1 Purpose

This Audit Logging Specification defines comprehensive logging requirements for the JLAW Forensic Analysis Platform to:
- **Detect:** Security incidents and policy violations
- **Investigate:** Security events and compliance breaches
- **Demonstrate:** Compliance with SOC 2, FRE 902, and regulatory requirements
- **Preserve:** Legal evidence with cryptographic integrity

### 1.2 Scope

This specification applies to:
- All JLAW application components
- All infrastructure systems (servers, databases, networks)
- All security-sensitive operations
- All user and system activities
- All evidence chain operations

**Retention Requirement:** Minimum 7 years (per legal and regulatory requirements)

---

## II. Logging Architecture

### 2.1 Log Types

| Log Type | Purpose | Retention | Storage Location |
|----------|---------|-----------|------------------|
| **Audit Logs** | Security-sensitive operations | 7 years | `/var/log/jlaw/audit.log` |
| **Security Logs** | Authentication, authorization | 2 years | `/var/log/jlaw/security.log` |
| **Application Logs** | JLAW execution, errors | 90 days | `/var/log/jlaw/application.log` |
| **Evidence Chain Logs** | Evidence acquisition, integrity | 7 years | `/evidence/custody/chain.log` |
| **Access Logs** | Resource access (files, data) | 2 years | `/var/log/jlaw/access.log` |
| **System Logs** | OS, database, infrastructure | 90 days | `/var/log/syslog`, `/var/log/postgresql/` |

### 2.2 Structured Logging Format

**Standard:** JSON (structured logging for machine parsing)

**Log Entry Schema:**
```json
{
  "timestamp": "2024-12-29T10:15:30.123456Z",
  "log_level": "INFO|WARN|ERROR|CRITICAL",
  "event_type": "authentication|authorization|evidence_access|...",
  "event_id": "uuid-v4",
  "user": {
    "id": "user_id",
    "username": "analyst_jane_doe",
    "role": "forensic_analyst",
    "ip_address": "192.168.1.100",
    "session_id": "session_uuid"
  },
  "resource": {
    "type": "evidence|dossier|configuration|database",
    "id": "resource_identifier",
    "path": "/evidence/case-123/filing.txt"
  },
  "action": "create|read|update|delete|execute",
  "result": "success|failure|denied",
  "details": {
    "reason": "insufficient_permissions",
    "error_code": "ERR_403",
    "additional_context": {}
  },
  "metadata": {
    "request_id": "req_uuid",
    "correlation_id": "correlation_uuid",
    "source_system": "jlaw_app|jlaw_api|postgres|neo4j"
  }
}
```

### 2.3 Log Storage Architecture

```
Application Logs
      ↓
[Local Disk Write] → [Log Rotation] → [Compression]
      ↓
[SIEM Forwarding (Real-Time)]
      ↓
[Splunk / ELK / CloudWatch Logs]
      ↓
[Long-Term Archival] → [AWS S3 Glacier / Azure Archive]
      ↓
[7-Year Retention] → [Secure Deletion]
```

**Write-Ahead Logging:** Logs written synchronously (not buffered) to prevent loss

---

## III. Events to Log

### 3.1 Authentication Events

**All authentication attempts shall be logged.**

| Event | Fields | Example |
|-------|--------|---------|
| **Login Success** | user, timestamp, IP, MFA method | `analyst_jane logged in via YubiKey from 192.168.1.100` |
| **Login Failure** | user, timestamp, IP, failure reason | `analyst_jane failed login (invalid password) from 192.168.1.100` |
| **MFA Challenge** | user, timestamp, MFA method | `analyst_jane requested MFA code (Duo Push)` |
| **MFA Failure** | user, timestamp, failure reason | `analyst_jane MFA timeout (no response)` |
| **Logout** | user, timestamp, session duration | `analyst_jane logged out (session: 2h 15m)` |
| **Session Timeout** | user, timestamp, inactivity period | `analyst_jane session expired (30 min inactivity)` |
| **Password Change** | user, timestamp, changed by | `analyst_jane changed password (self-service)` |
| **Password Reset** | user, timestamp, reset by | `admin_john reset password for analyst_jane` |

**Alert Trigger:** 5 failed login attempts in 5 minutes → Lock account, alert security

### 3.2 Authorization Events

**All access control decisions shall be logged.**

| Event | Fields | Example |
|-------|--------|---------|
| **Access Granted** | user, resource, action, timestamp | `analyst_jane granted READ on /evidence/case-123/filing.txt` |
| **Access Denied** | user, resource, action, reason | `analyst_jane denied DELETE on /evidence/case-123/filing.txt (insufficient permissions)` |
| **Privilege Escalation** | user, old role, new role, approved by | `analyst_jane elevated to lead_analyst by admin_john` |
| **Role Change** | user, old role, new role, changed by | `analyst_jane role changed from analyst to lead_analyst` |
| **Permission Grant** | user, resource, permission, granted by | `analyst_jane granted WRITE on /evidence/case-123/ by admin_john` |
| **Permission Revoke** | user, resource, permission, revoked by | `analyst_jane revoked WRITE on /evidence/case-123/ by admin_john` |

### 3.3 Evidence Chain Events (Critical)

**All evidence operations shall be logged with cryptographic integrity.**

| Event | Fields | Example |
|-------|--------|---------|
| **Evidence Acquired** | source, accession_number, timestamp, hash | `SEC filing 0001234567-19-000001 acquired (SHA-256: a3f5b8c9...)` |
| **Evidence Accessed** | user, evidence_id, timestamp, action | `analyst_jane read /evidence/case-123/filing.txt` |
| **Evidence Modified** | user, evidence_id, timestamp, hash (CRITICAL ALERT) | `analyst_jane modified /evidence/case-123/filing.txt (INTEGRITY VIOLATION)` |
| **Evidence Deleted** | user, evidence_id, timestamp, reason | `admin_john deleted /evidence/case-123/filing.txt (case closed)` |
| **Hash Verification** | evidence_id, timestamp, result | `Evidence E001 hash verified (PASS)` |
| **Merkle Root Computed** | evidence_set, root_hash, timestamp | `Merkle root computed for case-123: d4e5f6a7...` |
| **Timestamp Token Obtained** | evidence_id, TSA, timestamp, token_hash | `RFC 3161 timestamp obtained for case-123 from FreeTSA` |
| **Custody Transfer** | evidence_id, from_custodian, to_custodian, timestamp | `Evidence E001 transferred from analyst_jane to legal_counsel_bob` |

**Alert Trigger:** Evidence modification or hash mismatch → Immediate critical alert, freeze evidence

### 3.4 Forensic Analysis Events

**All JLAW execution phases shall be logged.**

| Event | Fields | Example |
|-------|--------|---------|
| **Analysis Started** | case_id, user, CIK, date_range, mode | `Analysis started for Nike (CIK 320187) 2019-01-01 to 2019-12-31 (strict mode)` |
| **Phase Execution** | phase_number, phase_name, status, duration | `Phase 4 (15-Node Analysis) completed (SUCCESS) in 12m 34s` |
| **Node Execution** | node_number, node_name, status, violations | `Node 1 (Form 4 Insider Trading) completed: 3 violations found` |
| **Detection Pattern** | pattern_name, result, confidence | `Options Backdating detection: 2 violations (confidence 92%)` |
| **AI Validation** | provider, model, result, timestamp | `OpenAI GPT-4 validation: fraud risk score 45/100` |
| **Phase Gate Failure** | phase_number, gate_name, threshold, actual | `Phase 2 gate failed: 60% filings acquired (threshold 80%)` |
| **Analysis Completed** | case_id, exit_code, total_violations, duration | `Analysis completed (EXIT CODE 0) with 12 violations in 45m 23s` |
| **Dossier Generated** | case_id, filename, hash, size | `Dossier generated: JLAW-320187-2019-dossier.pdf (SHA-256: b4c6d8e0...)` |

### 3.5 Configuration Changes

**All system configuration changes shall be logged.**

| Event | Fields | Example |
|-------|--------|---------|
| **Config Updated** | parameter, old_value, new_value, changed_by | `SEC_RATE_LIMIT changed from 6.0 to 8.0 by admin_john` |
| **API Key Rotated** | service, key_id, rotated_by, timestamp | `ANTHROPIC_API_KEY rotated by admin_john` |
| **Database Schema Change** | database, schema, change_type, changed_by | `PostgreSQL evidence table altered (ADD COLUMN case_status) by dba_alice` |
| **Firewall Rule Modified** | rule_id, action, source, destination, changed_by | `Firewall rule #42 modified (ALLOW 192.168.1.0/24 → 10.0.0.5:5432) by admin_john` |
| **User Created** | username, role, created_by, timestamp | `User analyst_bob created with role forensic_analyst by admin_john` |
| **User Deleted** | username, deleted_by, reason, timestamp | `User analyst_bob deleted by admin_john (termination)` |

### 3.6 Security Events

**All security-relevant events shall be logged and alerted.**

| Event | Fields | Alert Level | Example |
|-------|--------|-------------|---------|
| **Intrusion Attempt** | source_ip, timestamp, attack_type | 🚨 CRITICAL | `SQL injection attempt from 203.0.113.5` |
| **Malware Detected** | file_path, malware_type, timestamp | 🚨 CRITICAL | `Malware detected: /tmp/suspicious.exe (Trojan)` |
| **Port Scan** | source_ip, ports, timestamp | ⚠️ HIGH | `Port scan detected from 203.0.113.5 (ports 22-443)` |
| **DDoS Attack** | source_ips, request_rate, timestamp | 🚨 CRITICAL | `DDoS attack: 10,000 req/sec from botnet` |
| **Certificate Expiration** | certificate, expires_in_days | ⚠️ MEDIUM | `SSL certificate expires in 14 days` |
| **Patch Missing** | system, CVE, severity, days_overdue | ⚠️ HIGH | `CVE-2024-1234 patch missing (14 days overdue)` |

---

## IV. Log Protection and Integrity

### 4.1 Tamper-Evident Logs

**Requirement:** Audit logs shall be immutable and tamper-evident.

**Implementation:**
1. **Append-Only Storage:** Logs written to write-once file system (WORM) or append-only mode
2. **Log Signing:** Each log entry signed with HMAC-SHA256 (key rotated monthly)
3. **Merkle Tree:** Daily Merkle tree computed for all logs (root hash stored externally)
4. **Blockchain:** Optional: Log hashes submitted to public blockchain (Bitcoin, Ethereum)

**Log Entry Signature:**
```json
{
  "log_entry": { /* ... log data ... */ },
  "signature": "hmac-sha256(log_entry + previous_signature + timestamp)",
  "previous_signature": "[signature of previous log entry]",
  "sequence_number": 12345
}
```

### 4.2 Log Encryption

**At Rest:**
- All logs encrypted with AES-256-GCM
- Encryption keys stored in AWS KMS / Azure Key Vault
- Key rotation: Every 90 days

**In Transit:**
- SIEM forwarding over TLS 1.3
- Certificate pinning enforced
- Mutual TLS (mTLS) for high-security environments

### 4.3 Log Backup and Retention

**Backup Strategy:**
- **Real-Time:** Forwarded to SIEM (Splunk, ELK) immediately
- **Hourly:** Incremental backup to on-site NAS
- **Daily:** Full backup to off-site S3 / Azure Blob Storage
- **Weekly:** Backup to AWS Glacier / Azure Archive (long-term retention)

**Retention Schedule:**

| Log Type | Retention Period | Storage Tier | Deletion Method |
|----------|------------------|--------------|-----------------|
| Audit Logs | 7 years | Hot (0-90d) → Warm (90d-2y) → Cold (2y-7y) | Secure wipe (DOD 5220.22-M) |
| Security Logs | 2 years | Hot (0-90d) → Warm (90d-2y) | Secure wipe |
| Application Logs | 90 days | Hot only | Standard deletion |

---

## V. Log Monitoring and Alerting

### 5.1 Real-Time Monitoring

**SIEM Integration:**
- **Platform:** Splunk Enterprise / ELK Stack / AWS CloudWatch Logs
- **Ingestion Rate:** 10,000+ events per second
- **Search Latency:** < 5 seconds for last 24 hours
- **Dashboards:** Security Operations Center (SOC) dashboard, Executive dashboard

**Key Metrics:**
- Failed authentication rate (threshold: > 10/min)
- Evidence access anomalies (unusual times, volumes)
- Privilege escalation events (all reviewed)
- Critical error rate (threshold: > 5/min)

### 5.2 Alert Rules

| Alert | Condition | Severity | Action |
|-------|-----------|----------|--------|
| **Brute Force Attack** | 5 failed logins in 5 min (same user) | 🚨 CRITICAL | Lock account, notify security |
| **Evidence Tampering** | Evidence hash mismatch | 🚨 CRITICAL | Freeze evidence, escalate to CISO |
| **Privilege Escalation** | User role elevated to admin | ⚠️ HIGH | Notify security team, require approval |
| **Mass Data Download** | > 100 MB downloaded in 1 hour | ⚠️ MEDIUM | Notify manager, review user activity |
| **Off-Hours Access** | Admin access outside 9am-5pm | ℹ️ INFO | Log for review |
| **Unusual Geolocation** | Login from new country | ⚠️ MEDIUM | Challenge with additional MFA |

### 5.3 Incident Response Integration

**Alert Workflow:**
```
SIEM Alert Triggered
      ↓
[Automated Triage] (ML-based classification)
      ↓
Low Severity → Log for review
      ↓
Medium Severity → Create ticket, assign to analyst
      ↓
High Severity → Page on-call engineer, create incident
      ↓
Critical Severity → Escalate to CISO, activate incident response team
```

---

## VI. Log Analysis and Reporting

### 6.1 Automated Analysis

**Anomaly Detection:**
- Behavioral analysis (user behavior analytics - UBA)
- Statistical anomalies (standard deviations from baseline)
- Machine learning models (supervised + unsupervised)

**Example Anomalies:**
- User accessing evidence outside normal working hours
- Sudden spike in failed authentication attempts
- Unusual data transfer volumes
- Access patterns inconsistent with role

### 6.2 Compliance Reporting

**Monthly Reports:**
- Authentication summary (logins, failures, MFA usage)
- Access control decisions (granted, denied)
- Evidence chain integrity status
- Configuration changes
- Security incidents

**Annual SOC 2 Audit Report:**
- Comprehensive log review (samples)
- Control effectiveness validation
- Exception analysis
- Remediation tracking

### 6.3 Forensic Investigation

**Log Search Capabilities:**
- Full-text search (all fields)
- Time-range filtering
- User/resource correlation
- Chain-of-events reconstruction

**Example Queries:**
```
# Find all evidence access by user in time range
user:analyst_jane AND event_type:evidence_access AND timestamp:[2024-01-01 TO 2024-01-31]

# Find all failed authentication attempts
result:failure AND event_type:authentication

# Find all privilege escalations
event_type:privilege_escalation

# Reconstruct evidence chain for case
resource.id:case-123 AND (event_type:evidence_acquired OR event_type:evidence_accessed OR event_type:custody_transfer)
```

---

## VII. Log Quality Assurance

### 7.1 Log Completeness Testing

**Monthly Validation:**
- Verify all critical events are logged (sample 100 transactions)
- Check log forwarding to SIEM (100% delivery expected)
- Validate timestamp accuracy (NTP sync ± 100ms)
- Test log rotation and archival

### 7.2 Log Performance Testing

**Benchmarks:**
- Log write latency: < 10ms (p99)
- SIEM ingestion lag: < 5 seconds
- Search query performance: < 5 seconds (24 hours of data)
- Disk space utilization: < 80% (alerts at 75%)

---

## VIII. Compliance Mapping

### 8.1 SOC 2 Trust Services Criteria

| Criterion | Requirement | JLAW Implementation |
|-----------|-------------|---------------------|
| **CC7.2** | System generates audit logs | ✅ Comprehensive logging per Section III |
| **CC7.3** | System monitors security events | ✅ SIEM integration, real-time alerting |
| **CC7.4** | System responds to security incidents | ✅ Incident response integration |
| **A1.2** | System monitors availability | ✅ Performance metrics, uptime monitoring |

### 8.2 FRE 902(13)/(14) Compliance

**Evidence Chain Logging:**
- ✅ All evidence acquisition logged with timestamp
- ✅ Hash values logged at acquisition and verification
- ✅ Custody transfers logged with custodian signatures
- ✅ RFC 3161 timestamp tokens logged
- ✅ Merkle root computed and logged

---

## IX. Roles and Responsibilities

| Role | Responsibility |
|------|----------------|
| **CISO** | Overall policy ownership, compliance oversight |
| **Security Team** | SIEM monitoring, incident response, log analysis |
| **System Administrators** | Log infrastructure, storage, backup |
| **Forensic Analysts** | Generate audit events through JLAW usage |
| **Internal Audit** | Quarterly log review, compliance validation |
| **External Auditors** | Annual SOC 2 audit, log sampling |

---

## X. References

1. **SOC 2 Trust Services Criteria:** CC7.2, CC7.3, CC7.4, A1.2
2. **NIST SP 800-92:** Guide to Computer Security Log Management
3. **ISO 27001:2013:** A.12.4 (Logging and Monitoring)
4. **CIS Controls v8:** Control 8 (Audit Log Management)

---

**Policy Owner:** Chief Information Security Officer  
**Next Review Date:** December 2025  
**Compliance Framework:** SOC 2 Type II, FRE 902(13)/(14), ISO 27001  
