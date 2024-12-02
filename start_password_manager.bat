@echo off
chcp 65001 > nul
cd /d %~dp0

if not exist venv (
    echo 仮想環境をセットアップしています...
    python -m venv venv
    call venv\Scripts\activate
    python -m pip install --upgrade pip
    pip install -r requirements.txt --no-warn-script-location
) else (
    call venv\Scripts\activate
    python -m pip install --upgrade pip
)

echo パスワードマネージャーを起動しています...
python src/main.py
pause 