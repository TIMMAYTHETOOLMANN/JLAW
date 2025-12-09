# VoltAgent Subagent Integration Guide

## Overview

The JLAW forensic analysis platform now includes specialized VoltAgent Claude Code subagents for enhanced multi-agent orchestration. These subagents provide domain-specific expertise in forensic analysis, infrastructure management, and development tasks.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│               JLAW Forensic Platform                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │     Forensic Workflow Orchestrator                  │    │
│  │  (Master coordinator for forensic investigations)   │    │
│  └────────────────────────────────────────────────────┘    │
│                          ↓                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Multi-Agent Coordinator & Context Manager          │   │
│  │  (Task routing and state management)                │   │
│  └─────────────────────────────────────────────────────┘   │
│          ↓              ↓              ↓              ↓      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Forensic │  │ Forensic │  │ Forensic │  │ Forensic │   │
│  │   NLP    │  │ Financial│  │ Research │  │Compliance│   │
│  │ Analyst  │  │ Analyst  │  │Specialist│  │ Auditor  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                                                              │
│  Infrastructure Support:                                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  DevOps  │  │ Security │  │ Database │  │  Cloud   │   │
│  │ Engineer │  │ Engineer │  │   Admin  │  │Architect │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                                                              │
│  Development Support:                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │  Python  │  │ Backend  │  │   Docs   │                 │
│  │   Pro    │  │Developer │  │ Engineer │                 │
│  └──────────┘  └──────────┘  └──────────┘                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Subagent Categories

### 1. Forensic Subagents (`.claude/agents/forensic/`)

Specialized agents for forensic analysis of SEC filings and financial fraud detection.

#### forensic-nlp-analyst
- **Purpose**: Natural language processing for contradiction detection and linguistic analysis
- **Tools**: Read, Write, Edit, Bash, Glob, Grep
- **Integration**: 
  - `src/forensics/enhanced_contradiction_detector.py`
  - `src/forensics/linguistic_deception_analyzer.py`
- **Use Cases**:
  - Detect contradictions in SEC filings
  - Analyze hedging language and obfuscation patterns
  - Extract entities and relationships

#### forensic-financial-analyst
- **Purpose**: Quantitative analysis using Beneish M-Score, Benford's Law, and ML models
- **Tools**: Read, Write, Edit, Bash, Glob, Grep
- **Integration**:
  - `src/forensics/benfords_law_analyzer.py`
  - `src/forensics/ml_fraud_detector.py`
  - `src/forensics/advanced_forensic_analytics.py`
- **Use Cases**:
  - Calculate fraud detection scores
  - Run statistical anomaly detection
  - Perform financial ratio analysis

#### forensic-research-specialist
- **Purpose**: Deep research for SEC filings, whistleblower cases, and regulatory data
- **Tools**: Read, Write, Edit, Bash, Glob, Grep, WebFetch, WebSearch
- **Integration**:
  - `src/forensics/multi_tier_sec_fetcher.py`
  - `src/forensics/agent_sec_analyzer.py`
- **Use Cases**:
  - Retrieve SEC filings from EDGAR
  - Research whistleblower awards
  - Background checks on executives

#### forensic-compliance-auditor
- **Purpose**: Map findings to SEC rules, federal statutes, and enforcement precedents
- **Tools**: Read, Grep, Glob, WebFetch, WebSearch
- **Integration**:
  - `src/forensics/forensic_statutory_mapper.py`
  - `src/forensics/advanced_statute_integrator.py`
- **Use Cases**:
  - Identify regulatory violations
  - Research enforcement precedents
  - Assess potential penalties

### 2. Orchestration Subagents (`.claude/agents/orchestration/`)

Coordinate multi-agent workflows and manage investigation state.

#### forensic-workflow-orchestrator
- **Purpose**: Master orchestrator for comprehensive forensic investigations
- **Tools**: Read, Write, Edit, Bash, Glob, Grep
- **Integration**: `src/forensics/unified_forensic_pipeline.py`
- **Use Cases**:
  - Coordinate all forensic agents
  - Aggregate findings and generate reports
  - Manage investigation lifecycle

#### multi-agent-coordinator
- **Purpose**: Tactical coordination of agent handoffs and task routing
- **Tools**: Read, Write, Edit, Bash, Glob, Grep
- **Use Cases**:
  - Route tasks to appropriate agents
  - Manage sequential and parallel workflows
  - Handle agent failures and retries

#### context-manager
- **Purpose**: Maintain investigation context and state across agent invocations
- **Tools**: Read, Write, Edit, Bash, Glob, Grep
- **Use Cases**:
  - Persist investigation state
  - Provide context to agents
  - Track analysis progress

### 3. Infrastructure Subagents (`.claude/agents/infrastructure/`)

Support deployment, security, and infrastructure management.

#### devops-engineer
- **Purpose**: CI/CD pipelines and deployment automation
- **Tools**: Read, Write, Edit, Bash, Glob, Grep

#### security-engineer
- **Purpose**: Evidence integrity and chain of custody
- **Tools**: Read, Write, Edit, Bash, Glob, Grep

#### database-administrator
- **Purpose**: Forensic data storage and management
- **Tools**: Read, Write, Edit, Bash, Glob, Grep

#### cloud-architect
- **Purpose**: Cloud deployment architecture (AWS, Azure, GCP)
- **Tools**: Read, Write, Edit, Bash, Glob, Grep

### 4. Development Subagents (`.claude/agents/development/`)

Assist with code development, API design, and documentation.

#### python-pro
- **Purpose**: Expert Python development for forensic modules
- **Tools**: Read, Write, Edit, Bash, Glob, Grep

#### backend-developer
- **Purpose**: REST API and microservices development
- **Tools**: Read, Write, Edit, Bash, Glob, Grep

#### documentation-engineer
- **Purpose**: Technical documentation and API docs
- **Tools**: Read, Write, Edit, Bash, Glob, Grep

## Integration with JLAW Modules

### Core Forensic Pipeline Integration

The subagents integrate with the unified forensic pipeline (`src/forensics/unified_forensic_pipeline.py`):

```python
# Phase execution with subagent delegation
async def run_comprehensive_analysis(cik: str, period: tuple):
    """Execute full forensic analysis using subagents."""
    
    # Phase 1-3: Data Collection (forensic-research-specialist)
    filings = await delegate_to_research_specialist(cik, period)
    
    # Phase 4-6: NLP Analysis (forensic-nlp-analyst)
    nlp_findings = await delegate_to_nlp_analyst(filings)
    
    # Phase 7-9: Quantitative Analysis (forensic-financial-analyst)
    quant_findings = await delegate_to_financial_analyst(filings)
    
    # Phase 10-11: Compliance Mapping (forensic-compliance-auditor)
    compliance = await delegate_to_compliance_auditor(nlp_findings, quant_findings)
    
    # Phase 12-13: Synthesis (forensic-workflow-orchestrator)
    report = await orchestrator.synthesize_findings(
        nlp_findings, quant_findings, compliance
    )
    
    return report
```

## Usage Examples

### Example 1: Comprehensive Forensic Investigation

```
PROMPT TO FORENSIC-WORKFLOW-ORCHESTRATOR:

Conduct a comprehensive forensic investigation of Tesla (CIK 0001318605) 
covering fiscal years 2021-2023. Coordinate all forensic subagents to:

1. Retrieve all 10-K, 10-Q, and 8-K filings
2. Analyze for contradictions and deceptive language
3. Calculate Beneish M-Score and run Benford's Law tests
4. Research whistleblower activity and enforcement actions
5. Map findings to applicable SEC rules and statutes
6. Generate DOJ-grade forensic report

Provide comprehensive evidence packages suitable for enforcement referral.
```

### Example 2: Targeted NLP Analysis

```
PROMPT TO FORENSIC-NLP-ANALYST:

Analyze the MD&A and Risk Factors sections of Nike's 2019 10-K 
(CIK 0000320187) for:

1. Semantic contradictions between revenue recognition claims and footnotes
2. Hedging language indicating potential deception
3. Shifts in sentiment or disclosure completeness vs. prior years
4. Undisclosed related party transactions

Provide detailed contradiction analysis with exact citations and confidence scores.
```

### Example 3: Quantitative Fraud Detection

```
PROMPT TO FORENSIC-FINANCIAL-ANALYST:

Calculate comprehensive fraud detection metrics for [Company Name]:

1. Beneish M-Score using 2023 vs 2022 financial statements
2. Altman Z-Score for bankruptcy risk assessment
3. Benford's Law analysis on revenue and accounts receivable
4. XGBoost ML fraud probability with feature importance

Cross-validate findings and provide detailed statistical analysis with 
interpretation for non-technical stakeholders.
```

### Example 4: Research & Due Diligence

```
PROMPT TO FORENSIC-RESEARCH-SPECIALIST:

Conduct comprehensive research on [Company/Executive]:

1. Retrieve complete SEC filing history (2018-2024)
2. Search whistleblower awards database for related allegations
3. Research executive background and prior company involvement
4. Identify enforcement actions and litigation history
5. Analyze peer companies for industry comparison

Provide structured research report with all sources documented.
```

### Example 5: Compliance Assessment

```
PROMPT TO FORENSIC-COMPLIANCE-AUDITOR:

Based on the forensic findings (Beneish M-Score = -1.78, multiple 
contradictions detected), map violations to:

1. Specific SEC rules (10b-5, 13(a), etc.)
2. Federal securities statutes
3. Relevant accounting standards (ASC 606, etc.)
4. Research enforcement precedents for similar cases
5. Estimate potential penalties and remediation requirements

Generate prosecution-ready compliance report with legal citations.
```

## Deployment and Verification

### Single-Click Deployment (Recommended)

The VoltAgent subagent deployment is **fully integrated** into the JLAW single-click deployment script:

```powershell
# Windows PowerShell - Complete deployment with subagent verification
PowerShell -ExecutionPolicy Bypass -File .\deploy_forensic_system.ps1
```

The deployment script automatically:
1. Verifies Python environment
2. Installs dependencies
3. **Verifies all 14 VoltAgent subagents** (Step 3)
4. Verifies 13 forensic modules (Step 4)
5. Tests filing collection (Step 5)
6. Runs forensic analysis (Step 6)
7. Opens results folder (Step 7)

### Manual Deployment Verification

You can also run the deployment script independently:

```bash
python scripts/deploy_subagents.py --verbose
```

Expected output:
```
✓ All subagents deployed and verified successfully!
Total Subagents: 14
Validated: 14
Errors: 0
```

### Verify Directory Structure

```bash
tree .claude/agents/
```

Expected structure:
```
.claude/agents/
├── forensic/
│   ├── forensic-nlp-analyst.md
│   ├── forensic-financial-analyst.md
│   ├── forensic-research-specialist.md
│   └── forensic-compliance-auditor.md
├── orchestration/
│   ├── forensic-workflow-orchestrator.md
│   ├── multi-agent-coordinator.md
│   └── context-manager.md
├── infrastructure/
│   ├── devops-engineer.md
│   ├── security-engineer.md
│   ├── database-administrator.md
│   └── cloud-architect.md
└── development/
    ├── python-pro.md
    ├── backend-developer.md
    └── documentation-engineer.md
```

## Best Practices

### 1. Agent Selection

- **Use forensic-workflow-orchestrator** for complete investigations requiring multiple agents
- **Use specialized agents** for focused analysis (NLP only, financial only, etc.)
- **Use multi-agent-coordinator** when you need explicit control over agent handoffs

### 2. Context Management

- Always provide sufficient context in your prompts
- Reference specific CIK numbers, accession numbers, or file paths
- Include investigation goals and required outputs

### 3. Evidence Quality

- Agents maintain chain of custody for all evidence
- All findings include confidence scores and citations
- Evidence packages are suitable for legal proceedings

### 4. Performance Optimization

- Use parallel execution for independent analyses
- Leverage caching for repeated queries
- Monitor API rate limits (SEC EDGAR: 10 req/sec)

### 5. Error Handling

- Agents implement retry logic with exponential backoff
- Failed analyses include diagnostic information
- Escalation paths for unrecoverable errors

## Troubleshooting

### Subagent Not Found

If a subagent file is missing, run the deployment script:

```bash
python scripts/deploy_subagents.py
```

### API Rate Limits

The forensic-research-specialist respects SEC EDGAR rate limits (10 requests/second). For bulk operations, use the multi-tier fetcher with built-in rate limiting.

### Memory/Context Issues

If analyses are incomplete due to context limits, break down the investigation into smaller phases and use the context-manager to maintain state.

## Support and Contribution

- **Documentation**: See individual subagent files for detailed capabilities
- **Issues**: Report issues to the JLAW GitHub repository
- **Enhancements**: Propose new subagents or capabilities via pull request

## Version History

- **v1.0.0** (2024-01-15): Initial VoltAgent subagent integration
  - 14 specialized subagents across 4 categories
  - Full integration with JLAW forensic modules
  - Deployment and verification tooling

## References

- [JLAW Main README](../README.md)
- [Unified Forensic Pipeline Documentation](../docs/UNIFIED_FORENSIC_SYSTEM.md)
- [Agent Coordination Guide](../AGENTS.md)
- [Claude Code Subagents Documentation](https://docs.anthropic.com/)
