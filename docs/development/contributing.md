# Contributing to JLAW

Guidelines for contributing to the JLAW project.

## Code Style

- **Python Version**: 3.10+
- **Type Hints**: Required for all functions
- **Docstrings**: Google-style docstrings required
- **Imports**: Group as stdlib, third-party, local
- **Formatting**: Use `black` and `ruff`

## Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html
```

## Pull Requests

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run linters and tests
5. Submit PR with description

## Code Review

All PRs require:
- ✅ Passing tests
- ✅ Type hints
- ✅ Docstrings
- ✅ No linter errors

---

See [Testing Guide](testing.md) for test patterns.
