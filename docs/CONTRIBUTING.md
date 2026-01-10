# Contributing to DepegScope

Thank you for your interest in contributing to DepegScope! This document provides guidelines for contributing to the project.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Setup](#development-setup)
3. [Code Style](#code-style)
4. [Testing](#testing)
5. [Submitting Changes](#submitting-changes)
6. [Research Contributions](#research-contributions)

---

## Getting Started

### Types of Contributions

We welcome the following types of contributions:

- **Bug fixes**: Found a bug? Submit a fix!
- **New features**: Add new collectors, analysis methods, or visualizations
- **Documentation**: Improve or expand documentation
- **Research**: Validate findings, add case studies, or extend methodology
- **Data**: Add new data sources or historical events

### Before You Start

1. Check existing issues and PRs to avoid duplicates
2. For major changes, open an issue first to discuss
3. Read the [METHODOLOGY.md](METHODOLOGY.md) to understand the approach

---

## Development Setup

### Prerequisites

- Python 3.10+
- Git
- Virtual environment tool (venv, conda)

### Setup Steps

```bash
# Clone the repository
git clone https://github.com/yourusername/DepegScope.git
cd DepegScope

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # If exists

# Install pre-commit hooks (if configured)
pre-commit install

# Run tests to verify setup
pytest tests/
```

### Project Structure

```
src/
├── collectors/     # Add new data sources here
├── models/         # Data models
├── analysis/       # Analysis algorithms
├── simulation/     # Agent-based models
└── visualization/  # Plotting functions
```

---

## Code Style

### Python Style Guide

We follow PEP 8 with the following specifications:

- **Line length**: 88 characters (Black default)
- **Imports**: Use `isort` for sorting
- **Docstrings**: Google style
- **Type hints**: Required for public functions

### Example

```python
from typing import Dict, List, Optional

from loguru import logger


def calculate_blast_radius(
    stablecoin: str,
    severity: float = 0.1,
    include_secondary: bool = True
) -> Dict[str, float]:
    """Calculate the blast radius for a stablecoin depeg.

    Args:
        stablecoin: Symbol of the stablecoin to analyze.
        severity: Initial depeg severity (0-1).
        include_secondary: Whether to include secondary effects.

    Returns:
        Dictionary mapping protocol names to impact values.

    Raises:
        ValueError: If stablecoin is not found in the graph.

    Example:
        >>> impact = calculate_blast_radius("USDC", severity=0.15)
        >>> print(f"Total impact: ${sum(impact.values()):,.0f}")
    """
    if severity < 0 or severity > 1:
        raise ValueError("Severity must be between 0 and 1")

    # Implementation...
    pass
```

### Formatting Tools

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Check types
mypy src/

# Lint
flake8 src/ tests/
```

---

## Testing

### Test Structure

```
tests/
├── test_collectors/
│   ├── test_defillama.py
│   └── test_price_feeds.py
├── test_models/
│   ├── test_stablecoin.py
│   └── test_protocol.py
├── test_analysis/
│   ├── test_dependency_graph.py
│   └── test_risk_metrics.py
├── test_simulation/
│   ├── test_environment.py
│   └── test_scenarios.py
└── conftest.py          # Shared fixtures
```

### Writing Tests

```python
import pytest
from src.analysis.dependency_graph import DependencyGraph


class TestDependencyGraph:
    """Tests for DependencyGraph class."""

    @pytest.fixture
    def sample_graph(self):
        """Create a sample graph for testing."""
        graph = DependencyGraph()
        # Add test data...
        return graph

    def test_add_stablecoin(self, sample_graph):
        """Test adding a stablecoin node."""
        sample_graph.add_stablecoin(
            symbol="TEST",
            market_cap=1_000_000
        )
        assert "TEST" in sample_graph.get_stablecoins()

    def test_blast_radius_calculation(self, sample_graph):
        """Test blast radius returns expected structure."""
        result = sample_graph.calculate_blast_radius("USDC")

        assert isinstance(result, float)
        assert result >= 0

    @pytest.mark.parametrize("severity", [0.01, 0.1, 0.5, 1.0])
    def test_blast_radius_scales_with_severity(self, sample_graph, severity):
        """Test that blast radius increases with severity."""
        result = sample_graph.calculate_blast_radius("USDC", severity=severity)
        # Higher severity should mean higher impact
        assert result >= 0
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_analysis/test_dependency_graph.py

# Run tests matching pattern
pytest -k "blast_radius"

# Run with verbose output
pytest -v

# Run and stop on first failure
pytest -x
```

### Test Categories

Use markers for test categories:

```python
@pytest.mark.slow
def test_monte_carlo_simulation():
    """This test takes a long time."""
    pass

@pytest.mark.integration
def test_defillama_api():
    """This test requires network access."""
    pass
```

Run specific categories:

```bash
# Skip slow tests
pytest -m "not slow"

# Run only integration tests
pytest -m integration
```

---

## Submitting Changes

### Workflow

1. **Fork** the repository
2. **Create a branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make changes** following code style guidelines
4. **Add tests** for new functionality
5. **Run tests** and ensure they pass
6. **Commit** with clear messages:
   ```bash
   git commit -m "Add: New feature for X"
   git commit -m "Fix: Bug in Y when Z"
   git commit -m "Docs: Update API documentation"
   ```
7. **Push** to your fork
8. **Open a Pull Request**

### Commit Message Format

```
<type>: <short description>

<longer description if needed>

<references to issues>
```

Types:
- `Add`: New feature
- `Fix`: Bug fix
- `Docs`: Documentation
- `Refactor`: Code restructuring
- `Test`: Adding tests
- `Chore`: Maintenance

### Pull Request Checklist

- [ ] Code follows style guidelines
- [ ] Tests added/updated
- [ ] All tests pass
- [ ] Documentation updated
- [ ] No sensitive data committed
- [ ] PR has clear description

### PR Template

```markdown
## Description
Brief description of changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation
- [ ] Refactoring

## Testing
Describe how you tested these changes.

## Related Issues
Fixes #123
```

---

## Research Contributions

### Adding Historical Events

To add a new depeg event for validation:

1. Edit `config/stablecoins.yaml`:

```yaml
historical_events:
  - name: "new_event"
    stablecoin: "SYMBOL"
    start_date: "2024-01-15"
    end_date: "2024-01-17"
    min_price: 0.95
    trigger: "Description of cause"
    cascade_effects:
      - "Effect 1"
      - "Effect 2"
    tvl_impact: 500000000
    data_sources:
      - "URL to article"
      - "URL to data"
```

2. Add to `src/models/depeg_event.py`:

```python
HISTORICAL_EVENTS["new_event"] = DepegEvent(
    stablecoin="SYMBOL",
    start_date=datetime(2024, 1, 15),
    # ...
)
```

3. Add validation test in `tests/test_analysis/test_historical.py`

### Adding Data Sources

To add a new data collector:

1. Create `src/collectors/new_source.py`:

```python
"""Collector for NewSource API."""

from typing import Dict, List, Optional
import requests
from loguru import logger


class NewSourceCollector:
    """Collect data from NewSource API."""

    BASE_URL = "https://api.newsource.com/v1"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.session = requests.Session()

    def get_data(self) -> List[Dict]:
        """Fetch data from the API."""
        # Implementation...
        pass
```

2. Add tests in `tests/test_collectors/test_new_source.py`

3. Update `docs/API.md` with usage examples

### Adding Analysis Methods

To add a new risk metric:

1. Add to `src/analysis/risk_metrics.py`:

```python
def calculate_new_metric(self, ...) -> float:
    """Calculate the new metric.

    Mathematical definition:
        NewMetric = ...

    Args:
        ...

    Returns:
        The calculated metric value.
    """
    # Implementation with clear documentation
    pass
```

2. Add tests with known expected values
3. Document in `docs/METHODOLOGY.md`

---

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help newcomers get started
- Credit others' contributions

---

## Questions?

- Open an issue for discussion
- Tag maintainers for help
- Check existing documentation first

Thank you for contributing to DepegScope!
