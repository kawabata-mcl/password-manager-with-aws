# AWS Parameter Store パスワードマネージャー

AWS Parameter Storeを使用したWindowsで動作するパスワードマネージャーです。
パスワード情報をAWS上で安全に管理し、デスクトップアプリケーションから簡単にアクセスできます。

## 機能

- パスワード情報の安全な管理（AWS Parameter Store使用）
- パスワード情報の登録・編集・削除
- クリップボードへのコピー機能
- パスワードのマスク表示
- 自動ログアウト機能
- AWS認証情報の暗号化保存

## 必要要件

- Python 3.10以上
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
└── start_password_manager.bat  # Windows用起動スクリプト
```

## セットアップ手順

### 1. リポジトリのクローン

```bash
git clone https://github.com/kawabata-mcl/password-manager-with-aws.git
cd password-manager-with-aws
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
   ```powershell
   aws cloudformation create-stack `
     --stack-name password-manager-iam `
     --template-body file://infrastructure/password-manager-iam.yaml `
     --capabilities CAPABILITY_NAMED_IAM `
     --profile password-manager-admin
   ```

2. スタックの作成完了を待機
   ```powershell
   aws cloudformation wait stack-create-complete `
     --stack-name password-manager-iam `
     --profile password-manager-admin
   ```

3. アプリケーション用の認証情報の取得
   ```powershell
   # シークレットのARNを取得
   $SECRET_ARN = aws cloudformation describe-stacks `
     --stack-name password-manager-iam `
     --query 'Stacks[0].Outputs[?OutputKey==`SecretArn`].OutputValue' `
     --output text `
     --profile password-manager-admin

   # 認証情報の取得
   aws secretsmanager get-secret-value `
     --secret-id $SECRET_ARN `
     --query 'SecretString' `
     --output text `
     --profile password-manager-admin
   ```

4. 取得した認証情報を安全に保管
   - 表示された認証情報（JSON形式）をコピー
   - 次のステップのアプリケーション初回起動時に使用
   - 認証情報を取得したら、ターミナルの履歴をクリア
     ```cmd
     cls         # Windows
     ```

### 4. アプリケーションの初回起動

1. `start_password_manager.bat`をダブルクリック
2. 必要なパッケージが自動的にインストールされます

### 5. アカウント作成とログイン

#### 新規アカウント作成
1. アプリケーションを起動し、「新規登録」ボタンをクリック
2. 以下の情報を入力：
   - ユーザー名（英数字、アンダースコア、ハイフンのみ使用可）
   - パスワード（確認用に2回入力）
   - AWSアクセスキー（手順3で取得したJSONの`accessKeyId`の値）
   - AWSシークレットキー（手順3で取得したJSONの`secretAccessKey`の値）
3. 「登録」ボタンをクリックして完了
4. 登録完了のメッセージが表示されます

#### ログイン
1. ユーザー名とパスワードを入力
2. 「ログイン」ボタンをクリック
3. 認証に失敗した場合：
   - 登録されていないユーザー：新規登録を行ってください
   - パスワードが間違っている：正しいパスワードを入力してください
   - 3回連続で失敗するとアプリケーションが終了します

### 6. パスワード情報の管理

#### パスワード情報の追加
1. メイン画面の「追加」ボタンをクリック
2. 以下の情報を入力：
   - アプリ名（必須）
   - URL
   - ユーザー名（必須）
   - パスワード（必須）
   - メモ
3. 「保存」ボタンをクリック

#### パスワード情報の編集
1. 編集したい項目のチェックボックスを選択
2. 「編集」ボタンをクリック
3. 情報を修正
4. 「保存」ボタンをクリック

#### パスワード情報の削除
1. 削除したい項目のチェックボックスを選択（複数選択可）
2. 「削除」ボタンをクリック
3. 確認ダイアログで「はい」をクリック

#### パスワード情報のコピー
1. コピーしたい項目のチェックボックスを選択
2. 以下のいずれかのボタンをクリック：
   - 「URLをコピー」
   - 「ユーザー名をコピー」
   - 「パスワードをコピー」

#### パスワードの表示/非表示
- パスワード列をダブルクリックすると、マスク表示と実際のパスワードが切り替わります

#### 一覧の更新
- 「更新」ボタンをクリックすると、最新のパスワード情報を取得します

### 7. セキュリティ機能

- パスワード情報はAWS Parameter Storeで暗号化して保存
- AWS認証情報は暗号化して保存
- パスワードはマスク表示がデフォルト
- 自動ログアウト機能（30分間操作がない場合）
- ログイン試行回数の制限（3回まで）

### 8. トラブルシューティング

#### ログインできない場合
- ユーザー名とパスワードが正しいか確認
- 新規ユーザーの場合は新規登録を実行
- ログイン試行回数が上限に達した場合は、アプリケーションを再起動

#### パスワード情報が表示されない場合
- 「更新」ボタンをクリック
- AWS認証情報が正しいか確認
- インターネット接続を確認

## アプリケーションの設定

アプリケーションの設定は2つの場所で管理されています：

### 1. テンプレート設定ファイル
- 場所: `src/config/config.template.ini`
- 用途: デフォルト設定のテンプレート
- Git管理: リポジトリに含まれる

### 2. 実際の設定ファイル
- 場所: ユーザーホームディレクトリ下の `.password_manager/config.ini`
  - Windows: `C:\Users\ユーザー名\.password_manager\config.ini`
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
- セキュリティ上の理由から、実際の設定ファイル（`.password_manager/config.ini`）は手動で編集する必要があります
- 設定ファイルが存在しない場合は、初回起動時にテンプレートの内容を基にデフォルト値で作成されます
- AWS認証情報は別途暗号化して保存されるため、この設定ファイルには含まれません

## アプリケーションの削除

アプリケーションを完全に削除する場合は、以下の手順に従ってください：

### 1. AWSリソースの削除

> **Note**: コマンド例では `password-manager-admin` というプロファイル名を使用しています。
> 異なるプロファイル名を使用している場合は、`--profile password-manager-admin` の部分を
> 実際に使用しているプロファイル名に置き換えてください。

1. AWS CLIで認証情報を設定していない場合：
   ```bash
   aws configure --profile password-manager-admin
   ```

2. CloudFormationスタックの削除：
   ```powershell
   aws cloudformation delete-stack `
     --stack-name password-manager-iam `
     --profile password-manager-admin  # プロファイル名は適宜変更
   ```

3. 削除完了の確認：
   ```powershell
   aws cloudformation wait stack-delete-complete `
     --stack-name password-manager-iam `
     --profile password-manager-admin  # プロファイル名は適宜変更
   ```

## 注意事項

- AWS認証情報は適切に管理してください
- 定期的なパスワード変更を推奨します
- 重要なパスワード情報は別の方法でもバックアップすることを推奨します

## コスト

- AWS Parameter Storeの標準パラメータを使用（低コスト）
- ローカルキャッシュによりAPI呼び出しを最小限に抑制
- 概算コスト：月額1ドル未満（通常使用の場合）
