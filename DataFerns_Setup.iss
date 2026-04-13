; Inno Setup Script for DataFerns Fim Analyser

[Setup]
AppId={{588DD940-8E14-47FF-8F85-C85FF485E6BC}
AppName=DataFerns Fim Analyser
AppVersion=1.0
AppPublisher=DataFerns
DefaultDirName={autopf}\DataFerns Fim Analyser
DefaultGroupName=DataFerns Fim Analyser
OutputDir=.
OutputBaseFilename=DataFerns_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "c:\Users\suppo\OneDrive\Desktop\DataFerns-Fim-Analyser\dist\DataFerns-Analyser\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\DataFerns Fim Analyser"; Filename: "{app}\DataFerns-Analyser.exe"
Name: "{autodesktop}\DataFerns Fim Analyser"; Filename: "{app}\DataFerns-Analyser.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\DataFerns-Analyser.exe"; Description: "{cm:LaunchProgram,DataFerns Fim Analyser}"; Flags: nowait postinstall skipifsilent
