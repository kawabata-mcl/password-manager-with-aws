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
    def __init__(self):
        """
        AWSマネージャーの初期化
        """
        self.credentials_manager = CredentialsManager()
        self._setup_aws_client()
        self.cache = {}
        self.cache_timestamp = None
        self.cache_duration = 300  # 5分

    def _setup_aws_client(self):
        """AWSクライアントのセットアップ"""
        credentials = self.credentials_manager.load_credentials()
        self.ssm = boto3.client(
            'ssm',
            aws_access_key_id=credentials.get('aws_access_key_id'),
            aws_secret_access_key=credentials.get('aws_secret_access_key'),
            region_name=credentials.get('region', 'ap-northeast-1')
        )

    def update_credentials(self, credentials: Dict):
        """
        AWS認証情報の更新
        
        Args:
            credentials (Dict): 新しい認証情報
        """
        self.credentials_manager.save_credentials(credentials)
        self._setup_aws_client()

    def _get_parameter_path(self, username: str) -> str:
        """パラメータパスの生成"""
        return f"/password-manager/{username}"

    def _is_cache_valid(self) -> bool:
        """キャッシュが有効かどうかを確認"""
        if not self.cache_timestamp:
            return False
        return datetime.now() - self.cache_timestamp < timedelta(seconds=self.cache_duration)

    def get_passwords(self, username: str) -> List[Dict]:
        """
        ユーザーのパスワード情報を取得
        
        Args:
            username (str): ユーザー名
            
        Returns:
            List[Dict]: パスワード情報のリスト
        """
        if self._is_cache_valid():
            return self.cache.get(username, [])

        try:
            response = self.ssm.get_parameter(
                Name=self._get_parameter_path(username),
                WithDecryption=True
            )
            data = json.loads(response['Parameter']['Value'])
            self.cache[username] = data
            self.cache_timestamp = datetime.now()
            return data
        except self.ssm.exceptions.ParameterNotFound:
            return []

    def save_password(self, username: str, password_data: Dict) -> bool:
        """
        パスワード情報を保存
        
        Args:
            username (str): ユーザー名
            password_data (Dict): パスワード情報
            
        Returns:
            bool: 保存成功の場合True
        """
        current_data = self.get_passwords(username)
        
        # 既存のデータを更新または新規追加
        updated = False
        for item in current_data:
            if item['website'] == password_data['website']:
                item.update(password_data)
                updated = True
                break
        
        if not updated:
            current_data.append(password_data)

        try:
            self.ssm.put_parameter(
                Name=self._get_parameter_path(username),
                Value=json.dumps(current_data),
                Type='SecureString',
                Overwrite=True
            )
            self.cache[username] = current_data
            self.cache_timestamp = datetime.now()
            return True
        except Exception:
            return False

    def delete_password(self, username: str, website: str) -> bool:
        """
        パスワード情報を削除
        
        Args:
            username (str): ユーザー名
            website (str): 削除対象のウェブサイト
            
        Returns:
            bool: 削除成功の場合True
        """
        current_data = self.get_passwords(username)
        new_data = [item for item in current_data if item['website'] != website]
        
        if len(new_data) == len(current_data):
            return False

        try:
            self.ssm.put_parameter(
                Name=self._get_parameter_path(username),
                Value=json.dumps(new_data),
                Type='SecureString',
                Overwrite=True
            )
            self.cache[username] = new_data
            self.cache_timestamp = datetime.now()
            return True
        except Exception:
            return False 