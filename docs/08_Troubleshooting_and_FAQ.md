# 8. Troubleshooting and FAQ

## 8.1 Antivirus False Positives (Windows Defender)
A highly common issue with Python applications compiled via `PyInstaller` is that Windows Defender or corporate IT Antivirus suites will flag the `.exe` as a generic trojan or malware (e.g., `Win32/Wacatac` or `Trojan:Win32/Zpevdo`).

**Why this happens:** PyInstaller bundles a Python runtime and compresses it using UPX. Antivirus software hates self-extracting executables because it cannot easily read inside the package, and assumes malicious intent.

**The Solution:**
1. This is a highly documented false positive.
2. The client's IT team must add an **Exclusion/Whitelist** for either the specific `DataFerns-Analyser.exe` file or the `DataFerns Fim Analyser` installation directory.
3. If complete organizational avoidance is needed long-term, the executable must be compiled using a certified **Code Signing Certificate**.

## 8.2 Developer Environment Setup
If the codebase needs to be transferred to a new laptop or sent to an auxiliary developer, the environment must strictly mirror the current setup to prevent library conflicts (especially with `pandas` and `PyQt5`).

**Recreation Command:**
1. Install Python 3.12 natively.
2. Initialize a virtual environment via terminal in the root directory:
   `python -m venv venv`
3. Activate the environment:
   `.\venv\Scripts\Activate.ps1` (Powershell)
4. Push all required dependencies using the explicit requirements document:
   `pip install -r dcr_python/requirements.txt`

## 8.3 Logging and Crash Diagnosis
By design, the compiled graphical distribution of DataFerns Analyser operates silently. The `.spec` configuration utilizes `console=False`, meaning the terminal window stays hidden to provide a clean user experience.

However, if the application ever experiences a "Silent Crash" (closes instantly during loading or upon clicking "Generate"):
1. The developer must return to the source code folder and run the application explicitly through the terminal:
   `$env:PYTHONPATH = "dcr_python"; python -m src.ui.fim_loader`
2. This will map all internal `Traceback` lines directly to the open console, identifying exactly which `IndexError`, `FileNotFoundError`, or bad byte triggered the system termination.
3. Common crash reasons include feeding an empty `.fim` file (0 KB), or the target system locking the Excel Output path due to active OneDrive synchronization or file permissions.
