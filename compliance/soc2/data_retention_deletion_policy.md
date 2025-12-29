# Data Retention and Deletion Policy

## SOC 2 Type II - Data Lifecycle Management

**Document Version:** 1.0  
**Effective Date:** December 2024  
**Review Cycle:** Annual  
**Policy Owner:** Chief Information Security Officer (CISO)  
**Compliance Framework:** SOC 2, GDPR, CCPA, FRE 902  

---

## I. Purpose and Scope

### 1.1 Purpose

This Data Retention and Deletion Policy establishes requirements for:
- **Retention:** How long data is retained
- **Storage:** Where and how data is stored
- **Deletion:** When and how data is securely deleted
- **Compliance:** Meeting legal and regulatory obligations

### 1.2 Scope

This policy applies to:
- All JLAW system data (evidence, analysis results, logs)
- All storage systems (PostgreSQL, Neo4j, Redis, file systems)
- All data types (structured, unstructured, backups)
- All data lifecycle stages (active, archived, deleted)

---

## II. Data Classification

### 2.1 Data Categories

| Category | Description | Examples |
|----------|-------------|----------|
| **Evidence Data** | SEC filings and forensic evidence | 10-K, 10-Q, Form 4, 8-K, 13F, DEF 14A |
| **Analysis Results** | JLAW forensic analysis output | Node results, detection patterns, dossiers |
| **Audit Logs** | Security and compliance logs | Authentication, access, custody chain |
| **System Data** | Application and infrastructure data | Configuration, backups, temp files |
| **Personal Data** | Personally identifiable information (PII) | User accounts, contact info, IP addresses |

### 2.2 Data Sensitivity Levels

| Level | Description | Examples |
|-------|-------------|----------|
| **Public** | Publicly available data | SEC EDGAR filings, public company info |
| **Internal** | Company proprietary data | JLAW analysis algorithms, internal docs |
| **Confidential** | Sensitive business data | Client cases, forensic findings |
| **Highly Confidential** | Legal/regulated data | Evidence under protective order, PII |

---

## III. Retention Schedules

### 3.1 Evidence Data (7 Years)

**Retention Period:** 7 years from case closure  
**Justification:** Legal requirements (statute of limitations), FRE 902 compliance

| Data Type | Retention | Storage Tier | Rationale |
|-----------|-----------|--------------|-----------|
| **SEC Filings** | 7 years | Hot (0-1y) → Warm (1-3y) → Cold (3-7y) | Evidence for legal proceedings |
| **Evidence Chain** | 7 years | Hot (all) | Chain of custody records (legal requirement) |
| **Dossiers (PDF)** | 7 years | Hot (0-1y) → Warm (1-7y) | Forensic analysis reports |
| **Analysis Data (JSON)** | 7 years | Hot (0-1y) → Warm (1-7y) | Structured evidence data |

**Triggering Event:** Case closure date (final dossier delivery)

### 3.2 Audit Logs (7 Years)

**Retention Period:** 7 years from log entry  
**Justification:** SOC 2, regulatory compliance, legal discovery

| Log Type | Retention | Storage Tier | Rationale |
|----------|-----------|--------------|-----------|
| **Security Logs** | 7 years | Hot (0-90d) → Warm (90d-2y) → Cold (2-7y) | Incident investigation, compliance |
| **Access Logs** | 7 years | Hot (0-90d) → Warm (90d-2y) → Cold (2-7y) | Audit trail, compliance |
| **Custody Logs** | 7 years | Hot (all) | Evidence chain (legal requirement) |
| **System Logs** | 90 days | Hot only | Operational troubleshooting |

### 3.3 System Data (Variable)

| Data Type | Retention | Rationale |
|-----------|-----------|-----------|
| **Configuration** | Until superseded + 1 year | Change history, rollback capability |
| **Backups** | 90 days (incremental), 1 year (full) | Disaster recovery, operational restore |
| **Temp Files** | 7 days | Working files, cache |
| **Session Data** | 24 hours | User sessions (Redis) |

### 3.4 Personal Data (GDPR/CCPA)

**Retention Period:** As long as necessary for business purpose, or per user request

| Data Type | Retention | Rationale |
|-----------|-----------|-----------|
| **User Accounts (Active)** | While employed/contracted | Access control, audit trail |
| **User Accounts (Terminated)** | 90 days after termination | Final audit, knowledge transfer |
| **User Activity Logs** | 7 years | Audit trail, compliance |
| **User PII** | Per data subject request (GDPR) | Privacy rights (right to erasure) |

---

## IV. Storage Tiers

### 4.1 Hot Storage (Active)

**Characteristics:**
- Frequent access (daily)
- Low latency (< 100ms)
- High cost
- Full indexing and search

**Technologies:**
- SSD RAID arrays
- PostgreSQL (online database)
- Redis (cache)
- Local file systems

**Use Cases:**
- Current cases (0-1 year)
- Active audit logs (0-90 days)
- User sessions and temp data

### 4.2 Warm Storage (Infrequent Access)

**Characteristics:**
- Infrequent access (monthly)
- Medium latency (< 5 seconds)
- Medium cost
- Limited indexing

**Technologies:**
- HDD RAID arrays
- AWS S3 Standard-IA
- Azure Cool Blob Storage
- Compressed archives

**Use Cases:**
- Closed cases (1-3 years)
- Historical audit logs (90 days - 2 years)
- Archived configurations

### 4.3 Cold Storage (Archival)

**Characteristics:**
- Rare access (annually or never)
- High latency (minutes to hours)
- Low cost
- No indexing (restore required)

**Technologies:**
- AWS S3 Glacier / Glacier Deep Archive
- Azure Archive Storage
- Tape backup (offline)

**Use Cases:**
- Closed cases (3-7 years)
- Historical audit logs (2-7 years)
- Long-term compliance archives

---

## V. Data Deletion

### 5.1 Secure Deletion Standards

**Standard:** DOD 5220.22-M (3-pass overwrite)

**Method:**
1. **Pass 1:** Overwrite with character (0x00)
2. **Pass 2:** Overwrite with complement (0xFF)
3. **Pass 3:** Overwrite with random character
4. **Verify:** Read back and confirm overwrite

**Tools:**
- **Linux:** `shred -vfz -n 3 <file>`
- **Windows:** `cipher /w` or SDelete (Sysinternals)
- **Database:** `VACUUM FULL` (PostgreSQL), physical file deletion

### 5.2 Deletion Procedures

#### 5.2.1 Evidence Data Deletion (After 7 Years)

**Trigger:** 7 years from case closure date

**Procedure:**
```
1. Review legal hold status (confirm no ongoing litigation)
2. Generate deletion certificate (list of items to delete)
3. Obtain approval (Legal Counsel + CISO)
4. Execute secure deletion (DOD 5220.22-M)
5. Verify deletion (file system check)
6. Document deletion (audit log entry)
7. Update inventory (remove from catalog)
```

**Approval Required:** Legal Counsel (mandatory), CISO (mandatory)

#### 5.2.2 Audit Log Deletion (After 7 Years)

**Trigger:** 7 years from log entry date

**Procedure:**
```
1. Export logs to long-term archive (if not already archived)
2. Generate deletion list (logs older than 7 years)
3. Obtain approval (CISO)
4. Execute secure deletion (overwrite or crypto-shred)
5. Verify deletion
6. Document deletion (meta-audit log)
```

**Approval Required:** CISO

#### 5.2.3 User Data Deletion (GDPR Right to Erasure)

**Trigger:** User data subject access request (DSAR)

**Procedure:**
```
1. Receive DSAR (email to privacy@jlaw.forensics)
2. Verify identity (multi-factor verification)
3. Assess legal basis for retention (employment, contract, legal hold)
4. If deletion allowed:
   a. Identify all systems containing user data
   b. Generate deletion list
   c. Obtain approval (Legal Counsel + Privacy Officer)
   d. Execute secure deletion across all systems
   e. Verify deletion
   f. Respond to user within 30 days (GDPR requirement)
5. If deletion not allowed:
   a. Provide explanation to user (legal basis)
   b. Document decision (privacy log)
```

**Response Time:** 30 days (GDPR requirement)

#### 5.2.4 Backup Data Deletion

**Trigger:** Backup retention period expired

**Procedure:**
```
1. Identify expired backups (90 days for incremental, 1 year for full)
2. Verify no restore needed (check open restore requests)
3. Execute deletion (overwrite backup media or crypto-shred)
4. Update backup catalog
5. Document deletion (backup log)
```

**Special Case:** If backup contains evidence under legal hold, preserve until hold lifted

---

## VI. Legal Hold Process

### 6.1 Legal Hold Overview

A **legal hold** (litigation hold) suspends normal retention and deletion policies to preserve evidence for legal proceedings.

### 6.2 Legal Hold Procedure

**Triggering Events:**
- Lawsuit filed or threatened
- Government investigation initiated
- Regulatory inquiry received
- Internal investigation requiring evidence preservation

**Procedure:**
```
1. Legal Counsel issues legal hold notice
2. IT identifies systems and data in scope
3. IT suspends deletion for in-scope data
4. IT notifies custodians (users who own data)
5. Custodians acknowledge hold (signed confirmation)
6. IT monitors compliance (monthly review)
7. Legal Counsel lifts hold when resolved
8. IT resumes normal retention/deletion
```

**Documentation:**
- Legal hold notice (date, scope, custodians)
- Custodian acknowledgments
- Compliance reports (monthly)
- Hold release notice

### 6.3 Legal Hold Compliance

**Penalties for Non-Compliance:**
- Spoliation of evidence (court sanctions)
- Adverse inference instruction (jury assumes deleted data was unfavorable)
- Monetary sanctions (fines)
- Disciplinary action (employee termination)

---

## VII. Data Portability (GDPR Article 20)

### 7.1 Data Portability Rights

Users have the right to:
- Receive their personal data in structured, machine-readable format (JSON, CSV)
- Transmit their data to another controller

### 7.2 Data Portability Procedure

**Trigger:** User data portability request

**Procedure:**
```
1. Receive request (email to privacy@jlaw.forensics)
2. Verify identity
3. Extract user data (PostgreSQL, Neo4j, logs)
4. Format as JSON or CSV (user preference)
5. Deliver securely (encrypted email or secure download)
6. Document request (privacy log)
```

**Response Time:** 30 days (GDPR requirement)

**Export Format:**
```json
{
  "user_id": "user_123",
  "username": "analyst_jane_doe",
  "email": "jane.doe@example.com",
  "created_date": "2023-01-15T10:00:00Z",
  "last_login": "2024-12-29T14:30:00Z",
  "cases_accessed": [
    {"case_id": "CASE-2024-0001", "accessed_date": "2024-12-01"}
  ],
  "audit_log": [
    {"timestamp": "2024-12-29T10:15:30Z", "action": "login", "result": "success"}
  ]
}
```

---

## VIII. Retention Exceptions

### 8.1 Exception Process

**Policy:** Exceptions to retention schedules require CISO approval.

**Valid Reasons for Extension:**
- Ongoing litigation (legal hold)
- Regulatory investigation
- Business continuity requirement
- Technical limitation (system migration)

**Exception Request:**
1. Submit exception request (business justification)
2. Specify extended retention period (maximum)
3. Obtain approval (CISO + Legal Counsel if legal hold)
4. Document exception (retention exception log)
5. Set expiration reminder

### 8.2 Exception Review

**Frequency:** Quarterly  
**Reviewer:** CISO  
**Action:** Confirm exception still valid or release data for deletion

---

## IX. Compliance and Monitoring

### 9.1 Retention Compliance Monitoring

**Automated Monitoring:**
- Daily scan for data past retention period
- Weekly report of deletion-eligible data
- Monthly deletion execution
- Quarterly retention audit

**Alerts:**
- Data approaching retention expiration (30 days before)
- Data past retention period (immediate alert)
- Failed deletion attempts (immediate alert)
- Legal hold violations (immediate critical alert)

### 9.2 Metrics and KPIs

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Deletion Accuracy** | 100% | Data deleted matches deletion list |
| **Deletion Timeliness** | Within 30 days of retention expiration | Average days past retention |
| **Legal Hold Compliance** | 100% | No spoliation incidents |
| **GDPR Response Time** | < 30 days | Average days to respond to DSAR |

---

## X. Roles and Responsibilities

| Role | Responsibility |
|------|----------------|
| **CISO** | Policy ownership, exception approval, compliance oversight |
| **Legal Counsel** | Legal hold decisions, GDPR interpretation, exception approval (legal) |
| **Privacy Officer** | GDPR/CCPA compliance, DSAR processing |
| **IT Operations** | Deletion execution, backup management, monitoring |
| **Data Custodians** | Legal hold compliance, data classification |
| **Internal Audit** | Quarterly compliance review, retention audit |

---

## XI. References

1. **SOC 2 Trust Services Criteria:** PI1.5 (Data Retention and Disposal)
2. **GDPR:** Article 5(1)(e) (Storage Limitation), Article 17 (Right to Erasure), Article 20 (Data Portability)
3. **CCPA:** Section 1798.105 (Right to Delete)
4. **DOD 5220.22-M:** Data Sanitization Standard
5. **NIST SP 800-88:** Guidelines for Media Sanitization
6. **ISO 27001:2013:** A.11.2.7 (Secure Disposal of Media)

---

## XII. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-12-29 | CISO | Initial policy creation |

---

**Policy Owner:** Chief Information Security Officer  
**Next Review Date:** December 2025  
**Compliance Framework:** SOC 2 Type II, GDPR, CCPA, FRE 902  
