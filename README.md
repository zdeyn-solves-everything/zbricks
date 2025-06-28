# zbricks
zBricks - build cool stuff

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

### Typical Developer Workflow
1. **Develop on `dev` branch.**
2. **Merge `main` into `dev` regularly to keep up-to-date:**
   ```bash
   git checkout dev
   git pull origin dev
   git pull origin main --no-rebase
   # Resolve any conflicts, commit, and push
   git push origin dev
   ```
3. **When ready for release:**
   - Merge `dev` into `main`.
   - Tag a new release (e.g., `v0.1.2`).
   - Push the tag to trigger the release workflow.
4. **To test the release workflow repeatedly:**
   ```bash
   git tag -d v0.1.1
   git push origin :refs/tags/v0.1.1
   git tag v0.1.1
   git push --force origin v0.1.1
   ```

### GitHub Actions Workflows
- `.github/workflows/ci-dev.yml`: Runs on `dev` branch pushes.
- `.github/workflows/release-main.yml`: Runs on `main` branch pushes and on tag pushes (`v*`).

### Monitoring CI/CD
- Use GitHub CLI:
  ```bash
  gh run list -L 5
  gh run view <run-id>
  ```

---

## Project Structure
- `src/zbricks/`: Source code
- `tests/`: Tests
- `pyproject.toml`: Project metadata and build config
- `uv.lock`: Locked dependencies
- `.gitignore`: Clean, deduplicated, up-to-date

---

## Requirements
- Python 3.13+
- `uv`, `hatch`, `hatch-vcs`, `pytest`, `gh` (GitHub CLI)

---

## License
See `LICENSE` file.
