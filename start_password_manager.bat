@echo off
chcp 65001 > nul
cd /d %~dp0

REM Pythonコマンドの存在確認
where python > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo エラー: Pythonが見つかりません
    echo Microsoft StoreからPython 3.12をインストールしてください
    pause
    exit /b 1
)

REM Pythonのバージョン確認
python --version | findstr "3.1" > nul
if %ERRORLEVEL% neq 0 (
    echo エラー: Python 3.10以上が必要です
    echo 現在のバージョン:
    python --version
    pause
    exit /b 1
)

REM 仮想環境が存在しない場合のみ作成
if not exist venv (
    echo 仮想環境をセットアップしています...
    python -m venv venv
    if %ERRORLEVEL% neq 0 (
        echo エラー: 仮想環境の作成に失敗しました
        pause
        exit /b 1
    )
    
    REM 仮想環境をアクティベート
    call venv\Scripts\activate.bat
    if %ERRORLEVEL% neq 0 (
        echo エラー: 仮想環境のアクティベートに失敗しました
        pause
        exit /b 1
    )
    
    echo パッケージをインストールしています...
    python -m pip install --upgrade pip
    pip install -r requirements.txt
) else (
    REM 既存の仮想環境をアクティベート
    call venv\Scripts\activate.bat
    if %ERRORLEVEL% neq 0 (
        echo エラー: 仮想環境のアクティベートに失敗しました
        pause
        exit /b 1
    )
)

REM PYTHONPATHを設定
set PYTHONPATH=%~dp0

echo パスワードマネージャーを起動しています...
python -m src.main
pause