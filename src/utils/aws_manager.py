#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AWSパラメータストア操作用マネージャー

このモジュールは、AWSパラメータストアとの通信を管理し、
パスワード情報のCRUD操作を提供します。
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
        """
        self.region = region
        self.credentials_manager = CredentialsManager()
        self._setup_session()
        self.cache = {}
        self.cache_timestamp = None
        self.cache_duration = 300  # 5分

    def _setup_session(self):
        """AWSセッションのセットアップ"""
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
            NoCredentialsError: 認証情報が設定されていない場合
        """
        if self.ssm is None:
            raise self.NoCredentialsError("AWS認証情報が設定されていません。設定画面から認証情報を設定してください。")

    def _get_parameter_path(self, username: str) -> str:
        """パラメータパスの生成"""
        return f"/password-manager/{username}"

    def _is_cache_valid(self) -> bool:
        """キャッシュが有効かどうかを確認"""
        if not self.cache_timestamp:
            return False
        return datetime.now() - self.cache_timestamp < timedelta(seconds=self.cache_duration)

    def get_passwords(self, username: str) -> list:
        """
        指定されたユーザーのパスワード一覧を取得

        Args:
            username (str): ユーザー名

        Returns:
            list: パスワード情報のリスト
        """
        try:
            self._check_credentials()
            
            # キャッシュチェック
            if self.cache_timestamp and (datetime.now() - self.cache_timestamp).total_seconds() < self.cache_duration:
                if username in self.cache:
                    return self._migrate_password_data(self.cache[username])

            parameter_path = self._get_parameter_path(username)
            try:
                response = self.ssm.get_parameter(
                    Name=parameter_path,
                    WithDecryption=True
                )
                passwords = json.loads(response['Parameter']['Value'])
                
                # データ形式の移行
                passwords = self._migrate_password_data(passwords)
                
                # キャッシュ更新
                self.cache[username] = passwords
                self.cache_timestamp = datetime.now()
                
                return passwords
            except self.ssm.exceptions.ParameterNotFound:
                return []
            
        except self.NoCredentialsError as e:
            print(f"認証エラー: {e}")
            return []
        except Exception as e:
            print(f"パスワード取得エラー: {e}")
            return []

    def _migrate_password_data(self, passwords: list) -> list:
        """
        古い形式のパスワードデータを新しい形式に移行

        Args:
            passwords (list): パスワード情報のリスト

        Returns:
            list: 移行後のパスワード情報のリスト
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
            bool: 保存に成功した場合はTrue
        """
        try:
            self._check_credentials()
            
            # 既存のパスワード一覧を取得
            passwords = self.get_passwords(username)
            
            # データの検証
            if 'app_name' not in password_data:
                raise ValueError("必須フィールド 'app_name' が見つかりません")
            
            # 必須フィールドの確認と設定
            password_data.setdefault('url', '')
            password_data.setdefault('username', '')
            password_data.setdefault('password', '')
            password_data.setdefault('memo', '')
            
            # 既存のパスワードを更新または新規追加
            updated = False
            for item in passwords:
                if item['app_name'] == password_data['app_name']:
                    item.update(password_data)
                    updated = True
                    break
            
            if not updated:
                passwords.append(password_data)
            
            # パラメータストアに保存
            self.ssm.put_parameter(
                Name=self._get_parameter_path(username),
                Value=json.dumps(passwords),
                Type='SecureString',
                Overwrite=True
            )
            
            # キャッシュを更新
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
            app_name (str): アプリ名

        Returns:
            bool: 削除に成功した場合はTrue
        """
        try:
            self._check_credentials()
            
            # 既存のパスワード一覧を取得
            passwords = self.get_passwords(username)
            
            # 指定されたアプリ名のパスワードを削除
            passwords = [p for p in passwords if p['app_name'] != app_name]
            
            # パラメータストアに保存
            self.ssm.put_parameter(
                Name=self._get_parameter_path(username),
                Value=json.dumps(passwords),
                Type='SecureString',
                Overwrite=True
            )
            
            # キャッシュを更新
            self.cache[username] = passwords
            self.cache_timestamp = datetime.now()
            
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
        self.credentials_manager.save_credentials(access_key, secret_key)
        self._setup_session()
  