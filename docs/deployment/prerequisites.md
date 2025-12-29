# Prerequisites

System requirements and dependencies for JLAW deployment.

---

## System Requirements

### Minimum Requirements

| Component | Requirement | Notes |
|-----------|-------------|-------|
| **Python** | 3.10+ | Required (3.11+ recommended) |
| **RAM** | 16 GB | Minimum for analysis |
| **Storage** | 50 GB | For SEC filing cache |
| **CPU** | 4 cores | Multi-core for parallel processing |
| **OS** | Linux/macOS/Windows | Production: Linux recommended |

### Recommended Requirements

| Component | Requirement | Notes |
|-----------|-------------|-------|
| **Python** | 3.11 or 3.12 | Best performance |
| **RAM** | 32 GB | For large batch processing |
| **Storage** | 100+ GB | For extensive cache |
| **CPU** | 8+ cores | Faster parallel execution |
| **OS** | Ubuntu 22.04 LTS | Production standard |

---

## Required Services

### Core Services (Required)

#### 1. SEC EDGAR API Access

**Purpose**: Download SEC filings
**Cost**: Free
**Requirements**:
- Valid User-Agent header with organization name and contact email
- Respect rate limits (10 req/sec max)

**Configuration**:
```bash
SEC_USER_AGENT=YourCompany/1.0 (your-email@company.com)
```

**Documentation**: [SEC API Setup](../SEC_API_SETUP.md)

---

#### 2. OpenAI API

**Purpose**: Primary AI validation
**Cost**: Pay-per-use
**Requirements**:
- Active OpenAI account
- API key with GPT-4 access

**Configuration**:
```bash
OPENAI_API_KEY=sk-proj-YOUR_KEY_HERE
```

**Get API Key**: [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)

---

#### 3. Anthropic API

**Purpose**: Secondary AI validation
**Cost**: Pay-per-use
**Requirements**:
- Active Anthropic account
- API key with Claude 3 access

**Configuration**:
```bash
ANTHROPIC_API_KEY=sk-ant-api03-YOUR_KEY_HERE
```

**Get API Key**: [https://console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys)

---

### Optional Services (Enhanced Features)

#### 4. Neo4j Graph Database

**Purpose**: Executive network analysis (Node 11)
**Cost**: Free (Community Edition) or Paid (Enterprise)
**Requirements**:
- Neo4j 5.15+ installed
- Network accessible
- Authentication configured

**Configuration**:
```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=YOUR_PASSWORD
```

**Installation**:
```bash
# Docker
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5.15

# Or via package manager
# Ubuntu/Debian
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable latest' | sudo tee /etc/apt/sources.list.d/neo4j.list
sudo apt update
sudo apt install neo4j
```

**Skip if unavailable**: Node 11 will be skipped

---

#### 5. Redis

**Purpose**: Rate limiting and caching
**Cost**: Free (Open Source)
**Requirements**:
- Redis 6.0+ installed
- Network accessible

**Configuration**:
```bash
REDIS_URI=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=YOUR_PASSWORD
```

**Installation**:
```bash
# Docker
docker run -d \
  --name redis \
  -p 6379:6379 \
  redis:7-alpine

# Or via package manager
# Ubuntu/Debian
sudo apt update
sudo apt install redis-server
```

**Skip if unavailable**: In-memory caching will be used

---

#### 6. TimescaleDB

**Purpose**: Time-series financial metrics
**Cost**: Free (Open Source)
**Requirements**:
- PostgreSQL 14+ with TimescaleDB extension
- Network accessible

**Configuration**:
```bash
TIMESCALEDB_URI=postgresql://jlaw:password@localhost:5432/jlaw_forensics
TIMESCALE_HOST=localhost
TIMESCALE_PORT=5432
TIMESCALE_DATABASE=jlaw_forensics
TIMESCALE_USER=jlaw
TIMESCALE_PASSWORD=YOUR_PASSWORD
```

**Installation**:
```bash
# Docker
docker run -d \
  --name timescaledb \
  -p 5432:5432 \
  -e POSTGRES_PASSWORD=password \
  timescale/timescaledb:latest-pg15

# Or follow official guide
# https://docs.timescale.com/install/latest/
```

**Skip if unavailable**: Time-series features disabled

---

#### 7. Polygon.io API

**Purpose**: Market correlation analysis (Node 15)
**Cost**: Free tier available, paid plans for more features
**Requirements**:
- Active Polygon.io account
- API key

**Configuration**:
```bash
POLYGON_API_KEY=YOUR_POLYGON_API_KEY
```

**Get API Key**: [https://polygon.io/dashboard/api-keys](https://polygon.io/dashboard/api-keys)

**Skip if unavailable**: Node 15 will be skipped

---

## Python Dependencies

### Core Dependencies

```bash
# Install from requirements.txt
pip install -r requirements.txt

# Or with optional dependencies
pip install -e ".[dev,viz,docs]"
```

### Key Packages

| Package | Purpose | Version |
|---------|---------|---------|
| `aiohttp` | Async HTTP client | >=3.9.0 |
| `beautifulsoup4` | HTML parsing | >=4.12.0 |
| `pandas` | Data analysis | >=2.0.0 |
| `numpy` | Numerical computing | >=1.26.0 |
| `cryptography` | Evidence chain | >=41.0.0 |
| `rfc3161ng` | Timestamps | >=2.1.0 |
| `neo4j` | Graph database | >=5.15.0 |
| `redis` | Caching | >=5.0.0 |
| `asyncpg` | PostgreSQL async | >=0.29.0 |

---

## Network Requirements

### Outbound Access Required

| Service | Endpoint | Purpose |
|---------|----------|---------|
| SEC EDGAR | `www.sec.gov` | Filing downloads |
| OpenAI | `api.openai.com` | AI validation |
| Anthropic | `api.anthropic.com` | AI validation |
| FreeTSA | `freetsa.org` | Timestamps |
| Polygon.io | `api.polygon.io` | Market data (optional) |

### Firewall Rules

```bash
# Allow outbound HTTPS
iptables -A OUTPUT -p tcp --dport 443 -j ACCEPT

# Allow outbound HTTP (some SEC URLs use HTTP)
iptables -A OUTPUT -p tcp --dport 80 -j ACCEPT
```

---

## Storage Requirements

### Disk Space

| Component | Size | Purpose |
|-----------|------|---------|
| Python packages | ~5 GB | Dependencies |
| SEC filing cache | 10-50 GB | Downloaded filings |
| ML model cache | 5-10 GB | Pre-trained models |
| Logs | 1-5 GB | Operational/audit logs |
| Output dossiers | 1-10 GB | Analysis results |

**Total**: 22-80 GB depending on usage

### Cache Directories

```bash
# Create cache directories
mkdir -p ~/.jlaw_cache/{sec_edgar,ml_models}
mkdir -p /var/log/jlaw
mkdir -p output
```

---

## Security Considerations

### API Key Management

✅ **Best Practices**:
- Store API keys in `.env` file (not committed to git)
- Use environment variables in production
- Rotate keys periodically
- Use separate keys for dev/staging/prod

❌ **Never**:
- Commit `.env` to git
- Share API keys via email/chat
- Use production keys in development
- Store keys in code

### Network Security

✅ **Recommended**:
- Use HTTPS for all API calls
- Validate SSL certificates
- Use VPN for production deployments
- Implement rate limiting

### Database Security

✅ **Recommended**:
- Use strong passwords
- Enable authentication
- Use TLS/SSL connections
- Restrict network access

---

## Pre-Flight Validation

Before running JLAW, verify all prerequisites:

```bash
# Run pre-flight check
python scripts/preflight_check.py --verbose

# Or use CLI validation
python jlaw_cli.py --validate-only
```

Expected output:
```
✓ Environment Variables: Loaded 15 variables
✓ SEC User-Agent: Valid
✓ SEC API Connectivity: Accessible
✓ OpenAI API: Valid and accessible
✓ Anthropic API: Valid and accessible
⚠ Polygon API: Not configured (optional)
⚠ Neo4j: Not configured (optional)
⚠ Redis: Not configured (optional)
⚠ TimescaleDB: Not configured (optional)
✓ RFC 3161 TSA: Accessible
⚠ ML Model Cache: No models cached

✓ ALL CHECKS PASSED - READY FOR FORENSIC ANALYSIS
```

---

## Next Steps

- **[Configuration](configuration.md)**: Configure environment variables
- **[Docker Deployment](docker_deployment.md)**: Deploy with Docker
- **[Troubleshooting](troubleshooting.md)**: Common issues
- **[Quick Start](../quickstart.md)**: First analysis
