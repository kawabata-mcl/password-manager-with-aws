#!/bin/bash

# エラー時に実行を停止
set -e

# スクリプトのディレクトリに移動
cd "$(dirname "$0")"

# Pythonが利用可能か確認
if ! command -v python3 &> /dev/null; then
    echo "エラー: Python3がインストールされていません"
    exit 1
fi

# 必要なPythonバージョンを確認
REQUIRED_PYTHON_VERSION="3.10"
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if [ "$(echo -e "$PYTHON_VERSION\n$REQUIRED_PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_PYTHON_VERSION" ]; then
    echo "エラー: Python $REQUIRED_PYTHON_VERSION 以上が必要です（現在のバージョン: $PYTHON_VERSION）"
    exit 1
fi

# 仮想環境が存在しない場合は作成
if [ ! -d "venv" ]; then
    echo "仮想環境をセットアップしています..."
    python3 -m venv venv || { echo "仮想環境の作成に失敗しました"; exit 1; }
fi

# 仮想環境をアクティベート
source venv/bin/activate || { echo "仮想環境のアクティベートに失敗しました"; exit 1; }

# pipのアップグレードと依存関係のインストール
echo "パッケージをインストールしています..."
python3 -m pip install --upgrade pip
pip install -r requirements.txt --no-warn-script-location

echo "パスワードマネージャーを起動しています..."
python3 src/main.py 