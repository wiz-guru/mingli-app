@echo off
chcp 65001 >nul
title 紫微命理 App
cd /d "%USERPROFILE%\mingli-app"

if "%ANTHROPIC_API_KEY%"=="" (
  echo.
  echo  [提示] 没检测到 ANTHROPIC_API_KEY 环境变量。
  echo.
  echo  请先在 PowerShell 里运行一次（之后永久生效，不用再设）：
  echo.
  echo      setx ANTHROPIC_API_KEY "你的真key"
  echo.
  echo  设置完关掉所有终端，再重新双击本文件即可。
  echo.
  pause
  exit /b
)

echo  正在启动命理 App... 浏览器将自动打开 http://localhost:8000
echo  （首次打开若空白，等 2 秒刷新一下；关闭本窗口即停止服务）
start "" http://localhost:8000
"%LOCALAPPDATA%\Programs\Python\Python312\python.exe" server.py
pause
