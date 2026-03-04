# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in prospector-extended, please report it through
the internal security reporting process.

**Do not open a public issue for security vulnerabilities.**

When reporting, please include:

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

## Security Considerations

### Input Validation

All external input should be validated before processing. This includes:

- User-provided data
- API responses
- File contents
- Environment variables

### Dependency Security

Dependencies are scanned using Bandit and JFrog Xray. Run security checks with:

```bash
uv run poe security    # Bandit security scan
uv run poe xray        # JFrog Xray vulnerability scan
```

### Sensitive Data

Do not commit sensitive data to the repository:

- API keys
- Passwords
- Private keys
- Personal data

Use environment variables or secure vaults for sensitive configuration.
