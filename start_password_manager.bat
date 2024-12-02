@echo off
cd /d %~dp0
if not exist venv (
    echo 仮想環境をセットアップしています...
    python -m venv venv
    call venv\Scripts\activate
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate
)

echo パスワードマネージャーを起動しています...
python src/main.py
pause 