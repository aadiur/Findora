# Findora Installation & Deployment Guide

This guide covers setup prerequisites, standalone installation, and building from source on Windows.

---

## 1. System Requirements

| Specification | Minimum Requirement | Recommended |
| :--- | :--- | :--- |
| **Operating System** | Windows 10 (64-bit) build 19041+ | Windows 11 (64-bit) 22H2+ |
| **Processor** | Dual-core 2.0 GHz x64 | Quad-core 3.0+ GHz x64 |
| **RAM** | 4 GB | 8 GB or higher |
| **Disk Space** | 100 MB free storage | SSD with 500 MB free storage |
| **Display** | 1280 × 720 resolution | 1920 × 1080 resolution or higher |

---

## 2. Standalone Release Installation (Recommended for End Users)

The standalone release requires **no prior installation of Python, .NET SDK, or external compilers**.

### Option A: Modern Windows Installer (Recommended)
1. Download `Findora-Setup-v1.0.0.exe` from the [Findora Releases](https://github.com/aadiur/Findora/releases) page.
2. Run the installer. It installs cleanly into `%LOCALAPPDATA%\Programs\Findora` without requiring administrator privileges or UAC elevation.
3. Check the box to launch Findora upon completion. Start Menu and optional Desktop shortcuts are created automatically.

### Option B: Portable ZIP Edition
1. Download `Findora-v1.0.0-windows-x64.zip` from the [Findora Releases](https://github.com/aadiur/Findora/releases) page.
2. Extract the archive into any directory (e.g. `C:\Tools\Findora\` or a USB drive).
3. Run `Findora.exe`.

### First-Time Launch & SmartScreen
Because Findora is an open-source project without a paid EV code-signing certificate, Windows SmartScreen may show an *"Unknown Publisher"* warning.
- Click **More info** &rarr; **Run anyway**.
- You can verify package integrity against the published `SHA256SUMS.txt` cryptographic hash file.

### First-Run Folder Configuration
1. Open Findora (hotkey: **`Ctrl + Alt + F`** or click the floating desktop disc).
2. Click the **⚙️ Settings** icon in the search bar.
3. Under **Indexed Folders**, click **+ Add Folder...** to choose specific directories or drives to index.
4. Searches run instantly in $< 1\text{ ms}$ as the background engine indexes and monitors file changes.

---

## 3. Building From Source (Developers)

### 3.1 Developer Prerequisites
Ensure the following tools are installed on your Windows workstation:
1. **[.NET 8.0 SDK](https://dotnet.microsoft.com/download/dotnet/8.0)** (v8.0.100 or later).
   ```powershell
   dotnet --version
   ```
2. **[Python 3.10+](https://www.python.org/downloads/)** (64-bit recommended).
   ```powershell
   python --version
   ```
3. **PowerShell 5.1+ or PowerShell 7+**.

### 3.2 Clone Repository
```powershell
git clone https://github.com/aadiur/Findora.git
cd Findora
```

### 3.3 Set Up Python Virtual Environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

### 3.4 Restore and Build .NET Solution
```powershell
dotnet restore Findora.sln
dotnet build Findora.sln -c Release
```

---

## 4. Packaging the Standalone Distributable

To compile and assemble the full production release package:

```powershell
powershell -ExecutionPolicy Bypass -File build\build_release.ps1
```

### Build Pipeline Steps Executed:
1. **Quality Gate**: Runs full Python unit test suite (120 tests) and .NET xUnit test suite (12 tests) — 132 tests total.
2. **Directory Initialization**: Prepares `dist\Findora\` and `dist\Findora\backend\`.
3. **PyInstaller Compilation**: Bundles Python runtime, standard library, and dependencies into `dist\Findora\backend\FindoraBackend.exe`.
4. **.NET WPF Compilation**: Publishes `Findora.exe` in `Release` configuration (self-contained win-x64 single file) into `dist\Findora\`.
5. **Sanity Verification**: Validates presence of both primary executables.
6. **Package Generation**: Compiles `dist\Findora-Setup-v1.0.0.exe` via Inno Setup 6 and compresses `dist\Findora-v1.0.0-windows-x64.zip`.
7. **Checksum Generation**: Outputs `dist\SHA256SUMS.txt` with SHA-256 hashes of all distributables.

---

## 5. Storage and Data Directory Locations

Findora persists state in standard Windows per-user storage:

| Asset | File System Location | Description |
| :--- | :--- | :--- |
| **Catalog Database** | `%LOCALAPPDATA%\Findora\findora.db` | Primary SQLite index in WAL mode. |
| **Database WAL** | `%LOCALAPPDATA%\Findora\findora.db-wal` | Write-Ahead Log journal file. |
| **Database SHM** | `%LOCALAPPDATA%\Findora\findora.db-shm` | Shared-memory index for WAL. |
| **Backend Logs** | `%LOCALAPPDATA%\Findora\logs\backend.log` | Subprocess diagnostic and crash logs. |
| **Autostart Entry** | `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` | Windows login autostart registry key. |

---

## 6. Uninstallation

Because Findora stores all runtime state in standard `%LOCALAPPDATA%`:
1. Exit Findora from the system tray or Task Manager.
2. Delete the application folder where you unpacked `Findora`.
3. (Optional) Remove stored index and logs:
   ```powershell
   Remove-Item -Recurse -Force "$env:LOCALAPPDATA\Findora"
   ```
4. (Optional) Remove the autostart registry entry:
   ```powershell
   Remove-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" -Name "Findora" -ErrorAction SilentlyContinue
   ```
