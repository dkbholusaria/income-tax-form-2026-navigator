; ============================================================
;  Inno Setup Script — IT Forms Downloader 2026
; ============================================================
;
;  Prerequisites:
;    1. Build the EXE first:  python build_exe.py
;    2. Install Inno Setup:   https://jrsoftware.org/isinfo.php
;    3. Open this file in Inno Setup Compiler and click Build
;       Or run from command line:
;         "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
;
;  Output:
;    Output\ITFormsDownloader_Setup_1.0.0.exe
; ============================================================

#define MyAppName       "Income Tax Form 2026 Navigator"
#define MyAppVersion    "1.0.0"
#define MyAppPublisher  "CA. Deepak Bholusaria | DAKSM AND CO LLP"
#define MyAppURL        "https://www.incometaxindia.gov.in"
#define MyAppExeName    "ITFormsDownloader.exe"

[Setup]
AppId={{A8F2C3D4-E5B6-47A8-9C01-2D3E4F5A6B7C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} v{#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
DefaultDirName={autopf}\ITFormsDownloader
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=Output
OutputBaseFilename=ITFormsDownloader_Setup_{#MyAppVersion}
SetupIconFile=app_icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
WizardSizePercent=110
PrivilegesRequired=lowest
DisableProgramGroupPage=yes
LicenseFile=
InfoBeforeFile=
InfoAfterFile=

; Minimum Windows version
MinVersion=10.0

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Main EXE (built by PyInstaller)
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; Icon file
Source: "app_icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\app_icon.ico"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\app_icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
