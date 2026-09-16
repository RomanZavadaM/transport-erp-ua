#ifndef MyAppVersion
  #define MyAppVersion "0.2-r8"
#endif
#ifndef BundleDir
  #define BundleDir "dist\TransportERP-UA_v0_2_TEST_r8_Windows_x64"
#endif
#ifndef OutputBaseFilename
  #define OutputBaseFilename "TransportERP-UA_v0_2_TEST_r8_Setup_Windows_x64"
#endif

[Setup]
AppId={{B1E1D0A7-2F20-4B98-91D6-8D84FC77C7B4}
AppName=TransportERP-UA
AppVersion={#MyAppVersion}
AppPublisher=RomanZavadaM
DefaultDirName={localappdata}\Programs\TransportERP-UA
DefaultGroupName=TransportERP-UA
OutputDir=..\release_out
OutputBaseFilename={#OutputBaseFilename}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\TransportERP-UA.exe
SetupLogging=yes

[Tasks]
Name: "desktopicon"; Description: "Створити ярлик на робочому столі"; GroupDescription: "Додаткові ярлики:"; Flags: unchecked

[Files]
Source: "..\{#BundleDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\TransportERP-UA"; Filename: "{app}\TransportERP-UA.exe"
Name: "{autodesktop}\TransportERP-UA"; Filename: "{app}\TransportERP-UA.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\TransportERP-UA.exe"; Description: "Запустити TransportERP-UA"; Flags: nowait postinstall skipifsilent
