# Findora User & Operation Guide

This guide covers operating Findora, keyboard navigation, desktop widget interactions, and configuration settings.

---

## 1. Quick Start

- **Summon Search**: Press **`Ctrl + Alt + F`** anywhere on Windows or click the desktop magnifying-glass widget.
- **Type Query**: Start typing any filename or extension (e.g., `budget.xlsx` or `annual report`).
- **Navigate Matches**: Use $\uparrow$ and $\downarrow$ arrow keys to move through the results list.
- **Reveal File in Explorer**: Press **`Enter`** to open the parent folder and highlight the item.
- **Open File Directly**: Press **`Shift + Enter`** to launch the file in its default associated application.
- **Dismiss Search**: Press **`Escape`** or click anywhere outside the search window.

---

## 2. Keyboard Shortcuts Reference

| Shortcut | Context | Action |
| :--- | :--- | :--- |
| **`Ctrl + Alt + F`** | Global (Any Application) | Toggles the centered glassmorphism search window. |
| **`Enter`** | Search Window | Reveals the selected file in Windows File Explorer (`explorer.exe /select,...`). |
| **`Shift + Enter`** | Search Window | Opens the selected file directly in its default application. |
| **`Up / Down Arrows`** | Search Window | Navigates the search results list with wrap-around selection. |
| **`Escape`** | Search Window | Smoothly dismisses the search window. |
| **`Ctrl + C`** | Result Selected | Copies the absolute full path of the selected file to clipboard. |

---

## 3. Desktop Search Widget

Findora provides a compact, translucent desktop search widget:

- **Docked Mode**: By default, docks unobtrusively in a desktop corner with a subtle blue accent outline.
- **Non-Activating Window**: Implements `WS_EX_NOACTIVATE` and `HWND_NOTOPMOST`, meaning it never steals focus from active games, editors, or presentations.
- **Drag & Reposition**: Click and drag the circular widget anywhere across your monitor workspace.
- **Instant Activation**: Single-clicking the disc smoothly expands the centered search window.

---

## 4. Settings & Preferences

Access the **Settings** dialog by right-clicking the Findora system tray icon or through the search interface gear icon.

### 4.1 Drive Monitoring & Rescanning
- **Live Monitoring Toggle**: Enable or disable kernel-level `ReadDirectoryChangesW` filesystem tracking.
- **Rescan All Drives**: Manually initiate a full re-crawl of all attached NTFS/FAT32 fixed drives.

### 4.2 Exclusions Management
Prevent indexing of high-churn directories or private paths:
- Add folders by path (e.g., `D:\Temp` or `C:\Users\User\AppData\Local\Temp`).
- Default exclusions include:
  - `$Recycle.Bin`
  - `System Volume Information`
  - `pagefile.sys`, `hiberfil.sys`, `swapfile.sys`
  - `C:\Windows\WinSxS`
  - `C:\Windows\SoftwareDistribution`

### 4.3 Windows Autostart
Toggle **Launch on Windows Startup** to automatically start Findora in the system tray upon user login via `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`.

---

## 5. Command-Line Interface (CLI Mode)

The backend includes a standalone CLI mode for headless servers, scripts, or testing:

```powershell
# Launch interactive CLI search
python src\Findora.Backend\main.py --cli

# Launch with custom database path
python src\Findora.Backend\main.py --cli --db "D:\CustomIndex\findora.db"

# Trigger a background re-index
python src\Findora.Backend\main.py --rescan
```

### CLI Commands Available:
- `0`: Exit CLI mode.
- `1`: Print in-memory B+ Tree structure sample.
- `2`: Search for a filename (benchmarks search time in milliseconds).
- `3`: Rescan all attached drives and output timing statistics.
