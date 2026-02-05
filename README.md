# prospector-extended

Extended [Prospector](https://github.com/PyCQA/prospector) with improved and additional tools for comprehensive Python code analysis.

## Features

### Improved Tools

- **mypy**: Robust JSON parsing with Pydantic validation, text fallback for syntax errors, full configuration support

### New Tools

- **complexipy**: Cognitive complexity analysis (better than cyclomatic for measuring code understandability)
- **interrogate**: Docstring coverage analysis (reports missing docstrings as percentage)

### Why This Package?

Prospector's built-in tool integrations can have issues:
- mypy JSON parsing can break on certain output formats
- Configuration options aren't always properly passed through
- No support for newer tools like complexipy or interrogate

This package addresses these issues by:
- Using `mypy.api.run()` directly with robust JSON parsing
- Implementing Pydantic-based validation with text fallback
- Supporting all standard tool configuration options
- Adding cognitive complexity and docstring coverage analysis

## Installation

```bash
# With uv (recommended)
uv add prospector-extended

# With pip
pip install prospector-extended
```

## Usage

### CLI

```bash
# Run all checks (tools configured in .prospector.yaml)
prospector-extended src/

# Short alias
pex src/

# Exclude specific tools
prospector-extended --without-tool vulture src/

# JSON output
prospector-extended --output-format json src/
```

All tools are enabled/disabled via `.prospector.yaml` - no need for `--with-tool` flags.

### Configuration

#### `.prospector.yaml`

```yaml
# Prospector aggregation config
strictness: high
doc-warnings: true

# Enable ruff, bandit, vulture, pylint via prospector
ruff:
  run: true

bandit:
  run: true

vulture:
  run: true

pylint:
  run: true
  options:
    disable: all
    enable: duplicate-code

# Extended tools
mypy:
  run: true
  options:
    strict: true
    python-version: "3.12"
    show-error-codes: true

complexipy:
  run: true
  options:
    max-complexity: 15

interrogate:
  run: true
  options:
    ignore-init-method: true
    ignore-magic: true
    ignore-module: true
```

#### `pyproject.toml`

```toml
[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
show_error_codes = true

[tool.complexipy]
max_complexity = 15

[tool.interrogate]
ignore-init-method = true
ignore-init-module = true
ignore-magic = true
fail-under = 80
```

## Tool Coverage

| Tool | What it catches | Source |
|------|-----------------|--------|
| **ruff** | Linting, imports, bugs, cyclomatic complexity, design thresholds, docstring style | Prospector extra |
| **mypy** | Type errors (strict checking) | prospector-extended |
| **complexipy** | Cognitive complexity (code understandability) | prospector-extended |
| **interrogate** | Missing docstrings (coverage %) | prospector-extended |
| **pylint** | Duplicate/copy-paste code | Prospector extra |
| **vulture** | Dead/unused code | Prospector extra |
| **bandit** | Security vulnerabilities | Prospector extra |
| **dodgy** | Hardcoded secrets/passwords | Prospector built-in |

## Error Codes

### mypy

Uses standard mypy error codes: `arg-type`, `return-value`, `assignment`, etc.

### complexipy

| Code | Description |
|------|-------------|
| `CCR001` | Cognitive complexity exceeds threshold |
| `CCE001` | Parse error |

### interrogate

| Code | Description |
|------|-------------|
| `INT100` | Missing module docstring |
| `INT101` | Missing class docstring |
| `INT102` | Missing function/method docstring |
| `INT103` | Missing async function docstring |
| `INT104` | Missing nested function docstring |
| `INT105` | Missing nested async function docstring |
| `INT106` | Missing property docstring |

## Thresholds Reference

| Metric | Default | Recommended | Strict |
|--------|---------|-------------|--------|
| Cyclomatic complexity (ruff C90) | 10 | 10 | 7 |
| Cognitive complexity (complexipy) | 15 | 15 | 10 |
| Max function args (ruff PLR0913) | 5 | 6 | 5 |
| Max branches (ruff PLR0912) | 12 | 12 | 8 |
| Max returns (ruff PLR0911) | 6 | 6 | 4 |
| Max statements (ruff PLR0915) | 50 | 50 | 30 |
| Docstring coverage (interrogate) | 80% | 80% | 95% |
| Duplicate code lines (pylint) | 4 | 4 | 6 |

## Development

This project uses [uv](https://github.com/astral-sh/uv) for development:

```bash
# Clone the repository
git clone https://github.com/your-org/prospector-extended
cd prospector-extended

# Install dependencies
uv sync --all-extras

# Run tests
uv run poe test

# Run tests with coverage
uv run poe test-coverage

# Run linting
uv run poe lint

# Format code
uv run poe format

# Run all checks via prospector-extended
uv run poe checks
```

## Architecture

### Parsing Infrastructure

The package includes a flexible parsing infrastructure for tool outputs:

- **TypeRegistry**: Polymorphic JSON parsing with schema matching
- **Pydantic models**: Runtime validation with fingerprinting for drift detection
- **Text fallback**: Regex-based parsing for non-JSON output

### Tool Integration

Tools are integrated by patching Prospector's `TOOLS` dict at runtime:

```python
from prospector_extended import patch_prospector_tools

# Patch before running prospector
patch_prospector_tools()

# Now run prospector normally
from prospector.run import main
main()
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

GPL-2.0-or-later (same as Prospector)
