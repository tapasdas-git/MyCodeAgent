# MyOmnigent CLI

`MyOmnigent` is an enterprise-grade, automated workflow CLI tool designed to parse tasks from `TODO.md`, execute AI implementation stages, enforce adversarial code reviews, update changelogs, and manage GitHub pull requests automatically.

---

## 📋 Prerequisites

Before setting up `MyOmnigent` in a fresh environment, ensure the following dependencies and tools are installed and configured:

1. **Python 3.8+**
   * Check installation:
     ```bash
     python3 --version
     ```

2. **Git**
   * Installed and configured with your target repository:
     ```bash
     git --version
     ```

3. **GitHub CLI (`gh`)**
   * Required for automated Pull Request creation during the delivery stage.
   * Authenticate your active session:
     ```bash
     gh auth login
     gh auth status
     ```

4. **Omnigent Binary / Core Runner**
   * Ensure `omnigent` is installed and accessible in your environment's `$PATH`:
     ```bash
     omnigent --version
     ```

---

## 📁 Project Directory Structure

For `MyOmnigent` to locate configuration files and source code correctly, ensure your repository root matches this layout:

```text
MyOmnigent/                        # Project Root Directory
├── TODO.md                        # Task queue file containing structured tasks
├── CHANGELOG.md                   # Automated release changelog
├── codeReviewGuideline.md         # Enterprise review & security standards
├── pyproject.toml                 # Package configuration & entry points
├── workflow_runtime.toml          # Model, harness, and timeout runtime settings
├── omnigent_bugfix_workflow.yaml  # Workflow stage definitions for Omnigent
├── git_approval.toml             # Approved Git identity & remote repository rules
├── README.md                      # Documentation
├── scripts/
│   └── workflow_helpers.py        # Deterministic Python scripts (Changelog & PR)
└── src/
    └── myomnigent/
        ├── __init__.py            # Package initialization
        └── __main__.py            # CLI entry point logic