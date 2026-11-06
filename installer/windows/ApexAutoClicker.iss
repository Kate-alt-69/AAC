#ifndef ProductVersion
  #define ProductVersion "1.1"
#endif
#ifndef ReleaseVersion
  #define ReleaseVersion "1.0.0"
#endif
#ifndef AppExe
  #define AppExe "..\..\dist\windows\app\apex-autoclicker.exe"
#endif

[Setup]
AppId={{D17F5A3C-6B4E-4A73-9D51-8DA49F6A5011}
AppName=Apex Auto-Clicker
AppVersion={#ProductVersion}
AppVerName=Apex Auto-Clicker {#ProductVersion} (v{#ReleaseVersion})
AppPublisher=Kastrick
LicenseFile=..\..\LICENSE
AppPublisherURL=https://github.com/Kate-alt-69/AAC
AppSupportURL=https://github.com/Kate-alt-69/AAC/issues
DefaultDirName={autopf}\kastrick's_software\aac
DefaultGroupName=Apex Auto-Clicker
DisableProgramGroupPage=yes
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UsePreviousAppDir=yes
OutputDir=..\..\dist\installers
OutputBaseFilename=Apex-Auto-Clicker-Setup-{#ReleaseVersion}-x64
UninstallDisplayIcon={app}\apex-autoclicker.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
Source: "{#AppExe}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\LICENSE"; DestDir: "{app}"; DestName: "LICENSE.txt"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\Apex Auto-Clicker"; Filename: "{app}\apex-autoclicker.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\Apex Auto-Clicker"; Filename: "{app}\apex-autoclicker.exe"; WorkingDir: "{app}"; Tasks: desktopicon
