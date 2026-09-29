; Instalador de "Descargador y Conversor" (Inno Setup 6).
; Compilar:  ISCC.exe installer\instalador.iss   (o construir_instalador.ps1)
; Requiere que antes exista dist\DescargadorYConversor\ (PyInstaller).

#define AppName "Descargador y Conversor"
#define AppVersion "1.0.0"
#define AppPublisher "Genaro Velasco"
#define AppURL "https://github.com/Gatotote/descargador-y-conversor"
#define AppExe "DescargadorYConversor.exe"

[Setup]
AppId={{7E1C6A2B-9D4F-4B7A-8C21-DC0FE0B4A911}}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
DefaultDirName={autopf}\Descargador y Conversor
DefaultGroupName=Descargador y Conversor
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#AppExe}
OutputDir=..\Output
OutputBaseFilename=DescargadorYConversor-{#AppVersion}-Setup
SetupIconFile=..\assets\icono.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin

[Languages]
Name: "es"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear un acceso directo en el Escritorio"; GroupDescription: "Accesos directos:"
Name: "ffmpeg"; Description: "Instalar FFmpeg con winget (para convertir y bajar MP3)"; GroupDescription: "Componentes recomendados:"; Check: WingetDisponible
Name: "deno"; Description: "Instalar Deno con winget (para descargar de YouTube)"; GroupDescription: "Componentes recomendados:"; Check: WingetDisponible

[Files]
Source: "..\dist\DescargadorYConversor\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion createallsubdirs

[Icons]
Name: "{group}\Descargador y Conversor"; Filename: "{app}\{#AppExe}"
Name: "{group}\Desinstalar Descargador y Conversor"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Descargador y Conversor"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{cmd}"; Parameters: "/c winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements"; \
  StatusMsg: "Instalando FFmpeg (winget)..."; Flags: runhidden runasoriginaluser waituntilterminated; Tasks: ffmpeg
Filename: "{cmd}"; Parameters: "/c winget install --id DenoLand.Deno -e --accept-source-agreements --accept-package-agreements"; \
  StatusMsg: "Instalando Deno (winget)..."; Flags: runhidden runasoriginaluser waituntilterminated; Tasks: deno
Filename: "{app}\{#AppExe}"; Description: "Abrir Descargador y Conversor"; Flags: nowait postinstall skipifsilent

[Code]
function WingetDisponible(): Boolean;
var
  ResultCode: Integer;
begin
  Result := Exec('cmd.exe', '/c where winget', '', SW_HIDE, ewWaitUntilTerminated, ResultCode)
            and (ResultCode = 0);
end;
