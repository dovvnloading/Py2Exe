## Changelog: Py2Exe GUI - [v1.1.0] 10/24/2025 - 10:23pm EC/ATz

This update introduces a major new feature for asset management and a key user interface improvement for a more robust and predictable layout.

### Added

*   **Asset Management for Data Files:** A new "Assets" tab has been added to the main interface, providing comprehensive support for bundling non-code files with the final executable.
    *   **New UI Panel:** An "Assets" tab is now available, allowing users to specify files and folders to be included in the build.
    *   **File and Folder Addition:** Users can now add individual files or entire directories through dedicated "Add File(s)..." and "Add Folder..." buttons, which utilize the system's native file dialogs.
    *   **Interactive Asset Table:** Included assets are displayed in a table view with two columns: "Source Path" (the location on the local disk) and "Destination in App" (the target directory within the bundled application, e.g., `.` or `assets/`).
    *   **Build Process Integration:** The build worker has been enhanced to process the list of assets and correctly format them into `--add-data` arguments for the PyInstaller command-line tool.

### Fixed

*   **Main Splitter Layout Stability:** The primary horizontal splitter, which separates the left-side configuration tabs from the right-side build log, can no longer be collapsed. The splitter handle now has a hard stop that prevents the user from dragging it past the minimum width of the left-hand panel. This ensures the core application options are always visible and accessible.
