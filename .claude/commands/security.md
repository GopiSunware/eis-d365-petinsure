---
description: Run a security audit on the codebase
---

# Security Audit Command

Perform a security analysis of the codebase using the security-auditor agent.

## Instructions

1. **Scope the Audit**
   - If `$ARGUMENTS` provided, focus on that area
   - Otherwise, audit the entire codebase

2. **Check OWASP Top 10**
   - Injection vulnerabilities
   - Authentication issues
   - Sensitive data exposure
   - Security misconfigurations
   - XSS vulnerabilities

3. **Search for Common Issues**
   - Hardcoded secrets
   - Weak cryptography
   - Command injection
   - SQL injection
   - Insecure dependencies

4. **Report Findings**
   - Categorize by severity
   - Provide specific locations
   - Include remediation guidance

## Arguments

`$ARGUMENTS` can be:
- Empty: Full codebase audit
- File path: Audit specific file/directory
- "auth": Focus on authentication code
- "api": Focus on API endpoints
- "deps": Check dependencies for vulnerabilities

## Search Patterns Used

```bash
# Secrets
grep -rn "password\|api_key\|secret\|token" --include="*.py" --include="*.js"

# SQL injection
grep -rn "execute.*%\|execute.*format" --include="*.py"

# Command injection
grep -rn "os.system\|subprocess" --include="*.py"
```

## Examples

```
/security              # Full audit
/security src/auth     # Audit auth module
/security deps         # Check dependencies
/security api          # Audit API endpoints
```

## Output

Security report with:
- Risk summary (critical/high/medium/low counts)
- Detailed findings with locations
- Remediation steps
- Positive observations
