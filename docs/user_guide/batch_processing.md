# Batch Processing Guide

Process multiple companies in a single execution.

## Batch File Format

Create a JSON file with targets:

```json
{
  "targets": [
    {"cik": "320187", "company": "Nike Inc.", "year": 2019},
    {"cik": "320193", "company": "Apple Inc.", "year": 2019},
    {"cik": "789019", "company": "Microsoft Corp.", "year": 2019}
  ]
}
```

## Execute Batch

```bash
python jlaw_cli.py --batch targets.json --auto
```

## Output

Each company gets its own output directory:
```
output/
├── Nike_Inc_320187_2019/
├── Apple_Inc_320193_2019/
└── Microsoft_Corp_789019_2019/
```

---

See [CLI Reference](cli_reference.md) for more options.
