# AWS Parameter Store パスワードマネージャー

AWS Parameter Storeを使用したクロスプラットフォーム対応のパスワードマネージャーです。
パスワード情報をAWS上で安全に管理し、デスクトップアプリケーションから簡単にアクセスできます。

## 機能

- パスワード情報の安全な管理（AWS Parameter Store使用）
- クロスプラットフォーム対応（Windows/macOS）
- パスワード情報の登録・編集・削除
- クリップボードへのコピー機能
- パスワードのマスク表示
- 自動ログアウト機能
- AWS認証情報の暗号化保存

## 必要要件

- Python 3.8以上
- AWS アカウント
- AWS CLI（インフラストラクチャのセットアップ用）
- Git（ソースコードのクローン用）

## プロジェクト構造

```
password-manager/
├── src/                 # アプリケーションのソースコード
│   ├── config/         # 設定ファイル
│   ├── ui/            # GUI関連のコード
│   ├── utils/         # ユーティリティ関数
│   └── main.py        # アプリケーションのエントリーポイント
├── infrastructure/      # インフラストラクチャ設定
│   └── password-manager-iam.yaml  # IAMユーザー作成用CloudFormation
├── docs/               # ドキュメント
├── requirements.txt    # Pythonの依存パッケージ
├── start_password_manager.bat  # Windows用起動スクリプト
└── start_password_manager.sh   # macOS用起動スクリプト
```

## セットアップ手順

### 1. リポジトリのクローン

```bash
git clone https://github.com/yourusername/password-manager.git
cd password-manager
```

### 2. AWS CLIのセットアップ

> **Note**: すでにAWS CLIがインストールされており、管理者権限を持つプロファイルが設定済みの場合は、このステップをスキップできます。

1. [AWS CLIのインストール](https://aws.amazon.com/cli/)

2. 管理者権限を持つIAMユーザーの認証情報でプロファイルを設定
   ```bash
   # password-manager-adminという名前でプロファイルを作成
   aws configure --profile password-manager-admin
   ```
   
   以下の情報を入力：
   - AWS Access Key ID: 管理者権限を持つIAMユーザーのアクセスキー
   - AWS Secret Access Key: 管理者権限を持つIAMユーザーのシークレットキー
   - Default region name: アプリケーションを使用するリージョン（例：ap-northeast-1）
   - Default output format: json（推奨）

### 3. パスワードマネージャー用IAMユーザーの作成

1. CloudFormationテンプレートのデプロイ
   ```bash
   aws cloudformation create-stack \
     --stack-name password-manager-iam \
     --template-body file://infrastructure/password-manager-iam.yaml \
     --capabilities CAPABILITY_NAMED_IAM \
     --profile password-manager-admin
   ```

2. スタックの作成完了を待機
   ```bash
   aws cloudformation wait stack-create-complete \
     --stack-name password-manager-iam \
     --profile password-manager-admin
   ```

3. アプリケーション用の認証情報の取得
   ```bash
   # パラメータ名の取得
   PARAM_NAME=$(aws cloudformation describe-stacks \
     --stack-name password-manager-iam \
     --query 'Stacks[0].Outputs[?OutputKey==`ParameterName`].OutputValue' \
     --output text \
     --profile password-manager-admin)

   # 認証情報の取得（暗号化された状態で取得）
   aws ssm get-parameter \
     --name $PARAM_NAME \
     --with-decryption \
     --query 'Parameter.Value' \
     --output text \
     --profile password-manager-admin
   ```

4. 取得した認証情報を安全に保管
   - 表示された認証情報（JSON形式）をコピー
   - 次のステップのアプリケーション初回起動時に使用
   - 認証情報を取得したら、ターミナルの履歴をクリア
     ```bash
     history -c  # macOS/Linux
     cls         # Windows
     ```

### 4. アプリケーションの初回起動

#### Windows
1. `start_password_manager.bat`をダブルクリック
2. 必要なパッケージが自動的にインストールされます
3. AWS認証情報の入力を求められます
   - アクセスキーID: 手順3で取得したJSONの`accessKeyId`の値
   - シークレットアクセスキー: 手順3で取得したJSONの`secretAccessKey`の値
   - リージョン: 手順2で設定したリージョン（デフォルト: ap-northeast-1）

#### macOS
1. ターミナルで以下のコマンドを実行
   ```bash
   chmod +x start_password_manager.sh
   ./start_password_manager.sh
   ```
2. 必要なパッケージが自動的にインストールされます
3. AWS認証情報の入力を求められます
   - アクセスキーID: 手順3で取得したJSONの`accessKeyId`の値
   - シークレットアクセスキー: 手順3で取得したJSONの`secretAccessKey`の値
   - リージョン: 手順2で設定したリージョン（デフォルト: ap-northeast-1）

### 5. 通常の起動方法

#### Windows
- `start_password_manager.bat`をダブルクリック
- または、作成済みのショートカットをダブルクリック（ショートカット作成済みの場合）

#### macOS
- ターミナルで`./start_password_manager.sh`を実行
- または、作成済みのエイリアスをダブルクリック（エイリアス作成済みの場合）

### 6. ショートカットの作成（任意）

#### Windows
1. `start_password_manager.bat`を右クリック
2. 「ショートカットの作成」を選択
3. ショートカットをデスクトップに移動

#### macOS
1. Finderで`start_password_manager.sh`を選択
2. Command + Option キーを押しながらデスクトップにドラッグ

## アプリケーションの設定

アプリケーションの設定は2つの場所で管理されています：

### 1. テンプレート設定ファイル
- 場所: `src/config/config.template.ini`
- 用途: デフォルト設定のテンプレート
- Git管理: リポジトリに含まれる

### 2. 実際の設定ファイル
- 場所: ユーザーホームディレクトリ下の `.password_manager/config.ini`
  - Windows: `C:\Users\ユーザー名\.password_manager\config.ini`
  - macOS: `/Users/ユーザー名/.password_manager/config.ini`
- 用途: 実際のアプリケーション設定
- 作成タイミング: アプリケーション初回起動時に自動生成

### 設定可能な項目

```ini
[AWS]
region = ap-northeast-1  # AWSリージョン

[App]
# セッションタイムアウト時間（分）
# ユーザーの操作がない場合、指定時間後に自動ログアウト
# デフォルト: 30分
session_timeout = 30

# ログイン試行回数の制限
# この回数を超えるとアプリケーションが終了
# デフォルト: 3回
max_login_attempts = 3

# パスワード情報のキャッシュ時間（秒）
# AWS Parameter Storeへのアクセスを最小限に抑えるためのキャッシュ時間
# デフォルト: 300秒（5分）
password_cache_duration = 300
```

### 設定の反映

- 設定の変更は、アプリケーションの再起動後に反映されます
- セキュリティ上の理由から、実際の設定ファイル（`~/.password_manager/config.ini`）は手動で編集する必要があります
- 設定ファイルが存在しない場合は、初回起動時にテンプレートの内容を基にデフォルト値で作成されます
- AWS認証情報は別途暗号化して保存されるため、この設定ファイルには含まれません

## アプリケーションの削除

アプリケーションを完全に削除する場合は、以下の手順に従ってください：

### 1. AWSリソースの削除

1. AWS CLIで認証情報を設定していない場合：
   ```bash
   aws configure --profile password-manager-admin
   ```

2. CloudFormationスタックの削除：
   ```bash
   aws cloudformation delete-stack \
     --stack-name password-manager-iam \
     --profile password-manager-admin
   ```

3. 削除完了の確認：
   ```bash
   aws cloudformation wait stack-delete-complete \
     --stack-name password-manager-iam \
     --profile password-manager-admin
   ```

### 2. ローカルファイルの削除

#### Windows
1. アプリケーションフォルダの削除：
   ```cmd
   rmdir /s /q password-manager
   ```

2. 設定ファイルの削除：
   ```cmd
   rmdir /s /q "%USERPROFILE%\.password_manager"
   ```

#### macOS
1. アプリケーションフォルダの削除：
   ```bash
   rm -rf password-manager
   ```

2. 設定ファイルの削除：
   ```bash
   rm -rf ~/.password_manager
   ```

3. 作成したエイリアスの削除（作成している場合）：
   - デスクトップ上のエイリアスを削除

### 3. AWS CLIプロファイルの削除（任意）

管理用のプロファイルが不要な場合：

#### Windows
```cmd
del "%USERPROFILE%\.aws\credentials.password-manager-admin"
```

#### macOS
```bash
rm ~/.aws/credentials.password-manager-admin
```

## 注意事項

- AWS認証情報は適切に管理してください
- 定期的なパスワード変更を推奨します
- 重要なパスワード情報は別の方法でもバックアップすることを推奨します

## コスト

- AWS Parameter Storeの標準パラメータを使用（低コスト）
- ローカルキャッシュによりAPI呼び出しを最小限に抑制
- 概算コスト：月額1ドル未満（通常使用の場合）
