; Inno Setup Script for DataFerns Fim Analyser v3.0
; Compiles the build from dist/DataFerns-Analyser into a single installer executable.

#define MyAppName "DataFerns FIM Analyser"
#define MyAppVersion "3.0"
#define MyAppPublisher "DataFerns"
#define MyAppExeName "DataFerns-Analyser.exe"

[Setup]
AppId={{588DD940-8E14-47FF-8F85-C85FF485E6BC}
AppName={#MyAppName} v{#MyAppVersion}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} v{#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\DataFerns Fim Analyser
DefaultGroupName=DataFerns Fim Analyser
OutputDir=.
OutputBaseFilename=FIM_Analyzer_Setup_v3.0
SetupIconFile=dcr_python\src\ui\logo.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=auto

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\DataFerns-Analyser\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName} v{#MyAppVersion}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\_internal\src\ui\logo.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName} v{#MyAppVersion}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\_internal\src\ui\logo.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName} v{#MyAppVersion}}"; Flags: nowait postinstall skipifsilent
