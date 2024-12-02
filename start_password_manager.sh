#!/bin/bash

# スクリプトのディレクトリに移動
cd "$(dirname "$0")"

# 仮想環境が存在しない場合は作成
if [ ! -d "venv" ]; then
    echo "仮想環境をセットアップしています..."
    python3 -m venv venv
    source venv/bin/activate
    python3 -m pip install --upgrade pip
    pip install -r requirements.txt --no-warn-script-location
else
    source venv/bin/activate
    python3 -m pip install --upgrade pip
fi

echo "パスワードマネージャーを起動しています..."
python3 src/main.py 