# Troubleshooting Guide

Common issues and solutions for JLAW deployment and execution.

See also: [Strict Mode Troubleshooting](../STRICT_MODE_TROUBLESHOOTING.md)

## Configuration Issues

### SEC User-Agent Invalid
**Error**: "SEC User-Agent not valid"  
**Solution**: Set `SEC_USER_AGENT` in `.env` with format: `CompanyName/Version (email@domain.com)`

### API Keys Missing
**Error**: "API key not configured"  
**Solution**: Set required API keys in `.env`: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`

## Connection Issues

### SEC API 429 Errors
**Error**: "Rate limit exceeded"  
**Solution**: Reduce `SEC_RATE_LIMIT` in `.env` (default: 6.0)

### Database Connection Failed
**Error**: "Cannot connect to Neo4j/Redis/TimescaleDB"  
**Solution**: Verify service is running and connection settings in `.env`

## Execution Issues

### Node Failures
**Error**: "Node X failed"  
**Solution**: Check logs in `logs/execution.log` for specific error. Some nodes are optional.

### Phase Gate Failures
**Error**: "Phase gate failed"  
**Solution**: In strict mode, check abort report. In standard mode, warnings are logged but execution continues.

---

For more issues, see GitHub Issues or docs.
