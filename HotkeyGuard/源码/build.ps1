$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "== 1/2 生成图标 =="
python make_icon.py

Write-Host "== 2/2 PyInstaller 打包 =="
python -m PyInstaller --noconfirm --clean --onefile --noconsole `
  --name HotkeyGuard `
  --icon icon.ico `
  --add-data "icon.ico;." `
  --add-data "icon.png;." `
  --collect-all customtkinter `
  main.py

Write-Host "完成: dist\HotkeyGuard.exe"
