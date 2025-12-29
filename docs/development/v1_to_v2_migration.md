# V1 to V2 Migration Guide

Migrating from V1 node implementations to V2.

## Key Changes

### Import Changes

❌ **Old (V1)**:
```python
from src.nodes.node13_zscore.bankruptcy_predictor import BankruptcyPredictor
```

✅ **New (V2)**:
```python
from src.nodes import BankruptcyPredictorV2
```

### Version Management

Always import from `src.nodes.__init__` which exports V2 versions by default.

## Migration Checklist

- [ ] Update imports to use centralized exports
- [ ] Use V2 class names (suffix V2)
- [ ] Update method calls if API changed
- [ ] Test thoroughly

---

See [MIGRATION_V2_TO_V3.md](../MIGRATION_V2_TO_V3.md) for V2 to V3 migration.
