@echo off
chcp 65001 >nul
title RemoteMouse
cd /d "%~dp0"
C:\Python314\python.exe server.py
pause
