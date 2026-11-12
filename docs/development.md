# Findora Development Guide

Developer guide for contributing, running tests, debugging IPC, and profiling Findora.

---

## 1. Development Environment Setup

### 1.1 Requirements
- Windows 10 or Windows 11 (64-bit)
- Visual Studio 2022 (Community or higher) with `.NET desktop development` workload **OR** Visual Studio Code with the C# Dev Kit extension.
- [.NET 8.0 SDK](https://dotnet.microsoft.com/download/dotnet/8.0)
- Python 3.10+ (64-bit) with `pip`
- Git

### 1.2 Initial Workspace Bootstrap
```powershell
# Clone the repository
git clone https://github.com/aadiur/Findora.git
cd Findora

# Initialize Python virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install development dependencies
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt

# Restore .NET dependencies
dotnet restore Findora.sln
```

---

## 2. Running in Development Mode

In development mode, the C# WPF frontend automatically locates the Python source tree (`src/Findora.Backend/main.py`) and spawns the backend using `python.exe main.py --ipc`.

```powershell
# Run the WPF frontend from command line
dotnet run --project src\Findora.Wpf\Findora.Wpf.csproj
```

Alternatively, open `Findora.sln` in Visual Studio 2022, set `Findora.Wpf` as the Startup Project, and press **F5** for full interactive debugging.

---

## 3. Running Test Suites

### 3.1 Python Backend Tests
Findora maintains comprehensive unit and integration test coverage across all backend components (B+ Tree, SQLite storage, mutation queue, scanner, watcher, reconciler, and IPC server).

```powershell
# Run all Python tests via pytest
python -m pytest tests/python -v

# Run with test coverage report
python -m pytest tests/python --cov=src/Findora.Backend
```

### 3.2 .NET WPF Tests
The xUnit test suite in `tests/dotnet/Findora.Wpf.Tests/` tests IPC serialization, `FileIconService` handle cleanup, string truncation, rapid query cancellation, auto-recovery on process crash, and `BackendSupervisor` lifecycle.

```powershell
# Run .NET tests via dotnet CLI
dotnet test tests\dotnet\Findora.Wpf.Tests\Findora.Wpf.Tests.csproj -c Release
```

---

## 4. Debugging & Diagnostic Logging

### 4.1 Backend Diagnostic Logs
The backend outputs logs and error traces to `%LOCALAPPDATA%\Findora\logs\backend.log`. You can monitor live output in real-time via PowerShell:

```powershell
Get-Content -Path "$env:LOCALAPPDATA\Findora\logs\backend.log" -Wait -Tail 50
```

### 4.2 Interactive IPC Protocol Testing
You can manually test IPC commands using standard terminal piping:

```powershell
# Test ping handshake
'{"id":1,"method":"ping"}' | python src\Findora.Backend\main.py --ipc

# Test search query
'{"id":2,"method":"search","params":{"query":"report","limit":5}}' | python src\Findora.Backend\main.py --ipc

# Test status
'{"id":3,"method":"status"}' | python src\Findora.Backend\main.py --ipc
```

---

## 5. Performance Benchmarking & Stress Testing

To test B+ Tree index performance under high volume:

```powershell
# Generate synthetic benchmark files (configurable in script)
python tools\generate_benchmark_files.py
```

The script creates structured files with shared naming patterns to evaluate B+ Tree insertion rates, leaf split balance, memory overhead, and search latency.
