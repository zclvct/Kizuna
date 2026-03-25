; Kizuna - Inno Setup 安装脚本
; 使用方法: 在 Inno Setup Compiler 中打开此文件并编译
; 下载 Inno Setup: https://jrsoftware.org/isdl.php

#define MyAppName "Kizuna"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Kizuna"
#define MyAppExeName "Kizuna.exe"
#define MyAppDescription "二次元桌面助手"

[Setup]
; 应用信息
AppId={{8F3D5A7B-1234-5678-9ABC-DEF012345678}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL=https://github.com/yourname/Kizuna
AppSupportURL=https://github.com/yourname/Kizuna
AppUpdatesURL=https://github.com/yourname/Kizuna

; 安装目录
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}

; 输出设置
OutputDir=dist\installer
OutputBaseFilename=Kizuna_Setup_v{#MyAppVersion}
SetupIconFile=assets\images\icon.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern

; 权限
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog

; 界面
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}

; 许可协议（可选）
; LicenseFile=LICENSE.txt

; 系统要求
MinVersion=10.0
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

; 其他设置
DisableProgramGroupPage=yes
DisableWelcomePage=no

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; 复制所有文件
Source: "dist\Kizuna\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; 开始菜单快捷方式
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
; 桌面快捷方式
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; 安装完成后运行
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
// 检查是否已安装
function InitializeSetup(): Boolean;
var
    OldVersion: String;
begin
    // 检查注册表中是否有旧版本
    if RegQueryStringValue(HKEY_LOCAL_MACHINE,
        'Software\Microsoft\Windows\CurrentVersion\Uninstall\{#MyAppName}_is1',
        'UninstallString', OldVersion) then
    begin
        if MsgBox('检测到已安装 {#MyAppName}，是否先卸载旧版本？', mbConfirmation, MB_YESNO) = IDYES then
        begin
            OldVersion := RemoveQuotes(OldVersion);
            Exec(OldVersion, '/SILENT', '', SW_HIDE, ewWaitUntilTerminated, Result);
        end;
    end;
    Result := True;
end;
