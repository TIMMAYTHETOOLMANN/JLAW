# Access Control Policy

## SOC 2 Type II - Security Control Specification

**Document Version:** 1.0  
**Effective Date:** December 2024  
**Review Cycle:** Annual  
**Policy Owner:** Chief Information Security Officer (CISO)  
**Compliance Framework:** SOC 2 Trust Services Criteria - Security (CC6.1, CC6.2, CC6.3)  

---

## I. Purpose and Scope

### 1.1 Purpose

This Access Control Policy establishes the requirements for managing access to JLAW Forensic Analysis Platform resources, data, and systems to ensure:
- **Confidentiality:** Sensitive data accessible only to authorized personnel
- **Integrity:** Data cannot be modified by unauthorized parties
- **Availability:** Authorized users have timely access to required resources
- **Compliance:** SOC 2 Type II, FRE 902, and regulatory requirements met

### 1.2 Scope

This policy applies to:
- All JLAW system components (application, databases, infrastructure)
- All personnel (employees, contractors, third-party vendors)
- All data types (SEC filings, evidence chains, forensic dossiers, audit logs)
- All access methods (local, remote, API, database, file system)

---

## II. Access Control Principles

### 2.1 Principle of Least Privilege

**Policy:** Users shall be granted the minimum access rights necessary to perform their job functions.

**Implementation:**
- Default deny: No access unless explicitly granted
- Need-to-know basis: Access granted only for required data/systems
- Time-limited: Access rights expire and require periodic revalidation
- Just-in-time: Elevated privileges granted only when needed

### 2.2 Separation of Duties

**Policy:** Critical operations shall require multiple authorized individuals to prevent fraud and errors.

**Examples:**
- Evidence acquisition vs. evidence analysis (different roles)
- Dossier generation vs. dossier certification (different roles)
- Database administration vs. application administration (different roles)
- Security monitoring vs. incident response (oversight required)

### 2.3 Defense in Depth

**Policy:** Multiple layers of access controls shall be implemented.

**Layers:**
1. **Network:** Firewall, VPN, network segmentation
2. **System:** OS-level authentication and authorization
3. **Application:** JLAW role-based access control (RBAC)
4. **Data:** Encryption at rest, field-level access control
5. **Physical:** Badge access, visitor logs, camera surveillance

---

## III. Role-Based Access Control (RBAC) Matrix

### 3.1 JLAW System Roles

| Role | Description | Access Level |
|------|-------------|--------------|
| **System Administrator** | Full system access for maintenance | Root/Admin |
| **Lead Forensic Analyst** | Execute full analysis, generate dossiers | Read/Write Evidence |
| **Forensic Analyst** | Execute specific nodes, view results | Read Evidence, Write Analysis |
| **Data Custodian** | Manage evidence storage and integrity | Read Evidence, Manage Storage |
| **Legal Counsel** | Review dossiers and evidence | Read-Only |
| **Auditor** | Review audit logs and compliance | Read-Only (Logs) |
| **External Investigator** | Limited analysis on specific cases | Read Evidence (Case-Specific) |

### 3.2 Access Control Matrix

| Resource | System Admin | Lead Analyst | Analyst | Custodian | Legal | Auditor |
|----------|--------------|--------------|---------|-----------|-------|---------|
| **SEC EDGAR API** | ✅ Configure | ✅ Execute | ✅ Execute | ❌ | ❌ | ❌ |
| **Evidence Storage** | ✅ Full | ✅ Read/Write | ✅ Read | ✅ Manage | ✅ Read | ❌ |
| **Forensic Analysis** | ✅ Full | ✅ Execute | ✅ Execute | ❌ | ❌ | ❌ |
| **Dossier Generation** | ✅ Full | ✅ Generate | ❌ | ❌ | ✅ Read | ❌ |
| **Audit Logs** | ✅ Full | ✅ Read | ✅ Read | ✅ Read | ✅ Read | ✅ Full |
| **System Configuration** | ✅ Full | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Database Access** | ✅ Full | ✅ Read/Write | ✅ Read | ✅ Backup | ❌ | ✅ Read |
| **API Keys/Secrets** | ✅ Full | ❌ | ❌ | ❌ | ❌ | ❌ |

### 3.3 Privileged Access Management (PAM)

**Super User Access:**
- **Root/Administrator:** Break-glass access only, logged and monitored
- **Database SA:** Emergency use only, requires approval
- **API Keys:** Stored in secrets manager (AWS Secrets Manager, HashiCorp Vault)

**Approval Workflow:**
```
User Request → Manager Approval → Security Review → Access Granted (Time-Limited)
```

---

## IV. Authentication Requirements

### 4.1 Multi-Factor Authentication (MFA)

**Policy:** All user accounts shall require MFA for authentication.

**MFA Methods (at least 2 required):**
1. **Something you know:** Password/passphrase
2. **Something you have:** Hardware token (YubiKey), mobile app (Duo, Google Authenticator)
3. **Something you are:** Biometric (fingerprint, facial recognition)

**Exceptions:** Service accounts (API-to-API) use certificate-based authentication

### 4.2 Password Requirements

**Complexity:**
- Minimum length: 16 characters (20+ for admin accounts)
- Character classes: Uppercase, lowercase, numbers, special characters
- No dictionary words or common patterns
- No reuse of last 12 passwords

**Expiration:**
- User accounts: 90 days
- Admin accounts: 60 days
- Service accounts: Never (rotate on compromise)

**Storage:**
- Hashed with bcrypt (work factor 12+)
- Salted (unique per password)
- Never stored in plaintext

### 4.3 Session Management

**Session Timeout:**
- Active session: 30 minutes inactivity
- Maximum session: 8 hours
- Re-authentication required after timeout

**Session Security:**
- Secure session tokens (cryptographically random, 256-bit)
- HTTPOnly and Secure flags on cookies
- CSRF protection enabled
- Session fixation prevention

---

## V. Authorization and Permissions

### 5.1 File System Permissions

**Evidence Directory (`/evidence/`):**
```bash
drwxr-x--- root jlaw_evidence 755
```
- Owner: root (system administrator)
- Group: jlaw_evidence (authorized analysts)
- Permissions: Read/Execute for group, no world access

**Dossier Directory (`/reports/`):**
```bash
drwxr-x--- root jlaw_reports 755
```

**Audit Logs (`/var/log/jlaw/`):**
```bash
drwx------ root root 700
```
- Owner: root only
- No group or world access (immutable logs)

### 5.2 Database Access Control

**PostgreSQL (Evidence Storage):**
```sql
-- Role: jlaw_analyst (Read/Write Evidence)
GRANT SELECT, INSERT, UPDATE ON evidence.* TO jlaw_analyst;
REVOKE DELETE ON evidence.* FROM jlaw_analyst;

-- Role: jlaw_legal (Read-Only)
GRANT SELECT ON evidence.*, dossier.* TO jlaw_legal;

-- Role: jlaw_auditor (Logs Only)
GRANT SELECT ON audit_logs.* TO jlaw_auditor;
```

**Neo4j (Graph Database):**
- Use role-based access control (RBAC) in Neo4j Enterprise
- Analysts: Read/Write on case-specific subgraphs
- Legal: Read-only on entire database

**Redis (Caching):**
- Authentication required (password-protected)
- No external network access (localhost only)

### 5.3 API Access Control

**API Key Management:**
- One key per user/service account
- Key rotation: Every 90 days
- Key scope: Minimum required permissions
- Key revocation: Immediate on compromise or role change

**Rate Limiting:**
- Authenticated users: 1000 requests/hour
- Service accounts: 10,000 requests/hour
- Unauthenticated: 100 requests/hour (SEC EDGAR compliance)

---

## VI. Account Lifecycle Management

### 6.1 Account Provisioning

**New Employee Process:**
1. HR notification of new hire (Role, Start Date)
2. Manager submits access request form
3. Security reviews request (Least Privilege)
4. IT creates account with MFA enrollment
5. Training completed before access granted
6. Access logged in audit trail

**Required Training:**
- JLAW system overview (2 hours)
- Evidence handling procedures (1 hour)
- Security awareness (annual refresher)
- Compliance requirements (FRE 902, SOC 2)

### 6.2 Account Modification

**Role Change Process:**
1. Manager submits role change request
2. Security reviews new role requirements
3. Old permissions revoked
4. New permissions granted (least privilege)
5. User notified of change
6. Change logged in audit trail

### 6.3 Account Deprovisioning

**Termination Process:**
```
Employee Separation Notice (HR)
    ↓
Immediate: Disable all accounts
    ↓
Within 24 hours: Revoke all access (systems, badges, VPN)
    ↓
Within 7 days: Delete accounts (after data ownership transfer)
    ↓
Audit log review (detect any unauthorized access)
```

**Exit Interview:**
- Return all company property (laptop, tokens, badges)
- Sign confidentiality reminder
- Acknowledge access termination

### 6.4 Account Review and Recertification

**Quarterly Access Review:**
- All accounts reviewed by managers
- Verify access still required
- Remove unnecessary permissions
- Document review in compliance log

**Annual Recertification:**
- All privileged accounts recertified
- Business justification required
- Non-compliance results in immediate revocation

---

## VII. Remote Access

### 7.1 VPN Requirements

**Policy:** All remote access shall use company VPN.

**VPN Configuration:**
- Strong encryption: AES-256, SHA-256 HMAC
- Perfect Forward Secrecy (PFS) enabled
- Split tunneling: Disabled (all traffic through VPN)
- MFA required for VPN connection
- Session timeout: 8 hours maximum

### 7.2 Remote Desktop / SSH

**Policy:** Remote desktop and SSH shall require MFA and be logged.

**SSH Hardening:**
- Password authentication: Disabled
- Public key authentication: Required (RSA 4096-bit or Ed25519)
- Root login: Disabled
- SSH protocol: Version 2 only
- Port: Non-standard (security through obscurity, not relied upon)

**Bastion Host:**
- All SSH connections through bastion host
- Bastion logs all commands executed
- Bastion enforces MFA and time-based access

---

## VIII. Third-Party Access

### 8.1 Vendor Access Policy

**Policy:** Third-party vendors shall have time-limited, audited access.

**Vendor Access Workflow:**
1. Business justification (scope, duration, data access)
2. Security review (vendor security assessment)
3. Signed NDA and security agreement
4. Temporary account created (expires automatically)
5. Access logged and monitored in real-time
6. Exit: Account deleted, access reviewed

### 8.2 Vendor Security Requirements

**Mandatory Requirements:**
- SOC 2 Type II certification (if applicable)
- Background checks for vendor personnel
- MFA for all vendor accounts
- VPN access only (no direct internet exposure)
- Separate vendor network segment (VLAN)

---

## IX. Monitoring and Auditing

### 9.1 Access Logging

**Logged Events:**
- Authentication attempts (success and failure)
- Authorization decisions (granted and denied)
- Privileged operations (sudo, database admin, API key access)
- Evidence access (view, download, modify)
- Configuration changes (system, firewall, database)
- Account changes (create, modify, delete)

**Log Format:**
```json
{
  "timestamp": "2024-12-29T10:15:30.123Z",
  "event_type": "authentication",
  "user": "analyst_jane_doe",
  "result": "success",
  "mfa_method": "yubikey",
  "source_ip": "192.168.1.100",
  "session_id": "a3f5b8c9...",
  "resource": "jlaw_app",
  "action": "login"
}
```

### 9.2 Real-Time Alerting

**Alert Triggers:**
- ❗ Multiple failed authentication attempts (5 in 5 minutes)
- ❗ Privileged account access outside business hours
- ❗ Access from unusual geolocation
- ❗ Mass data download (> 100 MB in 1 hour)
- ❗ Configuration change without change ticket
- ❗ Evidence file modification (hash mismatch)

**Alert Channels:**
- SIEM dashboard (Splunk, ELK)
- Email to security team
- SMS to on-call engineer (critical alerts)
- PagerDuty escalation (if not acknowledged in 15 minutes)

### 9.3 Log Retention and Protection

**Retention Period:**
- Audit logs: 7 years (legal requirement)
- Security logs: 2 years
- System logs: 90 days

**Log Protection:**
- Write-once storage (WORM) or append-only
- Encrypted at rest (AES-256)
- Forwarded to SIEM in real-time
- Off-site backup (daily)
- Integrity monitoring (hash verification)

---

## X. Compliance and Enforcement

### 10.1 Policy Violations

**Violation Examples:**
- Sharing passwords or MFA tokens
- Accessing data outside authorized scope
- Failing to log out after session
- Bypassing access controls
- Unauthorized privilege escalation

**Disciplinary Actions:**
1. **First Violation:** Written warning, security training
2. **Second Violation:** Access suspension (14 days), manager review
3. **Third Violation:** Termination of employment
4. **Criminal Activity:** Immediate termination, law enforcement referral

### 10.2 Exception Process

**Policy:** Exceptions to this policy require CISO approval.

**Exception Request:**
1. Submit formal exception request (business justification)
2. Risk assessment (likelihood, impact, mitigation)
3. Compensating controls (if applicable)
4. CISO approval or denial (documented)
5. Exception expiration date (maximum 1 year)

---

## XI. Policy Review and Updates

### 11.1 Annual Review

**Policy Review:**
- Conducted annually by CISO and Security Team
- Updated for new threats, technologies, regulations
- Approved by executive management
- Communicated to all personnel

### 11.2 Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-12-29 | CISO | Initial policy creation |

---

## XII. Acknowledgment

I acknowledge that I have read, understood, and agree to comply with this Access Control Policy. I understand that violation of this policy may result in disciplinary action, up to and including termination of employment.

**Employee Signature:** ___________________________  
**Print Name:** [Full Name]  
**Date:** [YYYY-MM-DD]  

---

## XIII. References

1. **SOC 2 Trust Services Criteria:** CC6.1, CC6.2, CC6.3 (Logical and Physical Access Controls)
2. **NIST SP 800-53:** AC Family (Access Control)
3. **CIS Controls v8:** Control 6 (Access Control Management)
4. **ISO 27001:2013:** A.9 (Access Control)

---

**Policy Owner:** Chief Information Security Officer  
**Next Review Date:** December 2025  
**Compliance Framework:** SOC 2 Type II, FRE 902(13)/(14), ISO 27001  
