# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-11-13

### Added
- **Windows 11 Glassmorphism Floating UI**:
  - Centered floating search card with rounded corners, drop shadows, and subtle acrylic/mica translucency.
  - Idle draggable circular desktop search widget implementing `WS_EX_NOACTIVATE` and `HWND_NOTOPMOST` to prevent window occlusion and focus-stealing.
  - Dark and Light theme palettes with real-time toggle.
  - Native Windows file icons via Win32 `SHGetFileInfoW` with deterministic GDI handle cleanup (`DestroyIcon`) and caching.
- **Custom B+ Tree Indexing Engine**:
  - In-memory B+ Tree with fanout order 32, supporting sub-millisecond filename queries across 800,000+ files.
  - Multi-path value arrays per filename to seamlessly handle duplicate filenames across different drives and directories.
  - Thread-safe leaf snapshotting during search queries to guarantee safety during concurrent live indexing.
- **Persistent SQLite File Catalog**:
  - WAL (Write-Ahead Logging) storage mode with 32 MB cache in `%LOCALAPPDATA%\Findora\findora.db`.
  - Seamless automatic migration from legacy indexes without re-indexing.
  - Configurable exclusion filters for system files and high-churn paths.
- **Kernel-Level Filesystem Monitoring**:
  - Asynchronous `ReadDirectoryChangesW` engine tracking real-time additions, deletions, modifications, and renames.
  - Serialized mutation queue worker eliminating database lock contention.
  - Startup reconciliation comparing folder modification timestamps against synchronization checkpoints.
- **Asynchronous NDJSON IPC Architecture**:
  - High-throughput parent-child communication over anonymous standard I/O pipes.
  - Correlated request-response lifecycle with integer identifiers.
  - Automatic backend supervisor recovery upon unexpected child process crashes.
- **Global Hotkey Integration**:
  - Windows global shortcut listener (`Ctrl + Alt + F`) via Win32 `RegisterHotKey`.
- **Standalone Windows Distribution**:
  - Automated release packaging script (`build\build_release.ps1`) bundling frontend and PyInstaller backend into `dist\Findora\`.
- **Test Suites**:
  - 65 Python unit and integration tests covering the B+ Tree, SQLite persistence, mutation queue, scanner, watcher, reconciler, and IPC.
  - C# xUnit test suite covering WPF item formatting, icon normalization, IPC serialization, process recovery, and action execution.
