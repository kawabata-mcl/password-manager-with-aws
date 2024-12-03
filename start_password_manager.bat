@echo off
chcp 65001 > nul
setlocal

:: Pythonの仮想環境のパス
set VENV_PATH=_venv
:: インストール完了フラグファイル
set "INSTALL_FLAG=%~dp0%VENV_PATH%\install_complete.flag"

:: カレントディレクトリをバッチファイルの場所に設定
cd /d %~dp0

:: インストール完了フラグが存在しない場合（初回実行時）
if not exist "%INSTALL_FLAG%" (
    :: 通常のコマンドプロンプト表示で実行
    call :FIRST_TIME_SETUP
    :: インストール完了フラグを作成
    type nul > "%INSTALL_FLAG%"
) else (
    :: 通常のウィンドウで実行
    call %VENV_PATH%\Scripts\activate.bat >nul 2>&1
    cmd /c "python -m src.main 2>"%TEMP%\password_manager_error.log%" && exit || (type "%TEMP%\password_manager_error.log%" && pause && del "%TEMP%\password_manager_error.log%")"
)

goto :EOF

:FIRST_TIME_SETUP
echo 初回セットアップを実行しています...
:: 仮想環境が存在しない場合は作成
if not exist %VENV_PATH% (
    echo 仮想環境を作成しています...
    python -m venv %VENV_PATH%
)

:: 仮想環境をアクティベート
call %VENV_PATH%\Scripts\activate.bat

:: 必要なパッケージがインストールされているか確認
pip freeze | findstr /C:"PyQt6" > nul
if errorlevel 1 (
    echo 必要なパッケージをインストールしています...
    pip install -r requirements.txt
)

:: 初回起動
python -m src.main
exit /b

endlocal