# Development Quick Reference

## Environment Setup (One-time)

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone git@github.com:akhilkarra/investilearn.git
cd investilearn

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # macOS/Linux
uv sync --all-extras

# Install pre-commit hooks
uv run pre-commit install
```

## Daily Development Workflow

### Starting Work

```bash
cd investilearn
source .venv/bin/activate  # Activate venv
git pull origin main       # Get latest changes
```

### Making Changes

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make your changes...

# Run linter and formatter
uv run ruff check . --fix
uv run ruff format .

# Run tests
uv run pytest

# Commit (pre-commit hooks run automatically)
git add .
git commit -m "feat: your feature description"

# Push and create PR
git push origin feature/your-feature-name
```

### Running the App

```bash
uv run streamlit run dashboard.py
# Opens at http://localhost:8501
```

### Code Quality Checks

```bash
# Lint only
uv run ruff check .

# Format code
uv run ruff format .

# Type checking
uv run mypy dashboard.py --ignore-missing-imports

# Run all pre-commit hooks manually
uv run pre-commit run --all-files

# Run tests with coverage
uv run pytest --cov=. --cov-report=html
```

### Working with Stashed Changes

```bash
# View stashed changes
git stash list

# Apply stashed changes (your feature work)
git stash pop

# Or apply specific stash
git stash apply stash@{0}
```

## Adding Dependencies

```bash
# Add runtime dependency
uv add package-name

# Add dev dependency
uv add --dev package-name

# Update all dependencies
uv sync --upgrade
```

## Common Commands

| Task | Command |
|------|---------|
| Install deps | `uv sync` |
| Run app | `uv run streamlit run dashboard.py` |
| Run tests | `uv run pytest` |
| Format code | `uv run ruff format .` |
| Lint code | `uv run ruff check .` |
| Type check | `uv run mypy dashboard.py` |
| Update deps | `uv sync --upgrade` |

## Git Workflow

```bash
# Check status
git status

# Stash work in progress
git stash push -u -m "WIP: description"

# View stashes
git stash list

# Apply last stash
git stash pop

# Create branch
git checkout -b feature/name

# Commit with conventional commits
git commit -m "feat: add feature"
git commit -m "fix: fix bug"
git commit -m "docs: update docs"
git commit -m "chore: update config"

# Push
git push origin branch-name
```

## Troubleshooting

### Pre-commit hooks failing
```bash
# Update hooks
uv run pre-commit autoupdate

# Clear cache
uv run pre-commit clean
uv run pre-commit install --install-hooks
```

### Dependencies issues
```bash
# Remove .venv and reinstall
rm -rf .venv
uv venv
uv sync --all-extras
```

### App won't start
```bash
# Check Python version (need 3.10+)
python --version

# Verify dependencies
uv pip list

# Check for errors in dashboard.py
uv run python -m py_compile dashboard.py
```

## Next Steps

After infrastructure setup, restore your feature work:

```bash
# Apply stashed changes
git stash pop

# Continue development with proper tooling!
```
