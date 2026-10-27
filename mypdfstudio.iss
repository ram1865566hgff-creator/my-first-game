; My PDF Studio full offline setup for x64 Windows.
#define AppName "My PDF Studio"
#define AppVersion "1.2.0"
#define AppExe "MyPDFStudio.exe"
[Setup]
AppId={{9B4BA311-CA21-45C6-8AAE-FE7D18A8308D}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=My PDF Studio
DefaultDirName={localappdata}\Programs\My PDF Studio
DefaultGroupName={#AppName}
UninstallDisplayIcon={app}\{#AppExe}
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
DisableProgramGroupPage=yes
WizardStyle=modern
Compression=lzma2/max
SolidCompression=yes
OutputDir=release
OutputBaseFilename=MyPDFStudio_Offline_Setup
SetupLogging=yes
CloseApplications=yes
[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"
[Files]
Source: "dist\MyPDFStudio\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{autoprograms}\My PDF Studio"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\My PDF Studio"; Filename: "{app}\{#AppExe}"
[Run]
Filename: "{app}\{#AppExe}"; Description: "Запустить My PDF Studio"; Flags: nowait postinstall skipifsilent
