# Security Rotation Notice

## Previously Committed Credentials Are Compromised

This repository previously tracked the following files that may have contained credentials, API keys, or encoded secrets:

- `env.encoded` — base64-encoded environment file (contained API keys)
- `restore_env.sh` — script that decoded `env.encoded` into a live `.env` file

**Both files have been removed from version tracking.**

Any credentials that were stored in those files, or in any `.env` file ever committed to this repository, must be treated as **fully compromised**, regardless of whether the commit is still visible in the current branch.

Git history retains all previously committed content. Any credential that appeared in a commit — even a reverted one — should be considered exposed.

## Required Actions

If you held or used credentials associated with this repository, rotate them immediately:

1. **Anthropic API keys** — Generate new keys at [console.anthropic.com](https://console.anthropic.com).
2. **OpenAI API keys** — Generate new keys at [platform.openai.com](https://platform.openai.com).
3. **Polygon.io API keys** — Regenerate at [polygon.io](https://polygon.io).
4. **SEC EDGAR user-agent strings** — Update the contact email if it identifies a real person.
5. **Any other tokens or service credentials** — Rotate through the respective provider's console.

## Going Forward

The `.gitignore` in this repository now explicitly excludes:

```
env.encoded
restore_env.sh
.env
.env.*          (except .env.example)
*.key
*.pem
*.token
credentials.json
secrets/
```

Use `.env.example` as a template. Populate a local `.env` file with real values. **Never commit the populated `.env` file.**

## Verification

To confirm no secrets are currently tracked:

```bash
git ls-files | grep -E "(\.env$|env\.encoded|restore_env|\.key|\.pem|\.token|credentials\.json)"
```

This command should return no output. If it does, remove the listed files from tracking with `git rm --cached <file>` before committing.

---

*This notice was generated as part of the Phase 2 evidence architecture setup.*
