# JARVIS 2.0 - MCP Forensics Quick Reference

## 🚀 Quick Start (30 seconds)

```python
from agents.mcp import (
    MCPServerStdio,
    enable_forensics,
    get_server_forensic_summary,
    export_forensic_report_to_markdown,
)

# 1. Enable forensics
enable_forensics()

# 2. Use MCP normally
server = MCPServerStdio(params={"command": "python", "args": ["server.py"]})
await server.connect()
await server.list_tools()

# 3. Get insights
summary = get_server_forensic_summary(server)
print(f"Ops: {summary['audit']['total_operations']}")

# 4. Export report
export_forensic_report_to_markdown("report.md", [server])
```

---

## 📊 Core Functions

### Enable/Disable
```python
from agents.mcp import enable_forensics, disable_forensics, is_forensics_enabled

enable_forensics()      # Turn on
disable_forensics()     # Turn off
is_forensics_enabled()  # Check: returns bool
```

### Get Summaries
```python
from agents.mcp import (
    get_global_forensic_summary,
    get_server_forensic_summary,
    get_tool_execution_profiles,
)

global_summary = get_global_forensic_summary()
# Returns: {"enabled": bool, "archive": {...}, "execution_profiles": {...}}

server_summary = get_server_forensic_summary(server)
# Returns: {"audit": {...}, "state": {...}, "errors": {...}}

tool_profiles = get_tool_execution_profiles()
# Returns: {"tool_name": {"execution_count": int, "avg_duration_ms": float, ...}}
```

### Export Data
```python
from agents.mcp import (
    export_forensic_data_to_json,
    export_forensic_report_to_markdown,
)

# JSON export
json_path = export_forensic_data_to_json(
    "forensic_data.json",
    servers=[server1, server2],  # Optional
    pretty=True,
)

# Markdown report
md_path = export_forensic_report_to_markdown(
    "forensic_report.md",
    servers=[server1, server2],  # Optional
)
```

---

## 🔍 Data Access Patterns

### Audit Trail
```python
summary = get_server_forensic_summary(server)
audit = summary["audit"]

print(f"Total Ops: {audit['total_operations']}")
print(f"Errors: {audit['error_count']}")
print(f"Error Rate: {audit['error_rate']:.1%}")
print(f"Operations: {audit['operation_counts']}")
print(f"Avg Durations: {audit['average_durations']}")
```

### State Tracking
```python
state = summary["state"]

print(f"Current: {state['current_state']}")
print(f"Transitions: {state['total_transitions']}")
print(f"Durations: {state['state_durations']}")
```

### Error Analysis
```python
errors = summary["errors"]

print(f"Total: {errors['total_errors']}")
print(f"Patterns: {errors['error_patterns']}")
print(f"Recent: {errors['recent_errors']}")
```

### Tool Profiling
```python
profiles = get_tool_execution_profiles()

for tool_name, profile in profiles.items():
    print(f"{tool_name}:")
    print(f"  Executions: {profile['execution_count']}")
    print(f"  Errors: {profile['error_count']}")
    print(f"  Avg Time: {profile['avg_duration_ms']:.2f}ms")
    print(f"  Error Rate: {profile['error_rate']:.1%}")
```

---

## ⚠️ Anomaly Detection Thresholds

| Type | Threshold | Detection |
|------|-----------|-----------|
| Slow Operation | >3x average | Auto-logged |
| Excessive Retries | >2 retries | Auto-logged |
| High Error Rate | >30% | Auto-logged |
| Rapid Transitions | 10 in <1s | Auto-logged |
| Stuck State | >5x average | Auto-logged |
| Repetitive Pattern | >10 in 100 | Auto-logged |

All anomalies automatically logged to standard logger at WARNING/ERROR level.

---

## 📈 Performance Monitoring Template

```python
import asyncio
from agents.mcp import get_tool_execution_profiles

async def monitor():
    """Monitor tool performance every minute."""
    while True:
        profiles = get_tool_execution_profiles()
        
        for tool, profile in profiles.items():
            # Check for slow tools
            if profile["avg_duration_ms"] > 5000:
                print(f"⚠ SLOW: {tool} ({profile['avg_duration_ms']:.0f}ms)")
            
            # Check for high error rates
            if profile["error_rate"] > 0.1:
                print(f"⚠ ERRORS: {tool} ({profile['error_rate']:.1%})")
        
        await asyncio.sleep(60)
```

---

## 📋 Daily Report Template

```python
import asyncio
from datetime import datetime
from agents.mcp import export_forensic_report_to_markdown

async def daily_reports(servers):
    """Generate daily forensic reports."""
    while True:
        timestamp = datetime.now().strftime("%Y%m%d")
        path = f"reports/forensic_{timestamp}.md"
        
        export_forensic_report_to_markdown(path, servers)
        print(f"✓ Report generated: {path}")
        
        await asyncio.sleep(86400)  # 24 hours
```

---

## 🔧 Configuration

### Default Buffer Sizes
- Audit Buffer: 10,000 entries
- Archive: 10,000 operations
- State History: 1,000 transitions
- Error Chain: 1,000 errors

### Memory Usage
- ~1KB per operation
- Automatic oldest-entry removal
- Bounded by deque maxlen

### Performance Impact
- CPU: <1% overhead
- Latency: <1ms per operation
- I/O: In-memory until export

---

## 🔒 Security

### Auto-Sanitization
Sensitive fields automatically redacted:
- `password`, `token`, `api_key`, `secret`, `credential`

### Size Limits
- Arguments/results: 500 chars max
- Stack traces: Full capture
- Large payloads: Truncated with "..."

---

## 🐛 Troubleshooting

### Not Tracking?
```python
from agents.mcp import is_forensics_enabled, enable_forensics

if not is_forensics_enabled():
    enable_forensics()
```

### High Memory?
```python
# Forensics uses bounded buffers
# Check if you need to export/clear more frequently
export_forensic_data_to_json("backup.json")
```

### Missing Data?
```python
# Ensure servers included in export
export_forensic_report_to_markdown(
    "report.md",
    servers=[server1, server2, server3],  # All servers
)
```

---

## 📚 Documentation

- **Full Docs**: `docs/mcp_forensics.md`
- **Example**: `examples/mcp/forensic_analysis_example.py`
- **README**: `examples/jarvis_law_sec_auditor/MCP_FORENSICS_README.md`
- **Summary**: `FORENSIC_IMPLEMENTATION_SUMMARY.md`

---

## 💡 Common Patterns

### Pattern 1: Basic Monitoring
```python
enable_forensics()
server = MCPServerStdio(params={...})
await server.connect()
# ... use server ...
summary = get_server_forensic_summary(server)
```

### Pattern 2: Multi-Server Analysis
```python
servers = [server1, server2, server3]
export_forensic_report_to_markdown("report.md", servers)
```

### Pattern 3: Tool Performance Check
```python
profiles = get_tool_execution_profiles()
slow_tools = [
    t for t, p in profiles.items()
    if p["avg_duration_ms"] > 1000
]
```

### Pattern 4: Error Investigation
```python
summary = get_server_forensic_summary(server)
errors = summary["errors"]
top_errors = sorted(
    errors["error_patterns"].items(),
    key=lambda x: x[1],
    reverse=True,
)[:5]
```

---

## 🎯 One-Liners

```python
# Enable tracking
enable_forensics()

# Get all tool profiles
profiles = get_tool_execution_profiles()

# Export JSON report
export_forensic_data_to_json("data.json")

# Export markdown report
export_forensic_report_to_markdown("report.md")

# Check if enabled
is_forensics_enabled()

# Get global summary
get_global_forensic_summary()

# Get server summary
get_server_forensic_summary(server)
```

---

## ✅ Quick Validation

```python
from agents.mcp import *

# 1. Enable
enable_forensics()
assert is_forensics_enabled() == True

# 2. Create server
server = MCPServerStdio(params={"command": "python", "args": ["test.py"]})
await server.connect()

# 3. Check tracking
summary = get_server_forensic_summary(server)
assert "audit" in summary
assert "state" in summary
assert "errors" in summary

# 4. Export works
path = export_forensic_report_to_markdown("test_report.md", [server])
assert Path(path).exists()

print("✓ Forensics operational!")
```

---

**JARVIS 2.0 - Operational Excellence**  
*No excuses. No limits. Complete visibility.*

