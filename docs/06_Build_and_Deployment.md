# 6. Build and Deployment

## 6.1 PyInstaller Specification (`DataFerns.spec`)
For portability, the application is bundled into a single standalone `.exe` using PyInstaller. 

### Core Bundling Directives
The `DataFerns.spec` file strictly defines what elements make it into the executable payload. 
The critical line is the specific inclusion of external graphical assets (the report template):
```python
datas=[
    ('dcr_python/src/report-template.xlsx', 'src/'),
]
```
During runtime, PyInstaller unwraps this asset into a temporary hidden folder named `_MEIPASS`.

### Asset Resolution (`utils/helpers.py`)
To prevent `File Not Found` errors when moving the executable between machines, the `resource_path` function dynamically discovers if the user is running the raw Python script or the compiled Executable. If compiled, it automatically patches directory requests to point securely intercept the `_MEIPASS` temp folder.

## 6.2 Inno Setup (`DataFerns_Setup.iss`)
The resulting Pyinstaller build is packaged via Inno Setup (`ISCC.exe`) to create the final deployment wizard `DataFerns_Setup.exe`.
This configuration automatically establishes:
1.  Installation inside the Windows `Program Files` directory (`{app}`).
2.  Creation of normalized Start Menu definitions.
3.  Optional Desktop shortcut mappings targeting the embedded `DataFerns-Analyser.exe`.
