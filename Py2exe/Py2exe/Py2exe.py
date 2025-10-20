import sys
import re
import subprocess
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QCheckBox, QFileDialog,
    QTextEdit, QMessageBox, QTabWidget, QScrollArea, QFrame,
    QFormLayout, QGroupBox, QSplitter
)
from PySide6.QtCore import Qt, Signal, QObject, QThread, QSize, QRegularExpression
from PySide6.QtGui import QFont, QColor, QPalette, QIcon, QPixmap, QPainter, QSyntaxHighlighter, QTextCharFormat
from PySide6.QtSvg import QSvgRenderer

# Attempt to import Windows-specific libraries for title bar theming
try:
    import ctypes
    from ctypes import wintypes
    IS_WINDOWS = sys.platform == "win32"
except ImportError:
    IS_WINDOWS = False

# =================================================================================
# Constants: SVG Icons
# =================================================================================

APP_ICON_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"
fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
  <polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline>
  <line x1="12" y1="22.08" x2="12" y2="12"></line>
</svg>
"""

SUN_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"
fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="12" cy="12" r="5"></circle>
  <line x1="12" y1="1" x2="12" y2="3"></line>
  <line x1="12" y1="21" x2="12" y2="23"></line>
  <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
  <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
  <line x1="1" y1="12" x2="3" y2="12"></line>
  <line x1="21" y1="12" x2="23" y2="12"></line>
  <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
  <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
</svg>
"""

MOON_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"
fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
</svg>
"""

# =================================================================================
# Class: LogSyntaxHighlighter
# =================================================================================
class LogSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent, theme_colors):
        super().__init__(parent)
        self.highlighting_rules = []
        self.update_theme(theme_colors)

    def update_theme(self, theme_colors):
        self.highlighting_rules = []

        keywords = {
            'error': r'\[ERROR\]',
            'success': r'\[SUCCESS\]',
            'warning': r'\[WARNING\]',
            'info': r'\[INFO\]',
            'process': r'\[PROCESS\]',
            'config': r'\[CONFIG\]',
        }

        for key, pattern in keywords.items():
            color = theme_colors.get(key, theme_colors['text'])
            text_format = QTextCharFormat()
            text_format.setForeground(QColor(color))
            text_format.setFontWeight(QFont.Weight.Bold)
            self.highlighting_rules.append((QRegularExpression(pattern), text_format))
    
    def highlightBlock(self, text):
        for pattern, text_format in self.highlighting_rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                match = it.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), text_format)

# =================================================================================
# Class: BuildWorker (Background process handler)
# =================================================================================

class BuildWorker(QObject):
    output_signal = Signal(str)
    finished_signal = Signal(bool, str)

    def __init__(self, script_path, options):
        super().__init__()
        self.script_path = script_path
        self.options = options
        self._is_running = True

    def run(self):
        try:
            self.output_signal.emit("[INFO] Starting PyInstaller build process...\n")

            cmd = ["pyinstaller"]

            if self.options.get('one_file'):
                cmd.append("--onefile")
                self.output_signal.emit("[CONFIG] One-file mode enabled\n")
            else:
                cmd.append("--onedir")
                self.output_signal.emit("[CONFIG] One-directory mode enabled\n")

            if self.options.get('windowed'):
                cmd.append("--windowed")
                self.output_signal.emit("[CONFIG] Windowed mode enabled\n")
            else: # PyInstaller defaults to console, but explicit is better
                cmd.append("--console")
                self.output_signal.emit("[CONFIG] Console mode enabled\n")

            icon_path = self.options.get('icon')
            if icon_path:
                if Path(icon_path).is_file():
                    cmd.extend(["--icon", icon_path])
                    self.output_signal.emit(f"[CONFIG] Icon: {icon_path}\n")
                else:
                    self.output_signal.emit(f"[WARNING] Icon file not found at: {icon_path}. Build will proceed with the default icon.\n")

            cmd.extend(["-n", self.options['name']])
            self.output_signal.emit(f"[CONFIG] Output name: {self.options['name']}\n")

            if self.options.get('distpath'):
                cmd.extend(["--distpath", self.options['distpath']])
                self.output_signal.emit(f"[CONFIG] Distribution path: {self.options['distpath']}\n")

            if self.options.get('workpath'):
                cmd.extend(["--workpath", self.options['workpath']])
                self.output_signal.emit(f"[CONFIG] Work path: {self.options['workpath']}\n")

            if self.options.get('specpath'):
                cmd.extend(["--specpath", self.options['specpath']])
                self.output_signal.emit(f"[CONFIG] Spec path: {self.options['specpath']}\n")

            if self.options.get('clean'):
                cmd.append("--clean")
                self.output_signal.emit("[CONFIG] Clean build enabled\n")

            if self.options.get('strip'):
                cmd.append("--strip")
                self.output_signal.emit("[CONFIG] Binary stripping enabled\n")
            
            if self.options.get('upx_dir'):
                cmd.append("--upx-dir=" + self.options['upx_dir'])
                self.output_signal.emit(f"[CONFIG] UPX directory: {self.options['upx_dir']}\n")
            elif self.options.get('noupx'):
                cmd.append("--noupx")
                self.output_signal.emit("[CONFIG] UPX disabled\n")

            if self.options.get('hidden_imports'):
                for imp in self.options['hidden_imports']:
                    cmd.extend(["--hidden-import", imp])
                self.output_signal.emit(f"[CONFIG] Hidden imports: {', '.join(self.options['hidden_imports'])}\n")

            if self.options.get('collect_all'):
                for pkg in self.options['collect_all']:
                    cmd.extend(["--collect-all", pkg])
                self.output_signal.emit(f"[CONFIG] Collect all: {', '.join(self.options['collect_all'])}\n")

            if self.options.get('exclude_modules'):
                for mod in self.options['exclude_modules']:
                    cmd.extend(["--exclude-module", mod])
                self.output_signal.emit(f"[CONFIG] Excluded modules: {', '.join(self.options['exclude_modules'])}\n")

            cmd.append(self.script_path)
            self.output_signal.emit(f"[CONFIG] Script: {self.script_path}\n")
            self.output_signal.emit("\n" + "="*80 + "\n")
            self.output_signal.emit("[PROCESS] Executing PyInstaller...\n\n")

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1
            )

            for line in iter(process.stdout.readline, ''):
                if line:
                    self.output_signal.emit(line)

            process.wait()

            if process.returncode == 0:
                self.output_signal.emit("\n" + "="*80 + "\n")
                self.output_signal.emit("[SUCCESS] Build completed successfully!\n")
                self.finished_signal.emit(True, "Build completed successfully!")
            else:
                self.output_signal.emit("\n" + "="*80 + "\n")
                self.output_signal.emit(f"[ERROR] Build failed with return code {process.returncode}\n")
                self.finished_signal.emit(False, f"Build failed with return code {process.returncode}")

        except FileNotFoundError:
            self.output_signal.emit("[ERROR] Critical: 'pyinstaller' command not found.\n"
                                    "[ERROR] Please ensure PyInstaller is installed and accessible in your system's PATH.\n"
                                    "[ERROR] Installation: pip install pyinstaller\n")
            self.finished_signal.emit(False, "PyInstaller not found or not in PATH.")
        except Exception as e:
            self.output_signal.emit(f"[ERROR] An unexpected error occurred: {str(e)}\n")
            self.finished_signal.emit(False, str(e))

# =================================================================================
# Class: ThemeManager (Handles application styling)
# =================================================================================
class ThemeManager:
    THEMES = {
        "dark": {
            "bg_base": "#212529",
            "bg_raised": "#343A40",
            "bg_sunken": "#191C1F",
            "border": "#495057",
            "text": "#F8F9FA",
            "text_dim": "#ADB5BD",
            "primary": "#0D6EFD",
            "primary_hover": "#0B5ED7",
            "primary_pressed": "#0A58CA",
            "primary_disabled": "#343A40",
            "text_on_primary": "#FFFFFF",
            "text_disabled": "#6C757D",
            "success": "#198754",
            "info": "#0DCAF0",
            "warning": "#FFC107",
            "error": "#DC3545",
            "process": "#6F42C1",
            "config": "#ADB5BD",
        },
        "light": {
            "bg_base": "#F8F9FA",
            "bg_raised": "#FFFFFF",
            "bg_sunken": "#E9ECEF",
            "border": "#DEE2E6",
            "text": "#212529",
            "text_dim": "#6C757D",
            "primary": "#0D6EFD",
            "primary_hover": "#0B5ED7",
            "primary_pressed": "#0A58CA",
            "primary_disabled": "#E9ECEF",
            "text_on_primary": "#FFFFFF",
            "text_disabled": "#ADB5BD",
            "success": "#198754",
            "info": "#0DCAF0",
            "warning": "#FFC107",
            "error": "#DC3545",
            "process": "#6F42C1",
            "config": "#6C757D",
        }
    }

    @staticmethod
    def get_stylesheet(theme_name="light"):
        colors = ThemeManager.THEMES.get(theme_name, ThemeManager.THEMES["light"])
        return f"""
            QWidget {{
                color: {colors['text']};
                font-family: "Segoe UI", "Helvetica Neue", "Arial", sans-serif;
                font-size: 10pt;
            }}
            QMainWindow, QWidget#centralWidget, QFrame#logPanel {{
                background-color: {colors['bg_base']};
            }}
            QTabWidget::pane {{
                border: 1px solid {colors['border']};
                border-top: none;
                background-color: {colors['bg_raised']};
            }}
            QTabBar::tab {{
                background-color: {colors['bg_sunken']};
                color: {colors['text_dim']};
                padding: 8px 20px;
                border: 1px solid {colors['border']};
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            QTabBar::tab:selected {{
                background-color: {colors['bg_raised']};
                color: {colors['primary']};
                border-bottom: 2px solid {colors['primary']};
            }}
            QTabBar::tab:hover {{
                color: {colors['text']};
            }}
            QGroupBox {{
                font-weight: bold;
                color: {colors['text']};
                border: 1px solid {colors['border']};
                border-radius: 4px;
                margin-top: 10px;
                padding: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                left: 10px;
            }}
            QLabel {{
                color: {colors['text']};
            }}
            QLineEdit, QTextEdit {{
                background-color: {colors['bg_sunken']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                border-radius: 4px;
                padding: 5px;
            }}
            QTextEdit#logDisplay {{
                 color: {colors['text_dim']};
            }}
            QLineEdit:focus, QTextEdit:focus {{
                border: 1px solid {colors['primary']};
            }}
            QPushButton {{
                background-color: {colors['bg_raised']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                border-radius: 4px;
                padding: 6px 14px;
            }}
            QPushButton:hover {{
                border-color: {colors['primary_hover']};
            }}
            QPushButton#buildButton {{
                background-color: {colors['primary']};
                color: {colors['text_on_primary']};
                font-weight: bold;
                border: none;
            }}
            QPushButton#buildButton:hover {{
                background-color: {colors['primary_hover']};
            }}
            QPushButton#buildButton:pressed {{
                background-color: {colors['primary_pressed']};
            }}
            QPushButton#buildButton:disabled {{
                background-color: {colors['primary_disabled']};
                color: {colors['text_disabled']};
            }}
            QPushButton#themeButton {{
                border: none;
                background-color: transparent;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 1px solid {colors['border']};
                border-radius: 3px;
            }}
            QCheckBox::indicator:checked {{
                background-color: {colors['primary']};
                border-color: {colors['primary']};
            }}
            QCheckBox::indicator:unchecked:hover {{
                border-color: {colors['primary_hover']};
            }}
            QScrollBar:vertical, QScrollBar:horizontal {{
                border: none;
                background: {colors['bg_sunken']};
                width: 10px;
                height: 10px;
                margin: 0px 0px 0px 0px;
            }}
            QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
                background: {colors['border']};
                min-height: 20px;
                min-width: 20px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {{
                background: {colors['text_dim']};
            }}
            QScrollBar::add-line, QScrollBar::sub-line,
            QScrollBar::add-page, QScrollBar::sub-page {{
                border: none;
                background: none;
                height: 0;
                width: 0;
            }}
            QSplitter::handle {{
                background: {colors['border']};
                border-left: 1px solid {colors['bg_base']};
                border-right: 1px solid {colors['bg_base']};
            }}
            QSplitter::handle:horizontal {{
                width: 3px;
            }}
        """

# =================================================================================
# Class: PathSelectorWidget (Reusable UI Component)
# =================================================================================
class PathSelectorWidget(QWidget):
    def __init__(self, label_text, browse_title, file_filter="", is_directory=False):
        super().__init__()
        self.browse_title = browse_title
        self.file_filter = file_filter
        self.is_directory = is_directory

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.line_edit = QLineEdit()
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.browse)

        layout.addWidget(self.line_edit)
        layout.addWidget(browse_button)
        self.setLayout(layout)

    def browse(self):
        if self.is_directory:
            path = QFileDialog.getExistingDirectory(self, self.browse_title)
        else:
            path, _ = QFileDialog.getOpenFileName(self, self.browse_title, "", self.file_filter)
        
        if path:
            self.line_edit.setText(path)

    def text(self):
        return self.line_edit.text().strip()

    def setText(self, text):
        self.line_edit.setText(text)

# =================================================================================
# Classes: UI Tabs
# =================================================================================
class BasicOptionsTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Main Script & App Name Group
        main_group = QGroupBox("Core Application")
        main_layout = QFormLayout(main_group)
        main_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        self.script_input = PathSelectorWidget("Python Script", "Select Python Script", "Python Files (*.py *.pyw)")
        self.script_input.line_edit.textChanged.connect(self._auto_fill_app_name)
        self.app_name_input = QLineEdit("MyApp")
        self.icon_input = PathSelectorWidget("Icon File", "Select Icon File", "Icon Files (*.ico)")
        main_layout.addRow("Script Path:", self.script_input)
        main_layout.addRow("Application Name:", self.app_name_input)
        main_layout.addRow("Icon (.ico):", self.icon_input)
        layout.addWidget(main_group)

        # Output Directories Group
        paths_group = QGroupBox("Output Directories")
        paths_layout = QFormLayout(paths_group)
        paths_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        self.distpath_input = PathSelectorWidget("Distribution Path", "Select Distribution Folder", is_directory=True)
        self.workpath_input = PathSelectorWidget("Build Path", "Select Build Folder", is_directory=True)
        self.specpath_input = PathSelectorWidget("Spec Path", "Select Spec Folder", is_directory=True)
        paths_layout.addRow("Dist Path (Output):", self.distpath_input)
        paths_layout.addRow("Build Path (Work):", self.workpath_input)
        paths_layout.addRow("Spec Path:", self.specpath_input)
        layout.addWidget(paths_group)

        # Packaging Options Group
        packaging_group = QGroupBox("Packaging Options")
        packaging_layout = QHBoxLayout(packaging_group)
        self.one_file_check = QCheckBox("One-File Executable")
        self.one_file_check.setChecked(True)
        self.windowed_check = QCheckBox("Windowed (No Console)")
        packaging_layout.addWidget(self.one_file_check)
        packaging_layout.addWidget(self.windowed_check)
        packaging_layout.addStretch()
        layout.addWidget(packaging_group)

        layout.addStretch()

    def _auto_fill_app_name(self, script_path):
        if self.app_name_input.text() == "MyApp" or not self.app_name_input.text():
            try:
                p = Path(script_path)
                if p.is_file():
                    self.app_name_input.setText(p.stem)
            except Exception:
                pass # Ignore invalid paths during typing

    def get_options(self):
        return {
            'script': self.script_input.text(),
            'name': self.app_name_input.text().strip() or "MyApp",
            'icon': self.icon_input.text() or None,
            'distpath': self.distpath_input.text() or None,
            'workpath': self.workpath_input.text() or None,
            'specpath': self.specpath_input.text() or None,
            'one_file': self.one_file_check.isChecked(),
            'windowed': self.windowed_check.isChecked(),
        }

class AdvancedOptionsTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Build Options Group
        build_group = QGroupBox("Build Process")
        build_layout = QHBoxLayout(build_group)
        self.clean_check = QCheckBox("Clean Build")
        self.clean_check.setToolTip("Remove PyInstaller cache and temporary files before building.")
        self.strip_check = QCheckBox("Strip Binaries")
        self.strip_check.setToolTip("Apply a symbol-table strip to the executable and shared libraries.")
        build_layout.addWidget(self.clean_check)
        build_layout.addWidget(self.strip_check)
        build_layout.addStretch()
        layout.addWidget(build_group)
        
        # UPX Compression Group
        upx_group = QGroupBox("UPX Compression")
        upx_layout = QFormLayout(upx_group)
        upx_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        self.upx_dir_input = PathSelectorWidget("UPX Directory", "Select UPX Directory", is_directory=True)
        self.noupx_check = QCheckBox("Disable UPX")
        upx_layout.addRow("UPX Path:", self.upx_dir_input)
        upx_layout.addRow("", self.noupx_check)
        layout.addWidget(upx_group)
        
        layout.addStretch()
    
    def get_options(self):
        return {
            'clean': self.clean_check.isChecked(),
            'strip': self.strip_check.isChecked(),
            'upx_dir': self.upx_dir_input.text() or None,
            'noupx': self.noupx_check.isChecked(),
        }

class PackagesTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        hidden_group = QGroupBox("Hidden Imports")
        hidden_layout = QVBoxLayout(hidden_group)
        self.hidden_imports_edit = QTextEdit()
        self.hidden_imports_edit.setPlaceholderText("e.g., numpy, pandas. A new module on each line.")
        hidden_layout.addWidget(self.hidden_imports_edit)
        layout.addWidget(hidden_group)

        collect_group = QGroupBox("Collect All")
        collect_layout = QVBoxLayout(collect_group)
        self.collect_all_edit = QTextEdit()
        self.collect_all_edit.setPlaceholderText("e.g., sklearn, scipy. A new package on each line.")
        collect_layout.addWidget(self.collect_all_edit)
        layout.addWidget(collect_group)

        exclude_group = QGroupBox("Exclude Modules")
        exclude_layout = QVBoxLayout(exclude_group)
        self.exclude_modules_edit = QTextEdit()
        self.exclude_modules_edit.setPlaceholderText("e.g., tkinter, tests. A new module on each line.")
        exclude_layout.addWidget(self.exclude_modules_edit)
        layout.addWidget(exclude_group)

    def get_options(self):
        hidden_imports = [line.strip() for line in self.hidden_imports_edit.toPlainText().split('\n') if line.strip()]
        collect_all = [line.strip() for line in self.collect_all_edit.toPlainText().split('\n') if line.strip()]
        exclude_modules = [line.strip() for line in self.exclude_modules_edit.toPlainText().split('\n') if line.strip()]
        return {
            'hidden_imports': hidden_imports,
            'collect_all': collect_all,
            'exclude_modules': exclude_modules,
        }

# =================================================================================
# Class: PyInstallerGUI (Main Application Window)
# =================================================================================
class PyInstallerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_theme = "light"
        self.build_thread = None
        self.build_worker = None
        self.log_highlighter = None

        self.setWindowTitle("Py2Exe")
        self.setFixedSize(960, 850)

        app_icon_color = ThemeManager.THEMES["light"]["primary"]
        app_icon = self._create_icon_from_svg(APP_ICON_SVG, app_icon_color)
        self.setWindowIcon(app_icon)
        QApplication.instance().setWindowIcon(app_icon)

        self._init_ui()
        self.apply_theme("light")

    def _init_ui(self):
        central_widget = QWidget(objectName="centralWidget")
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        header = self._create_header()
        main_layout.addWidget(header)
        
        # Main content splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter, 1)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setMinimumWidth(500)
        self.basic_tab = BasicOptionsTab()
        self.advanced_tab = AdvancedOptionsTab()
        self.packages_tab = PackagesTab()
        self.tabs.addTab(self.basic_tab, "Basic Options")
        self.tabs.addTab(self.advanced_tab, "Advanced Options")
        self.tabs.addTab(self.packages_tab, "Package Management")
        
        # Log Panel
        log_panel = self._create_log_panel()

        splitter.addWidget(self.tabs)
        splitter.addWidget(log_panel)
        splitter.setSizes([500, 460])

    def _create_header(self):
        header_widget = QFrame()
        header_widget.setObjectName("header")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(15, 10, 15, 10)

        title = QLabel("Py2Exe")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        
        self.theme_button = QPushButton()
        self.theme_button.setObjectName("themeButton")
        self.theme_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_button.setIconSize(QSize(24, 24))
        self.theme_button.clicked.connect(self.toggle_theme)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.theme_button)
        return header_widget

    def _create_log_panel(self):
        log_panel = QFrame()
        log_panel.setObjectName("logPanel")
        log_layout = QVBoxLayout(log_panel)
        log_layout.setContentsMargins(15, 15, 15, 15)
        log_layout.setSpacing(10)

        control_layout = QHBoxLayout()
        log_label = QLabel("Build Log")
        log_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        
        self.clear_log_button = QPushButton("Clear Log")
        self.clear_log_button.clicked.connect(self.clear_log)
        self.build_button = QPushButton("Start Build")
        self.build_button.setObjectName("buildButton")
        self.build_button.setMinimumHeight(38)
        self.build_button.clicked.connect(self.start_build)
        
        control_layout.addWidget(log_label)
        control_layout.addStretch()
        control_layout.addWidget(self.clear_log_button)
        control_layout.addWidget(self.build_button)
        
        self.log_display = QTextEdit()
        self.log_display.setObjectName("logDisplay")
        self.log_display.setReadOnly(True)
        self.log_display.setFont(QFont("Consolas", 9))
        self.log_display.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)

        log_layout.addLayout(control_layout)
        log_layout.addWidget(self.log_display)
        return log_panel

    def _create_icon_from_svg(self, svg_data, color):
        colored_svg = svg_data.replace('currentColor', color)
        renderer = QSvgRenderer(colored_svg.encode('utf-8'))
        pixmap = QPixmap(renderer.defaultSize())
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        return QIcon(pixmap)
        
    def _set_windows_titlebar_theme(self, theme_name):
        if not IS_WINDOWS:
            return

        try:
            # DwmSetWindowAttribute(HWND, DWMWA_USE_IMMERSIVE_DARK_MODE, &value, sizeof(value))
            hwnd = self.winId()
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            value = wintypes.DWORD(1 if theme_name == "dark" else 0)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_USE_IMMERSIVE_DARK_MODE,
                ctypes.byref(value),
                ctypes.sizeof(value)
            )
        except (AttributeError, TypeError, NameError):
            # This can fail if dwmapi is not available or ctypes is misconfigured
            pass

    def apply_theme(self, theme_name):
        self.current_theme = theme_name
        self.setStyleSheet(ThemeManager.get_stylesheet(theme_name))
        
        colors = ThemeManager.THEMES[theme_name]
        icon_color = colors["text"]
        
        if theme_name == "dark":
            self.theme_button.setIcon(self._create_icon_from_svg(SUN_SVG, icon_color))
            self.theme_button.setToolTip("Switch to Light Theme")
        else:
            self.theme_button.setIcon(self._create_icon_from_svg(MOON_SVG, icon_color))
            self.theme_button.setToolTip("Switch to Dark Theme")
        
        if self.log_highlighter is None:
            self.log_highlighter = LogSyntaxHighlighter(self.log_display.document(), colors)
        else:
            self.log_highlighter.update_theme(colors)
            self.log_highlighter.rehighlight()

        self._set_windows_titlebar_theme(theme_name)

    def toggle_theme(self):
        if self.current_theme == "light":
            self.apply_theme("dark")
        else:
            self.apply_theme("light")
    
    def start_build(self):
        basic_opts = self.basic_tab.get_options()
        script_path = basic_opts.pop('script')

        if not script_path:
            QMessageBox.warning(self, "Validation Error", "Please select a Python script to build.")
            return
        
        if not Path(script_path).exists():
            QMessageBox.critical(self, "File Not Found", f"The script '{script_path}' does not exist.")
            return

        self.build_button.setEnabled(False)
        self.build_button.setText("Building...")
        self.clear_log()

        options = {}
        options.update(basic_opts)
        options.update(self.advanced_tab.get_options())
        options.update(self.packages_tab.get_options())

        self.build_worker = BuildWorker(script_path, options)
        self.build_worker.output_signal.connect(self.append_log)
        self.build_worker.finished_signal.connect(self.build_finished)

        self.build_thread = QThread()
        self.build_worker.moveToThread(self.build_thread)
        self.build_thread.started.connect(self.build_worker.run)
        self.build_thread.start()

    def append_log(self, text):
        # The syntax highlighter now handles all coloring automatically.
        # This method just needs to append the text.
        self.log_display.moveCursor(self.log_display.textCursor().MoveOperation.End)
        self.log_display.insertPlainText(text)
        self.log_display.verticalScrollBar().setValue(self.log_display.verticalScrollBar().maximum())

    def clear_log(self):
        self.log_display.clear()

    def build_finished(self, success, message):
        self.build_button.setEnabled(True)
        self.build_button.setText("Start Build")
        if self.build_thread:
            self.build_thread.quit()
            self.build_thread.wait()
            self.build_thread = None
        
        if not success:
            QMessageBox.critical(self, "Build Failed", message)

    def closeEvent(self, event):
        if self.build_thread and self.build_thread.isRunning():
            reply = QMessageBox.question(self, 'Confirm Exit', 
                                         "A build is currently in progress. Are you sure you want to exit?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                         QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


# =================================================================================
# Main Execution Block
# =================================================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PyInstallerGUI()
    window.show()
    sys.exit(app.exec())