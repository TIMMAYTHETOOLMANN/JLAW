# API Keys Setup Guide

## Quick Start

After cloning this repository, run the setup script:

```bash
python setup_keys.py
```

This will:
1. Create a `.env` file from the template
2. Prompt you to enter your API keys
3. Validate the configuration

## Manual Setup

### Step 1: Create .env File

```bash
# Copy the template
cp .env.example .env

# Or on Windows
copy .env.example .env
```

### Step 2: Edit .env File

Open `.env` in your editor and add your API keys:

```env
# Required: At least ONE of these AI API keys
OPENAI_API_KEY=sk-proj-your-key-here
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
OPENROUTER_API_KEY=sk-or-v1-your-key-here

# Recommended for government data access
GOVINFO_API_KEY=your-govinfo-key

# Required for SEC EDGAR
SEC_USER_AGENT=YourName contact@your-email.org
```

### Step 3: Validate

```bash
python -m config.secure_config
```

## Obtaining API Keys

### OpenAI API Key
1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create an account or sign in
3. Click "Create new secret key"
4. Copy the key (starts with `sk-proj-`)

### Anthropic (Claude) API Key
1. Go to [Anthropic Console](https://console.anthropic.com/settings/keys)
2. Create an account or sign in
3. Click "Create Key"
4. Copy the key (starts with `sk-ant-api03-`)

### OpenRouter API Key
1. Go to [OpenRouter](https://openrouter.ai/keys)
2. Create an account or sign in
3. Generate a new key
4. Copy the key (starts with `sk-or-v1-`)

### GovInfo API Key
1. Go to [GovInfo API](https://api.govinfo.gov/docs/)
2. Register for an API key
3. Check your email for the key

## Security Best Practices

### ✅ DO:
- Keep `.env` file local (it's in `.gitignore`)
- Use different keys for development and production
- Rotate keys periodically
- Use environment variables in CI/CD

### ❌ DON'T:
- Commit `.env` to git
- Share API keys in chat/email
- Hardcode keys in source files
- Use production keys for testing

## Using Keys in Code

The secure configuration module automatically loads keys:

```python
from config.secure_config import get_api_key, load_all_keys

# Get a specific key
openai_key = get_api_key('OPENAI_API_KEY')

# Load all keys and check status
status = load_all_keys()
print(status)  # {'OPENAI_API_KEY': True, 'ANTHROPIC_API_KEY': False, ...}

# Require a key (raises error if not set)
api_key = get_api_key('OPENAI_API_KEY', required=True)
```

## Troubleshooting

### "API key not found"
1. Check that `.env` file exists in project root
2. Verify the key name matches exactly
3. Run `python -m config.secure_config` to see status

### "Invalid API key"
1. Verify you copied the full key
2. Check the key hasn't expired
3. Ensure sufficient credits/quota on your account

### "Push contains secrets"
If GitHub blocks your push:
1. The key has been committed to git history
2. You need to remove it from ALL commits
3. See: [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/)

## Environment Variables for CI/CD

For automated systems, set environment variables directly:

### GitHub Actions
```yaml
env:
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

### Docker
```dockerfile
ENV OPENAI_API_KEY=${OPENAI_API_KEY}
```

### Shell
```bash
export OPENAI_API_KEY="sk-proj-..."
python sec_forensic_analyzer.py
```

