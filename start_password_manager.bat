@echo off
chcp 65001 > nul
cd /d %~dp0

REM Pythonのパスを明示的に指定
set PYTHON_PATH=C:\Users\kawabata\AppData\Local\Microsoft\WindowsApps\python.exe

if not exist venv (
    echo 仮想環境をセットアップしています...
    %PYTHON_PATH% -m venv venv
)

call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt --no-warn-script-location

echo パスワードマネージャーを起動しています...
python src/main.py
pause