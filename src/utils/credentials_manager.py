#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AWS認証情報マネージャー

AWSの認証情報を安全に管理するためのユーティリティクラス。
認証情報は暗号化されて保存されます。

主な機能:
- AWS認証情報の暗号化保存
- 認証情報の安全な読み込み
- 設定ファイルの管理

依存関係:
- cryptography: 暗号化処理
- configparser: 設定ファイル処理
- base64: エンコーディング
"""

import os
import json
import configparser
from pathlib import Path
from base64 import b64encode, b64decode
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class CredentialsManager:
    def __init__(self):
        """
        認証情報マネージャーの初期化

        Attributes:
            config_dir (Path): 設定ファイルディレクトリ
            config_path (Path): 設定ファイルのパス
            credentials_path (Path): 認証情報ファイルのパス
            cipher_suite (Fernet): 暗号化/復号化オブジェクト
        """
        self.config_dir = Path.home() / '.password_manager'
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_path = self.config_dir / 'config.ini'
        self.credentials_path = self.config_dir / 'credentials.enc'
        self._setup_encryption()

    def _setup_encryption(self):
        """
        暗号化キーのセットアップ

        暗号化に使用するマスターキーの生成または読み込みを行います。
        キーはPBKDF2を使用して生成され、ファイルに保存されます。

        Note:
            - キーファイルが存在しない場合は新規に生成されます
            - 既存のキーファイルが存在する場合はそれを読み込みます
            - キーはソルトとともに保存されます
        """
        key_file = self.config_dir / 'master.key'
        if not key_file.exists():
            # マスターキーの生成
            salt = os.urandom(16)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = b64encode(kdf.derive(os.urandom(32)))
            with open(key_file, 'wb') as f:
                f.write(salt + b'\n' + key)
        
        # 既存のキーの読み込み
        with open(key_file, 'rb') as f:
            salt = f.readline().strip()
            key = f.readline().strip()
        
        self.cipher_suite = Fernet(key)

    def save_credentials(self, credentials: dict):
        """
        AWS認証情報を暗号化して保存

        Args:
            credentials (dict): AWS認証情報を含む辞書
                {
                    'access_key': str,
                    'secret_key': str,
                    'region': str (optional)
                }

        Note:
            - 認証情報は暗号化されてファイルに保存されます
            - リージョン情報は設定ファイルに平文で保存されます
            - 既存の認証情報は上書きされます
        """
        # 認証情報の暗号化
        encrypted_data = self.cipher_suite.encrypt(json.dumps(credentials).encode())
        
        # 暗号化されたデータの保存
        with open(self.credentials_path, 'wb') as f:
            f.write(encrypted_data)

    def load_credentials(self) -> dict:
        """
        暗号化された認証情報を読み込む

        Returns:
            dict: 認証情報を含む辞書
                {
                    'access_key': str,
                    'secret_key': str,
                    'region': str
                }

        Note:
            - 認証情報が存在しない場合は空の辞書を返します
            - 復号化に失敗した場合は空の辞書を返します
            - リージョン情報は設定ファイルから読み込まれます
        """
        if not self.credentials_path.exists():
            return {'access_key': '', 'secret_key': ''}
        
        try:
            with open(self.credentials_path, 'rb') as f:
                encrypted_data = f.read()
                decrypted_data = self.cipher_suite.decrypt(encrypted_data)
                return json.loads(decrypted_data.decode())
        except Exception as e:
            print(f"認証情報の読み込みエラー: {e}")
            return {'access_key': '', 'secret_key': ''}

    def get_access_key(self) -> str:
        """
        AWSアクセスキーを取得

        Returns:
            str: AWSアクセスキー。認証情報が存在しない場合は空文字列

        Note:
            このメソッドは内部でload_credentials()を呼び出します。
        """
        return self.load_credentials().get('access_key', '')

    def get_secret_key(self) -> str:
        """
        AWSシークレットキーを取得

        Returns:
            str: AWSシークレットキー。認証情報が存在しない場合は空文字列

        Note:
            このメソッドは内部でload_credentials()を呼び出します。
        """
        return self.load_credentials().get('secret_key', '')

    def save_credentials(self, credentials: dict):
        """
        AWS認証情報を暗号化して保存
        
        Args:
            credentials (dict): AWS認証情報を含む辞書
        """
        # 認証情報の暗号化
        encrypted_data = self.cipher_suite.encrypt(json.dumps(credentials).encode())
        
        # 暗号化されたデータの保存
        with open(self.credentials_path, 'wb') as f:
            f.write(encrypted_data)
        
        # 設定ファイルの更新（リージョンのみ平文で保存）
        config = configparser.ConfigParser()
        config['AWS'] = {'region': credentials.get('region', 'ap-northeast-1')}
        config['App'] = {
            'session_timeout': '30',
            'max_login_attempts': '3',
            'password_cache_duration': '300'
        }
        
        with open(self.config_path, 'w') as f:
            config.write(f)

    def load_credentials(self) -> dict:
        """
        暗号化されたAWS認証情報を読み込み
        
        Returns:
            dict: AWS認証情報を含む辞書
        """
        if not self.credentials_path.exists():
            return {}
        
        try:
            # 暗号化されたデータの読み込みと復号
            with open(self.credentials_path, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.cipher_suite.decrypt(encrypted_data)
            credentials = json.loads(decrypted_data)
            
            # 設定ファイルからリージョン情報を読み込み
            config = configparser.ConfigParser()
            config.read(self.config_path)
            credentials['region'] = config.get('AWS', 'region', fallback='ap-northeast-1')
            
            return credentials
        except Exception:
            return {} 