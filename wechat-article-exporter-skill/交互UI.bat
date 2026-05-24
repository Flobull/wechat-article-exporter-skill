@echo off
chcp 65001 >nul
title 微信公众号文章下载工具 - TUI
cd /d "%~dp0"
python wechat.py ui
