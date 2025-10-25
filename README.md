<img width="1024" height="492" alt="bnr_1" src="https://github.com/user-attachments/assets/7820a793-70c4-4632-ab56-b8f2ea8e4ce1" />

# Py2Exe

A modern, professional Graphical User Interface for the powerful PyInstaller toolchain.

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![UI Framework](https://img.shields.io/badge/UI-PySide6-2796EC)](https://www.qt.io/qt-for-python)
[![Built with](https://img.shields.io/badge/Built%20with-PyInstaller-informational)](https://pyinstaller.org/)

Py2Exe provides an intuitive and powerful front-end for PyInstaller, allowing developers to package their Python applications into standalone executables without memorizing command-line arguments. It exposes basic, advanced, and asset-related PyInstaller features in a clean, themeable, and easy-to-navigate interface.

## Features

- **Intuitive UI**: A clean, tabbed interface separates basic, advanced, package, and asset options.
- **Full Asset Management**: A dedicated "Assets" tab allows for easy inclusion of data files and folders (e.g., images, configs, fonts). Specify the source path and the destination directory within your bundled app.
- **Light & Dark Themes**: Switch between themes for comfortable viewing in any environment. The application can also theme the window's title bar on modern Windows systems.
- **Real-time Build Log**: A side-by-side log panel provides immediate feedback on the build process.
- **Syntax Highlighting**: Critical log messages like `[ERROR]`, `[SUCCESS]`, and `[WARNING]` are color-coded for quick identification.
- **Comprehensive Options**: Access a wide range of PyInstaller features:
  - One-file or one-directory bundling
  - Windowed or console application type
  - Custom icon assignment
  - Management of output directories (dist, build, spec)
  - Pre-build cleaning and binary stripping
  - UPX compression control
  - Inclusion of hidden imports and data collection
- **Robust & Stable**: The UI is designed with a fixed window and a non-collapsible settings panel to prevent layout issues and ensure a consistent user experience.

## Demonstration

The application provides a seamless workflow from configuration to final build.

![Py2Exe Application Demo](https://github.com/user-attachments/assets/e602ac87-7d23-4d8f-9fbd-6c794d860a14)

<details>
<summary>View Application Screenshots</summary>
  
| | |
| :---: | :---: |
| <img width="470" alt="Py2Exe Basic Options Tab" src="https://github.com/user-attachments/assets/16744af5-4586-447a-9b59-d066dfb5b14f" /> | <img width="470" alt="Py2Exe Advanced Options Tab" src="https://github.com/user-attachments/assets/db56db9e-eb60-4887-bbec-de1350e88c18" /> |
| <img width="470" alt="Py2Exe Package Management Tab" src="https://github.com/user-attachments/assets/7704f714-d0c2-4805-8d23-8cdfc94905b4" /> | <img width="470" alt="Py2Exe Assets Tab" src="https://github.com/user-attachments/assets/a7a38fc7-2ee6-4eba-a1be-390215a61329" /> |

</details>


## Getting Started

Follow these instructions to get a local copy up and running.

### Prerequisites

- Python 3.8 or newer
- `pip` and `git` installed and available in your system's PATH

### Installation

1.  **Clone the repository:**
    ```sh
    git clone https://github.com/dovvnloading/Py2Exe.git
    cd Py2Exe
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```sh
    # On Windows
    python -m venv venv
    .\venv\Scripts\activate

    # On macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install the required dependencies:**
    ```sh
    pip install PySide6 pyinstaller
    ```

### Usage

Once the dependencies are installed, run the application with the following command:

```sh
python Py2Exe.py
```

## Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

## License

Distributed under the MIT License. See the `LICENSE` file for more information.
