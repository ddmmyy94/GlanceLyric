#define AppVersion "1.1.0"
#define AppName "GlanceLyric"

[Setup]
AppId={{5BEF9027-7064-4672-A368-D476937B162D}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=ddmmyy94
AppPublisherURL=https://github.com/ddmmyy94/GlanceLyric
AppSupportURL=https://github.com/ddmmyy94/GlanceLyric/issues
AppUpdatesURL=https://github.com/ddmmyy94/GlanceLyric/releases
DefaultDirName={localappdata}\Programs\GlanceLyric
DefaultGroupName=GlanceLyric
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64os
ArchitecturesInstallIn64BitMode=x64os
MinVersion=10.0.17763
LicenseFile=..\LICENSE
SetupIconFile=..\assets\glancelyric.ico
UninstallDisplayIcon={app}\GlanceLyric.exe
OutputDir=..\dist
OutputBaseFilename=GlanceLyric-Setup-{#AppVersion}-x64
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
CloseApplicationsFilter=GlanceLyric.exe
RestartApplications=no

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked
Name: "autostart"; Description: "Start GlanceLyric with Windows (show lyrics when Spotify opens)"; Flags: unchecked

[Files]
Source: "..\dist\GlanceLyric\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "Install.bat,Uninstall.bat,GlanceLyric.bat,Aktifkan-Autostart.bat,Matikan-Autostart.bat,tools\*"

[Icons]
Name: "{group}\GlanceLyric"; Filename: "{app}\GlanceLyric.exe"
Name: "{autodesktop}\GlanceLyric"; Filename: "{app}\GlanceLyric.exe"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "GlanceLyric"; ValueData: """{app}\GlanceLyric.exe"" --watch"; Tasks: autostart; Flags: uninsdeletevalue

[Run]
Filename: "{app}\GlanceLyric.exe"; Parameters: "--watch"; Tasks: autostart; Flags: nowait skipifsilent
Filename: "{app}\GlanceLyric.exe"; Description: "Launch GlanceLyric"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{app}\GlanceLyric.exe"; Parameters: "--uninstall"; Flags: runhidden waituntilterminated; RunOnceId: "RemoveAutostart"
