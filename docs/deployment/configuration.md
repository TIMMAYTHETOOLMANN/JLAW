# Configuration Reference

Complete reference for all JLAW configuration variables.

---

## Environment Variables

All configuration is managed through environment variables in the `.env` file.

### Core API Keys

#### SEC_USER_AGENT (Required)
**Purpose**: SEC EDGAR API access  
**Format**: `CompanyName/Version (email@domain.com)`  
**Example**: `JLAW/4.1.0 (forensics@company.com)`  
**Validation**: Must include company name and valid email  

#### OPENAI_API_KEY (Required)
**Purpose**: Primary AI validation  
**Format**: `sk-proj-...` or `sk-...`  
**Get key**: https://platform.openai.com/api-keys  

#### ANTHROPIC_API_KEY (Required)
**Purpose**: Secondary AI validation  
**Format**: `sk-ant-api03-...`  
**Get key**: https://console.anthropic.com/settings/keys  

### Optional API Keys

#### POLYGON_API_KEY
**Purpose**: Market correlation (Node 15)  
**Default**: None (Node 15 skipped if not set)  
**Get key**: https://polygon.io/dashboard/api-keys  

#### GOVINFO_API_KEY
**Purpose**: Live statutory citation validation  
**Default**: None (static references used)  
**Get key**: https://api.govinfo.gov/docs/  

### SEC EDGAR Configuration

#### SEC_RATE_LIMIT
**Purpose**: Requests per second to SEC API  
**Default**: `6.0`  
**Range**: 1-10 (SEC allows 10 max)  
**Recommendation**: 6-9 for reliability  

#### SEC_CACHE_ENABLED
**Purpose**: Enable persistent file-based cache  
**Default**: `true`  
**Values**: `true`, `false`  

#### SEC_CACHE_DIR
**Purpose**: Cache directory path  
**Default**: `.jlaw_cache/sec_edgar`  

#### SEC_STALE_CACHE_FALLBACK
**Purpose**: Use expired cache if fetch fails  
**Default**: `true` (crucial for reliability)  
**Values**: `true`, `false`  

### Database Configuration

#### Neo4j (Node 11 - Executive Networks)
```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j
```

#### TimescaleDB (Time-series metrics)
```bash
TIMESCALEDB_URI=postgresql://user:password@localhost:5432/jlaw_forensics
TIMESCALE_HOST=localhost
TIMESCALE_PORT=5432
TIMESCALE_DATABASE=jlaw_forensics
TIMESCALE_USER=jlaw
TIMESCALE_PASSWORD=your_password
```

#### Redis (Caching and rate limiting)
```bash
REDIS_URI=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_password
REDIS_DB=0
REDIS_MAX_CONNECTIONS=50
```

### Evidence Chain Configuration

#### RFC3161_TIMESTAMP_URL
**Purpose**: Timestamp authority for court-admissible evidence  
**Default**: `https://freetsa.org/tsr`  
**Alternatives**:
- DigiCert: `http://timestamp.digicert.com`
- GlobalSign: `http://timestamp.globalsign.com/scripts/timstamp.dll`
- Comodo: `http://timestamp.comodoca.com/rfc3161`

⚠️ **Warning**: Use network TSA (not `local`) for court-admissible evidence

### Logging Configuration

#### LOG_LEVEL
**Purpose**: Logging verbosity  
**Default**: `INFO`  
**Values**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`  

#### LOG_FORMAT
**Purpose**: Log output format  
**Default**: `text`  
**Values**:
- `text`: Human-readable (colored console)
- `json`: Structured JSON (for CloudWatch, Splunk, ELK)

#### LOG_FILE
**Purpose**: Operational log file path  
**Default**: `/var/log/jlaw/execution.log`  
**Fallback**: `logs/execution.log` (if /var/log not writable)  

#### AUDIT_LOG_FILE
**Purpose**: Audit log file path (separate from operational)  
**Default**: `/var/log/jlaw/audit.log`  
**Fallback**: `logs/audit.log`  

#### LOG_ROTATION_MAX_BYTES
**Purpose**: Max log file size before rotation  
**Default**: `104857600` (100MB)  

#### LOG_ROTATION_BACKUP_COUNT
**Purpose**: Number of backup log files to keep  
**Default**: `10`  

---

## Configuration Examples

### Minimal Configuration (Required Only)
```bash
SEC_USER_AGENT=MyCompany/1.0 (admin@company.com)
OPENAI_API_KEY=sk-proj-YOUR_KEY_HERE
ANTHROPIC_API_KEY=sk-ant-api03-YOUR_KEY_HERE
```

### Production Configuration
```bash
# Core APIs
SEC_USER_AGENT=MyCompany/1.0 (admin@company.com)
OPENAI_API_KEY=sk-proj-YOUR_KEY_HERE
ANTHROPIC_API_KEY=sk-ant-api03-YOUR_KEY_HERE
POLYGON_API_KEY=YOUR_POLYGON_KEY

# SEC Configuration
SEC_RATE_LIMIT=8.0
SEC_CACHE_ENABLED=true
SEC_STALE_CACHE_FALLBACK=true

# Databases
NEO4J_URI=bolt://neo4j.prod:7687
NEO4J_USER=jlaw_prod
NEO4J_PASSWORD=secure_password

REDIS_URI=redis://redis.prod:6379/0
REDIS_PASSWORD=secure_password

TIMESCALEDB_URI=postgresql://jlaw:secure_password@timescale.prod:5432/jlaw_forensics

# Evidence Chain
RFC3161_TIMESTAMP_URL=https://freetsa.org/tsr

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=/var/log/jlaw/execution.log
AUDIT_LOG_FILE=/var/log/jlaw/audit.log
```

### Development Configuration
```bash
# Core APIs
SEC_USER_AGENT=MyCompany-Dev/1.0 (dev@company.com)
OPENAI_API_KEY=sk-proj-DEV_KEY
ANTHROPIC_API_KEY=sk-ant-api03-DEV_KEY

# SEC Configuration
SEC_RATE_LIMIT=5.0  # More conservative for dev
SEC_CACHE_ENABLED=true

# Logging
LOG_LEVEL=DEBUG
LOG_FORMAT=text
LOG_FILE=logs/execution.log
AUDIT_LOG_FILE=logs/audit.log
```

---

## Validation

Validate configuration before running:

```bash
# Pre-flight check
python scripts/preflight_check.py --verbose

# CLI validation
python jlaw_cli.py --validate-only
```

---

## Next Steps

- **[Prerequisites](prerequisites.md)**: System requirements
- **[Docker Deployment](docker_deployment.md)**: Deploy with Docker
- **[Troubleshooting](troubleshooting.md)**: Common configuration issues
