# Contributing to Findora

Thank you for your interest in contributing to **Findora**! We welcome bug reports, feature suggestions, architectural improvements, and code contributions.

---

## Code of Conduct
By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

---

## How Can I Contribute?

### 1. Reporting Bugs
- Check the [Issue Tracker](https://github.com/aadiur/Findora/issues) to ensure the bug hasn't already been reported.
- Use the **Bug Report Template** and include:
  - Windows OS build and version (e.g., Windows 11 23H2).
  - .NET SDK and Python version.
  - Clear steps to reproduce the issue.
  - Relevant logs from `%LOCALAPPDATA%\Findora\logs\backend.log`.

### 2. Suggesting Enhancements
- Open a feature request explaining the problem, the proposed solution, and alternative approaches considered.

### 3. Pull Requests
1. Fork the repository and create your branch from `master` (or `main`):
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Follow established code style:
   - **C# / WPF**: Follow official [.NET C# Coding Conventions](https://learn.microsoft.com/en-us/dotnet/csharp/fundamentals/coding-style/coding-conventions).
   - **Python**: Adhere to [PEP 8](https://peps.python.org/pep-0008/) and type hints where appropriate.
3. Ensure all tests pass:
   ```powershell
   python -m pytest tests/python
   dotnet test Findora.sln
   ```
4. Write new tests for any added features or bug fixes.
5. Submit a pull request with a clear description of changes.

---

## Commit Message Guidelines
Use clear, imperative commit messages:
- `feat: add fuzzy filename matching stage in B+ tree`
- `fix: prevent potential handle leak in FileIconService`
- `docs: update IPC protocol specification`
- `ci: add Windows .NET 8 test runner matrix`
