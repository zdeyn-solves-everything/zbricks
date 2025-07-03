# Development & Workflow Guide

This document contains all technical instructions, workflow details, and best practices for developing, testing, and releasing this project.

---

## Project Architecture

zBricks follows a clean separation between the main library and examples:

### Main Library (`src/zbricks/`)
- **Core package**: Contains the main zBricks toolkit
- **Tests**: Located in `tests/` at project root
- **Build system**: Uses `hatch` with `hatch-vcs` for versioning
- **Dependencies**: Core web framework dependencies (Starlette, Jinja2, etc.)

### Examples (`examples/xx-name/`)
- **Separate projects**: Each example is a standalone project with its own `pyproject.toml`
- **Independent tests**: Each example has its own test files
- **App-style config**: Uses hatch but configured for application development
- **Minimal dependencies**: Only what each specific example needs

---

## Development Setup

### Main Library Development

```bash
# Clone and navigate to project
git clone <repo-url>
cd zbricks

# Install in development mode
uv sync --dev

# Run library tests
uv run pytest tests/ -v

# Run all tests (including examples)
uv run pytest tests/ examples/ -v
```

### Example Development

Each example can be developed independently:

```bash
# Navigate to specific example
cd examples/01-hello-world

# Install example dependencies (note: zbricks imported from parent)
uv sync --dev

# Run example
cd ../../  # Run from main project root
uv run uvicorn examples.01-hello-world.app:app --reload

# Test example
uv run pytest examples/01-hello-world/test_app.py -v
```

---

## Automated Python Package Workflow (2025)

This project uses a modern, robust, and developer-friendly workflow for Python package development, testing, and release automation.

### Key Features
- **Dynamic Versioning:**
  - Uses `hatch` and `hatch-vcs` for automatic versioning from git tags/commits.
- **Dependency Management:**
  - Uses `uv` for fast, reproducible dependency installs (see `uv.lock`).
- **Branch Strategy:**
  - `main`: Stable, tagged releases only.
  - `dev`: Active development, always up-to-date with `main`.
- **CI/CD Automation:**
  - **Dev Branch:** On every push, runs tests, builds, and uploads artifacts.
  - **Main Branch:** On every push, runs tests, builds, uploads artifacts, and (optionally) creates a GitHub Release.
  - **Tagged Release:** On every tag push (e.g., `v0.1.1`), runs full release workflow and creates a GitHub Release with artifacts.
- **Re-usable Tag Testing:**
  - You can force-push the same tag (e.g., `v0.1.1`) to repeatedly test the release workflow without polluting release history.
- **GitHub CLI Integration:**
  - Use `gh` to monitor workflow runs, inspect logs, and manage releases from the terminal.

---

## Git Tagging, Versioning, and Branch Workflow

### How Git Tags Work
- **Tags are global**: Tags point to specific commits, not branches. A tag (e.g., `v0.1.2`) always refers to the same commit, no matter which branch you are on.
- **Tags do not move**: If you continue development on `dev`, the tag still points to the commit on `main` where it was created.
- **Tags must be pushed**: Tags are not pushed by default. Use `git push origin v0.1.2` to push a tag, or `git push --tags` to push all tags.
- **Force-pushing tags**: To re-test a workflow with the same tag, delete it locally and remotely, then re-create and force-push it (see below).

### hatch-vcs Versioning
- **Automatic versioning**: `hatch-vcs` reads the latest tag reachable from the current commit to determine the version.
- **On dev branch**: If you branched from `main` at `v0.1.2`, your version will be something like `0.1.2+<dev-commits>` or `0.1.2.devN` (depending on config).
- **Pre-releases**: For RCs or betas, tag on `dev` (e.g., `v0.1.3-rc1`). hatch-vcs will use this for versioning until the next stable tag.
- **On main branch**: Tag the release commit (e.g., `v0.1.3`).

### Best Practices for Tag Flow
- **Tag only on main for releases**: Keeps release history clean.
- **Pre-releases/RCs**: Tag on `dev` with pre-release tags (e.g., `v0.1.3-rc1`).
- **After merging dev into main**: Tag the new release (e.g., `v0.1.3`) on `main`.
- **Keep dev up-to-date**: Regularly merge `main` into `dev` so dev versioning is based on the latest release tag.

### Example Workflow
1. On `main`, tag `v0.1.2` and merge to `dev`.
2. On `dev`, work continues. hatch-vcs versions will be `0.1.2+<dev-commits>`.
3. For a pre-release, tag `v0.1.3-rc1` on `dev`.
4. When ready, merge `dev` into `main` and tag `v0.1.3` on `main`.
5. Merge `main` back into `dev` to update the base for future dev work.

### Day-to-Day Developer Steps
- **Start new work**: Branch from `dev`.
- **Keep up-to-date**: Regularly merge `main` into `dev`.
- **Release process**:
  1. Merge `dev` into `main`.
  2. Tag the release (e.g., `v0.1.3`).
  3. Push the tag to trigger the release workflow.
  4. Merge `main` back into `dev`.
- **Pre-release process**:
  1. Tag a pre-release on `dev` (e.g., `v0.1.3-rc1`).
  2. Push the tag to test workflows.
- **Re-usable tag testing**:
  1. Delete the tag locally: `git tag -d v0.1.1`
  2. Delete the tag remotely: `git push origin :refs/tags/v0.1.1`
  3. Re-create the tag: `git tag v0.1.1`
  4. Force-push the tag: `git push --force origin v0.1.1`

### Summary Table

| Branch | Tag Example      | hatch-vcs Version Output | When to Tag?         |
|--------|------------------|-------------------------|----------------------|
| main   | v0.1.2           | 0.1.2                   | On release           |
| dev    | (no new tag)     | 0.1.2+<dev-commits>     | During development   |
| dev    | v0.1.3-rc1       | 0.1.3rc1                | For pre-releases/RCs |
| main   | v0.1.3           | 0.1.3                   | On next release      |

---

## Creating New Examples

To create a new example:

1. **Create directory**: `examples/02-your-example/`
2. **Add pyproject.toml**:
   ```toml
   [project]
   name = "zbricks-your-example"
   version = "0.1.0"
   description = "Your example description"
   dependencies = [
       "starlette>=0.47.1",
       "uvicorn>=0.35.0",
   ]
   
   [build-system]
   requires = ["hatchling"]
   build-backend = "hatchling.build"
   
   [dependency-groups]
   dev = [
       "pytest>=8.0",
       "pytest-asyncio>=1.0.0",
       "httpx>=0.28.1",
   ]
   ```
3. **Add your app code**: Create `app.py` and templates
4. **Add tests**: Create `test_app.py`
5. **Test**: Run from main project root

---

## Testing Strategy

### Library Tests
- **Location**: `tests/`
- **Focus**: Core functionality, templating, middleware
- **Run with**: `uv run pytest tests/ -v`

### Example Tests
- **Location**: `examples/xx-name/test_*.py`
- **Focus**: End-to-end functionality, integration
- **Run individual**: `uv run pytest examples/01-hello-world/test_app.py -v`
- **Run all**: `uv run pytest examples/ -v`

### Continuous Integration
- Tests run on every push to `dev` and `main`
- Examples are tested as part of the full test suite
- Release builds include all tests passing

---

## GitHub Actions Workflows
- `.github/workflows/ci-dev.yml`: Runs on `dev` branch pushes.
- `.github/workflows/release-main.yml`: Runs on `main` branch pushes and on tag pushes (`v*`).

## Monitoring CI/CD
- Use GitHub CLI:
  ```bash
  gh run list -L 5
  gh run view <run-id>
  ```

---

## Requirements
- Python 3.13+
- `uv`, `hatch`, `hatch-vcs`, `pytest`, `gh` (GitHub CLI)

---

## License
See `LICENSE` file.
