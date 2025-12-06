# Removing Secrets from Git History

## Why This Is Needed

Even after removing API keys from files, they remain in git history. GitHub's secret scanning detects them in historical commits and blocks the push.

## Solution Options

### Option 1: Rewrite Git History (Recommended)

Use BFG Repo-Cleaner to remove secrets from all commits:

1. **Download BFG**: https://rtyley.github.io/bfg-repo-cleaner/

2. **Create a file with secrets to remove** (`secrets.txt`):
   ```
   # Add each exposed secret on its own line
   # These are the keys that GitHub detected - find them in your error message
   YOUR_EXPOSED_OPENAI_KEY_1
   YOUR_EXPOSED_OPENAI_KEY_2
   YOUR_EXPOSED_ANTHROPIC_KEY
   YOUR_EXPOSED_OPENROUTER_KEY
   YOUR_EXPOSED_GOVINFO_KEY
   ```

3. **Run BFG**:
   ```bash
   java -jar bfg.jar --replace-text secrets.txt .git
   ```

4. **Clean up**:
   ```bash
   git reflog expire --expire=now --all
   git gc --prune=now --aggressive
   ```

5. **Force push**:
   ```bash
   git push --force
   ```

### Option 2: Allow Secrets on GitHub (Quick Fix)

Click the "unblock" links GitHub provided in the error message:
- https://github.com/TIMMAYTHETOOLMANN/JLAW/security/secret-scanning/unblock-secret/36S24fH9n2PYyl6ziCugvZpNheY
- https://github.com/TIMMAYTHETOOLMANN/JLAW/security/secret-scanning/unblock-secret/36QS7zIIFJSiYlpwgRoSIv8Rtmr
- https://github.com/TIMMAYTHETOOLMANN/JLAW/security/secret-scanning/unblock-secret/36QS80rfpML5VTF9jNm2XcnmpvQ
- https://github.com/TIMMAYTHETOOLMANN/JLAW/security/secret-scanning/unblock-secret/36QS7zQqEMyKYuqlA7mDFdZJgWw

⚠️ **Warning**: This marks the secrets as "allowed" but they remain in git history. Rotate your API keys after using this option!

### Option 3: Rotate All Keys (Safest)

1. Generate new API keys from each provider
2. Revoke the old keys
3. Update your `.env` file with new keys
4. Allow the old (now invalid) keys on GitHub
5. Push your code

## After Pushing

Remember to:
1. ✅ Rotate all exposed API keys
2. ✅ Update `.env` with new keys
3. ✅ Run `python setup_keys.py` to verify
4. ✅ Never commit `.env` to git

## Prevention

The following measures are now in place:
- `.gitignore` excludes `.env` and secret files
- `setup_keys.py` for secure key configuration
- Pre-commit hook to detect secrets
- `.env.example` as a template (no real keys)

