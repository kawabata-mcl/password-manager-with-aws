#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AWSパラメータストア操作用マネージャー

このモジュールは、AWSパラメータストアとの通信を管理し、
パスワード情報のCRUD操作を提供します。

主な機能:
- パスワード情報の暗号化保存
- パスワード情報の取得と復号
- キャッシュを使用したパフォーマンス最適化
- エラーハンドリングとリトライ処理

依存関係:
- boto3: AWS SDK for Python
- json: JSONデータの処理
- typing: 型ヒント
- datetime: 日時処理
"""

import boto3
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from .credentials_manager import CredentialsManager

class AWSManager:
    class NoCredentialsError(Exception):
        """認証情報が設定されていない場合のエラー"""
        pass

    def __init__(self, region: str = 'ap-northeast-1'):
        """
        AWSマネージャーの初期化

        Args:
            region (str): AWS リージョン名。デフォルトは 'ap-northeast-1'

        Attributes:
            region (str): 使用するAWSリージョン
            credentials_manager (CredentialsManager): 認証情報管理オブジェクト
            session (boto3.Session): AWSセッション
            ssm (boto3.client): Systems Manager クライアント
            cache (dict): パスワード情報のキャッシュ
            cache_timestamp (datetime): キャッシュの最終更新時刻
            cache_duration (int): キャッシュの有効期間（秒）
        """
        self.region = region
        self.credentials_manager = CredentialsManager()
        self._setup_session()
        self.cache = {}
        self.cache_timestamp = None
        self.cache_duration = 300  # 5分

    def _setup_session(self):
        """
        AWSセッションのセットアップ

        認証情報を使用してAWSセッションとSystems Managerクライアントを初期化します。
        認証情報が存在しない場合、セッションとクライアントはNoneに設定されます。
        """
        access_key = self.credentials_manager.get_access_key()
        secret_key = self.credentials_manager.get_secret_key()
        
        if not access_key or not secret_key:
            self.session = None
            self.ssm = None
            return

        self.session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=self.region
        )
        self.ssm = self.session.client('ssm')

    def _check_credentials(self):
        """
        認証情報が設定されているか確認

        Raises:
            NoCredentialsError: 認証情報が設定されていない場合に発生

        Note:
            このメソッドは他のメソッドから認証情報の存在を確認するために使用されます。
        """
        if self.ssm is None:
            raise self.NoCredentialsError("AWS認証情報が設定されていません。設定画面から認証情報を設定してください。")

    def _get_parameter_path(self, username: str, app_name: str = None) -> str:
        """
        パラメータパスの生成

        Args:
            username (str): ユーザー名
            app_name (str, optional): アプリ名。指定がない場合はユーザーのルートパスを返す。

        Returns:
            str: パラメータパス（例: /password-manager/username/app_name）

        Note:
            パスの形式は /password-manager/{username}/{app_name} です。
            app_nameが指定されていない場合は /password-manager/{username} を返します。
        """
        base_path = f"/password-manager/{username}"
        if app_name:
            return f"{base_path}/{app_name}"
        return base_path

    def _is_cache_valid(self) -> bool:
        """
        キャッシュが有効かどうかを確認

        Returns:
            bool: キャッシュが有効な場合はTrue、それ以外はFalse

        Note:
            キャッシュの有効期間は self.cache_duration で指定された秒数です。
        """
        if not self.cache_timestamp:
            return False
        return datetime.now() - self.cache_timestamp < timedelta(seconds=self.cache_duration)

    def get_passwords(self, username: str) -> list:
        """
        指定されたユーザーのパスワード一覧を取得

        Args:
            username (str): ユーザー名

        Returns:
            list: パスワード情報のリスト。各要素は以下の形式の辞書:
                {
                    'app_name': str,
                    'url': str,
                    'username': str,
                    'password': str,
                    'memo': str
                }

        Note:
            - キャッシュが有効な場合はキャッシュから情報を返します
            - エラーが発生した場合は空のリストを返します
            - 取得したデータは自動的にキャッシュされます
        """
        try:
            self._check_credentials()
            
            # キャッシュチェック
            if self.cache_timestamp and (datetime.now() - self.cache_timestamp).total_seconds() < self.cache_duration:
                if username in self.cache:
                    return self._migrate_password_data(self.cache[username])

            # ユーザーのルートパスを取得
            root_path = self._get_parameter_path(username)
            print(f"パラメータ取得開始: {root_path}")  # デバッグ情報
            passwords = []

            try:
                # パラメータの一覧を取得
                response = self.ssm.get_parameters_by_path(
                    Path=root_path,
                    Recursive=True,
                    WithDecryption=True
                )
                
                print(f"取得されたパラメータ数: {len(response.get('Parameters', []))}")  # デバッグ情報
                
                # 各パラメータからパスワード情報を取得
                for param in response.get('Parameters', []):
                    param_name = param['Name']
                    print(f"処理中のパラメータ: {param_name}")  # デバッグ情報
                    
                    app_name = param_name.split('/')[-1]  # パスの最後の部分をアプリ名として使用
                    try:
                        password_data = json.loads(param['Value'])
                        password_data['app_name'] = app_name
                        passwords.append(password_data)
                        print(f"パスワード情報を追加: {app_name}")  # デバッグ情報
                    except json.JSONDecodeError as e:
                        print(f"JSONデコードエラー ({param_name}): {e}")  # デバッグ情報
                        continue
                
                print(f"処理完了したパスワード数: {len(passwords)}")  # デバッグ情報
                
                # データ形式の移行
                passwords = self._migrate_password_data(passwords)
                
                # キャッシュ更新
                self.cache[username] = passwords
                self.cache_timestamp = datetime.now()
                
                return passwords
            except self.ssm.exceptions.ParameterNotFound:
                print(f"パラメータが見つかりません: {root_path}")  # デバッグ情報
                return []
            
        except self.NoCredentialsError as e:
            print(f"認証エラー: {e}")
            return []
        except Exception as e:
            print(f"パスワード取得エラー: {e}")
            import traceback
            print(f"詳細なエラー情報: {traceback.format_exc()}")  # デバッグ情報
            return []

    def _migrate_password_data(self, passwords: list) -> list:
        """
        古い形式のパスワードデータを新しい形式に移行

        Args:
            passwords (list): パスワード情報のリスト

        Returns:
            list: 移行後のパスワード情報のリスト

        Note:
            - 古い形式（'website'キー）から新しい形式（'app_name'キー）への変換を行います
            - 必須フィールドが存在しない場合は空文字列を設定します
        """
        migrated_passwords = []
        for password in passwords:
            migrated_password = password.copy()
            
            # 古い形式から新しい形式への変換
            if 'website' in password and 'app_name' not in password:
                migrated_password['app_name'] = password['website']
                migrated_password['url'] = password.get('url', '')
                del migrated_password['website']
            
            # 必須フィールドの確認と設定
            if 'app_name' not in migrated_password:
                migrated_password['app_name'] = ''
            if 'url' not in migrated_password:
                migrated_password['url'] = ''
            if 'username' not in migrated_password:
                migrated_password['username'] = ''
            if 'password' not in migrated_password:
                migrated_password['password'] = ''
            if 'memo' not in migrated_password:
                migrated_password['memo'] = ''
            
            migrated_passwords.append(migrated_password)
        
        return migrated_passwords

    def save_password(self, username: str, password_data: dict) -> bool:
        """
        パスワード情報を保存

        Args:
            username (str): ユーザー名
            password_data (dict): パスワード情報
                {
                    'app_name': str,
                    'url': str,
                    'username': str,
                    'password': str,
                    'memo': str
                }

        Returns:
            bool: 保存に成功した場合はTrue、失敗した場合はFalse

        Note:
            - パスワード情報はAWSパラメータストアに暗号化して保存されます
            - 保存後、キャッシュは自動的に更新されます
            - app_nameは必須フィールドです
        """
        try:
            self._check_credentials()
            
            # データの検証
            if 'app_name' not in password_data:
                raise ValueError("必須フィールド 'app_name' が見つかりません")
            
            # 必須フィールドの確認と設定
            password_data.setdefault('url', '')
            password_data.setdefault('username', '')
            password_data.setdefault('password', '')
            password_data.setdefault('memo', '')
            
            # app_nameをパラメータパスに使用するため、コピーから削除
            app_name = password_data['app_name']
            param_data = password_data.copy()
            del param_data['app_name']
            
            # パラメータストアに保存
            parameter_path = self._get_parameter_path(username, app_name)
            self.ssm.put_parameter(
                Name=parameter_path,
                Value=json.dumps(param_data),
                Type='SecureString',
                Overwrite=True
            )
            
            # キャッシュを更新
            passwords = self.get_passwords(username)  # 最新のパスワード一覧を取得
            self.cache[username] = passwords
            self.cache_timestamp = datetime.now()
            
            return True
            
        except Exception as e:
            print(f"パスワード保存エラー: {e}")
            return False

    def delete_password(self, username: str, app_name: str) -> bool:
        """
        パスワード情報を削除

        Args:
            username (str): ユーザー名
            app_name (str): 削除するアプリ名

        Returns:
            bool: 削除に成功した場合はTrue、失敗した場合はFalse

        Note:
            - 削除後、キャッシュは自動的に更新されます
            - 指定されたapp_nameが存在しない場合もTrueを返します
        """
        try:
            self._check_credentials()
            
            # パラメータの削除
            parameter_path = self._get_parameter_path(username, app_name)
            self.ssm.delete_parameter(Name=parameter_path)
            
            # キャッシュを更新
            passwords = self.get_passwords(username)  # 最新のパスワード一覧を取得
            self.cache[username] = passwords
            self.cache_timestamp = datetime.now()
            
            return True
            
        except self.ssm.exceptions.ParameterNotFound:
            # パラメータが存在しない場合は成功として扱う
            return True
        except Exception as e:
            print(f"パスワード削除エラー: {e}")
            return False

    def update_credentials(self, access_key: str, secret_key: str):
        """
        AWS認証情報の更新

        Args:
            access_key (str): AWSアクセスキー
            secret_key (str): AWSシークレットキー
        """
        credentials = {
            'access_key': access_key,
            'secret_key': secret_key
        }
        self.credentials_manager.save_credentials(credentials)
        self._setup_session()
  